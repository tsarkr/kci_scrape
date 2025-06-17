import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re

KCI_URL = 'https://www.kci.go.kr/kciportal/po/search/poArtiSearList.kci'
SEARCH_KEYWORD1 = '문화유산 OR "cultural heritage"'
SEARCH_KEYWORD2 = '큐레이션'

articles_data = []

async def extract_detail_info(detail_page):
    """
    논문 상세 페이지에서 초록, 저자_상세, 키워드_상세 정보를 추출합니다.
    제공된 HTML 스니펫을 기반으로 셀렉터를 세밀하게 조정했습니다.
    """
    abstract_text = ""
    authors_full_list = ""
    keywords_combined = ""

    # --- 1. 초록 추출 (국문/영문 모두 포함) ---
    try:
        # ID가 korAbst 또는 folaAbst인 모든 p 태그를 찾음
        abstract_locators = detail_page.locator('p#korAbst, p#folaAbst') 
        
        extracted_abstracts = []
        for i in range(await abstract_locators.count()):
            content = await abstract_locators.nth(i).text_content()
            if content.strip(): 
                extracted_abstracts.append(content.strip())
        
        abstract_text = "\n".join(extracted_abstracts) # 국문/영문 초록을 줄바꿈으로 연결
        if not abstract_text:
            print("    ⚠️ 초록 내용을 찾지 못했습니다.")

    except Exception as e:
        print(f"    ❌ 초록 추출 실패: {e}")

    # --- 2. 저자 목록 추출 (저자 중복 제거 및 정제) ---
    try:
        all_authors = []
        # 'div.author' 내에 있는 모든 'a' 태그 (저자 링크)를 찾습니다.
        # 이 셀렉터는 'div.author'가 저자 그룹의 컨테이너이며, 그 안에 각 저자 링크가 있음을 가정합니다.
        author_links = detail_page.locator('div.author a') 
        
        if await author_links.count() > 0:
            for i in range(await author_links.count()):
                author_link = author_links.nth(i)
                author_name_raw = await author_link.text_content()
                
                # 불필요한 공백, 줄바꿈, 이름 뒤의 숫자나 이메일 패턴을 제거
                author_name_cleaned = re.sub(r'\s*\d+(\s*@\S+)?$', '', author_name_raw).strip() 
                
                # 국문/영문 이름이 '/'로 구분된 경우, 국문 이름만 취함
                if '/' in author_name_cleaned:
                    author_name_cleaned = author_name_cleaned.split('/')[0].strip()

                if author_name_cleaned: # 비어있지 않은 이름만 추가
                    all_authors.append(author_name_cleaned)
            
            # 추출된 저자 목록에서 중복을 제거하고 알파벳/가나다 순으로 정렬 후 문자열로 합칩니다.
            authors_full_list = "; ".join(sorted(list(set(all_authors)))) 
        else:
            print("    ⚠️ 저자 정보 (div.author a)를 찾을 수 없습니다.")

    except Exception as e:
        print(f"    ❌ 저자 목록 추출 실패: {e}")

    # --- 3. 키워드 추출 (영어 키워드 및 한글 키워드 모두 포함) ---
    try:
        english_keywords = []
        korean_keywords_text = ""
        
        # 키워드 섹션 컨테이너를 찾기 위한 여러 셀렉터 시도 (HTML 구조 다양성에 대응)
        # `p` 태그 내에 '키워드' 또는 'Keywords' 텍스트를 포함하는 innerBox를 우선 찾거나,
        # 'a#keywd'를 가진 innerBox를 찾음
        keywords_section_locator = detail_page.locator(
            'div.innerBox.open:has(p:has-text("키워드")), ' 
            'div.innerBox.open:has(p:has-text("Keywords")), '
            'div.innerBox.open:has(a#keywd)'
        )
        
        if await keywords_section_locator.count() > 0:
            target_keywords_section = keywords_section_locator.first

            # 영어 키워드 (a#keywd) 추출
            english_keywd_locators = target_keywords_section.locator('a#keywd')
            for i in range(await english_keywd_locators.count()):
                keyword = await english_keywd_locators.nth(i).text_content()
                english_keywords.append(keyword.strip())
            
            # 한글 키워드 (<p> 태그) 추출 (유연하게)
            korean_keywd_p_locators = target_keywords_section.locator('p')
            for i in range(await korean_keywd_p_locators.count()):
                p_text = await korean_keywd_p_locators.nth(i).text_content()
                # 한글 포함, 길이 10자 이상, '초록/저자'와 같은 불필요한 단어가 없는 텍스트 필터링
                if re.search(r'[가-힣]', p_text) and len(p_text) > 10 and \
                   not any(phrase in p_text for phrase in ['초록', '저자', 'abstract', 'author', '본 논문은']): 
                    korean_keywords_text = p_text.strip()
                    break 
            
            # 한글 키워드 정제: 쉼표를 세미콜론으로 변환 및 공백 제거
            if korean_keywords_text:
                korean_keywords_text = korean_keywords_text.replace(' ', '').replace(',', ';')
                korean_keywords_text = ';'.join(filter(None, korean_keywords_text.split(';')))

            # 영문 키워드와 국문 키워드를 결합
            if english_keywords and korean_keywords_text:
                keywords_combined = "; ".join(english_keywords) + ";" + korean_keywords_text
            elif english_keywords:
                keywords_combined = "; ".join(english_keywords)
            elif korean_keywords_text:
                keywords_combined = korean_keywords_text
            
            # 최종 정제: 중복 세미콜론 제거 및 양쪽 공백 제거
            keywords_combined = ';'.join(filter(None, keywords_combined.split(';')))
            keywords_combined = re.sub(r';\s*;', ';', keywords_combined).strip()

        if not keywords_combined:
             print("    ⚠️ 키워드 섹션을 찾았으나 추출된 키워드가 없습니다.")
        
    except Exception as e:
        print(f"    ❌ 키워드 추출 실패: {e}")

    return abstract_text, authors_full_list, keywords_combined

async def extract_page_articles(page, browser): 
    rows = page.locator('table.search-answer-tbl > tbody > tr')
    count = await rows.count()
    print(f"📄 페이지 내 논문 수: {count}")

    for i in range(count):
        detail_page = None 
        try:
            row = rows.nth(i)
            # 논문 상세 페이지로 연결되는 링크 찾기
            article_link_locator = row.locator('a.subject')
            
            if await article_link_locator.count() == 0: # 대체 셀렉터
                 article_link_locator = row.locator('a[href*="ciSereArtiView"]')

            # 링크 엘리먼트가 화면에 나타날 때까지 확실히 대기 (타임아웃 증가)
            await article_link_locator.first.wait_for(state='visible', timeout=20000) 

            if await article_link_locator.count() == 0:
                print(f"  ❌ [{i+1}] 논문 상세 페이지 링크를 찾을 수 없습니다. 건너뜁니다.")
                continue

            article_link_el = article_link_locator.first
            article_url_path = await article_link_el.get_attribute('href')
            article_title_on_search_page = await article_link_el.text_content()

            # --- 검색 결과 페이지에서 기본 정보 추출 ---
            inputs = row.locator("input[type='hidden']")
            input_count = await inputs.count()
            data_dict = {}
            for j in range(input_count):
                input_el = inputs.nth(j)
                name = await input_el.get_attribute('name')
                value = await input_el.get_attribute('value')
                data_dict[name] = value

            temp_article_data = {
                '제목': data_dict.get('R_INDE_TITL', '') or article_title_on_search_page.strip(),
                '저널명': data_dict.get('R_SERE_NM', ''),
                '발행기관': data_dict.get('R_PUBI_INSI_NM', ''),
                '권': data_dict.get('R_VOL', ''),
                '호': data_dict.get('R_ISSE', ''),
                '시작페이지': data_dict.get('R_ST_PG', ''),
                '종료페이지': data_dict.get('R_END_PG', ''),
                '발행년도': data_dict.get('R_PUBI_DT', '')[:4],
                '주제분야': data_dict.get('R_MAJOR', ''),
                '인용횟수': data_dict.get('R_CITATED_IDX', ''),
                '논문ID': data_dict.get('R_SYST_LOCA_ID1', ''),
                '초록': '',        
                '저자_상세': '',   
                '키워드_상세': '' 
            }
            temp_article_data['저자'] = data_dict.get('R_CRET_NM', '')


            if article_url_path:
                full_detail_url = "https://www.kci.go.kr" + article_url_path
                print(f"    ↗️ 새로운 페이지에서 상세 페이지 이동: '{temp_article_data['제목']}'")
                
                detail_page = await browser.new_page() 
                await detail_page.goto(full_detail_url, wait_until='domcontentloaded', timeout=60000) 
                await detail_page.wait_for_load_state('networkidle', timeout=60000) 
                await detail_page.wait_for_timeout(2000) 

                detail_abstract, detail_authors, detail_keywords = await extract_detail_info(detail_page)
                temp_article_data['초록'] = detail_abstract
                temp_article_data['저자_상세'] = detail_authors
                temp_article_data['키워드_상세'] = detail_keywords
                print(f"    ✅ 상세 정보 추출 완료: 저자_상세='{detail_authors[:50]}...' 키워드='{detail_keywords[:50]}...'")

                await detail_page.close() 
                detail_page = None 
            
            articles_data.append(temp_article_data)
            print(f"  ✅ [{i+1}] '{temp_article_data.get('제목', '')}' 추출 완료")

        except Exception as e:
            print(f"  ❌ [{i+1}] 논문 추출 또는 상세 페이지 이동 실패 (오류: {e})")
            import traceback
            traceback.print_exc()
            if detail_page: 
                try:
                    await detail_page.close()
                except:
                    pass
            continue

async def run():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page() # 메인 검색 결과 페이지

        try:
            await page.goto(KCI_URL)
            await page.wait_for_load_state('load')
            await page.wait_for_timeout(1000)

            await page.fill('#topKeyword', f'{SEARCH_KEYWORD1} {SEARCH_KEYWORD2}')
            await page.click('button.searchbtn')
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(3000)

            for page_num in range(1, 11): 
                print(f"\n--- 📄 검색 결과 {page_num}페이지 처리 중... ---")
                await page.wait_for_selector('table.search-answer-tbl > tbody > tr', timeout=40000)
                
                await extract_page_articles(page, browser)

                next_button = page.get_by_role("link", name=" 다음페이지") 
                
                if await next_button.count() == 0:
                    next_selector = f'a[href^="javascript:goPage({page_num + 1})"]'
                    next_button = page.locator(next_selector).filter(has_text=re.compile(r"^\d+$"))

                if await next_button.count() > 0:
                    if await next_button.is_enabled() and await next_button.is_visible():
                        print(f"    ➡️ {page_num+1}페이지로 이동 중...")
                        await next_button.click()
                        await page.wait_for_load_state('networkidle', timeout=40000)
                        await page.wait_for_timeout(2000)
                    else:
                        print("🔚 다음 페이지 버튼이 비활성화되었거나 숨겨져 있습니다. 스크래핑을 종료합니다.")
                        break
                else:
                    print("🔚 다음 페이지 링크를 찾을 수 없습니다. 스크래핑을 종료합니다.")
                    break

            df = pd.DataFrame(articles_data)
            final_columns = [
                '제목', '저자_상세', '초록', '키워드_상세', '저자', 
                '저널명', '발행기관', '권', '호', '시작페이지', '종료페이지',
                '발행년도', '주제분야', '인용횟수', '논문ID'
            ]
            existing_cols = [col for col in final_columns if col in df.columns]
            df = df[existing_cols]

            df.to_csv('kci_articles_all_fields_with_details.csv', index=False, encoding='utf-8-sig')
            print(f"\n✅ 저장 완료: kci_articles_all_fields_with_details.csv (총 {len(df)}건)")

        except Exception as e:
            print(f"\n🚨 전체 스크립트 실행 중 치명적인 오류 발생: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(run())