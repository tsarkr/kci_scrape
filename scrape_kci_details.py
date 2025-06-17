import pandas as pd
import networkx as nx
import re

def analyze_kci_data_from_details_csv(file_path):
    """
    KCI 상세 정보 CSV 파일을 분석하여 논문 수, CAGR, AI/XR 키워드 비율, 공저 네트워크 밀도를 계산합니다.

    Args:
        file_path (str): 상세 정보가 포함된 KCI CSV 파일의 경로.
    """
    try:
        # 파일 인코딩 문제 해결을 위해 'utf-8-sig' (BOM 포함 UTF-8) 먼저 시도
        df_kci = pd.read_csv(file_path, encoding='utf-8-sig')
    except UnicodeDecodeError:
        try:
            df_kci = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df_kci = pd.read_csv(file_path, encoding='cp949')
            except Exception as e:
                print(f"오류: 파일 인코딩을 감지할 수 없습니다: {e}")
                return
    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        return
    except Exception as e:
        print(f"오류: 파일을 읽는 중 예기치 않은 오류가 발생했습니다: {e}")
        import traceback
        traceback.print_exc()
        return

    # 필요한 컬럼이 존재하는지 확인 (저자_상세, 초록, 키워드_상세 포함)
    required_cols = {'발행년도', '저자_상세', '제목', '초록', '키워드_상세'}
    if not required_cols.issubset(df_kci.columns):
        missing_cols = required_cols - set(df_kci.columns)
        print(f"오류: 필수 컬럼이 파일에 없습니다. 누락된 컬럼: {', '.join(missing_cols)}")
        print("파일의 실제 컬럼명:", df_kci.columns.tolist())
        return

    # 데이터 타입 변환 및 누락 값 처리
    df_kci['발행년도'] = pd.to_numeric(df_kci['발행년도'], errors='coerce').fillna(0).astype(int)
    df_kci['저자_상세'] = df_kci['저자_상세'].astype(str).fillna('')
    df_kci['제목'] = df_kci['제목'].astype(str).fillna('')
    df_kci['초록'] = df_kci['초록'].astype(str).fillna('')
    df_kci['키워드_상세'] = df_kci['키워드_상세'].astype(str).fillna('') # 키워드_상세 추가

    # 2015-2024년 데이터 필터링
    df_kci_filtered = df_kci[(df_kci['발행년도'] >= 2015) & (df_kci['발행년도'] <= 2024)].copy()

    print("--- KCI 데이터 분석 결과 (상세 정보 포함) ---")

    # --- 1. 총 논문 수 (2015-2024) ---
    total_kci_articles = len(df_kci_filtered)
    print(f"\n1. 총 KCI 논문 수 (2015-2024): {total_kci_articles}편")

    # --- 2. 연도별 출판량 및 CAGR ---
    df_grp_kci_yearly = df_kci_filtered.groupby("발행년도").size().reindex(range(2015, 2025), fill_value=0)
    print("\n2. KCI 논문 연도별 출판량 (2015-2024):\n", df_grp_kci_yearly)

    articles_2015 = df_grp_kci_yearly.loc[2015] if 2015 in df_grp_kci_yearly.index else 0
    articles_2024 = df_grp_kci_yearly.loc[2024] if 2024 in df_grp_kci_yearly.index else 0
    print(f"   - 2015년 논문 수: {articles_2015}편")
    print(f"   - 2024년 논문 수: {articles_2024}편")
    if articles_2015 > 0:
        growth_factor = articles_2024 / articles_2015
        print(f"   - 2015년 대비 2024년 논문 수 증가율: 약 {round(growth_factor, 1)}배")
    else:
        print("   - 2015년 논문 수가 없어 증가율을 계산할 수 없습니다.")

    y0_cagr_abstract = df_grp_kci_yearly.loc[2019] if 2019 in df_grp_kci_yearly.index else 0
    yN_cagr_abstract = df_grp_kci_yearly.loc[2024] if 2024 in df_grp_kci_yearly.index else 0
    cagr_kci_2019_2024 = 0.0
    if y0_cagr_abstract > 0 and (2024 - 2019) > 0:
        cagr_kci_2019_2024 = (yN_cagr_abstract / y0_cagr_abstract) ** (1/(2024-2019)) - 1
    print(f"   - KCI 연평균 성장률(CAGR, 2019-2024): {round(cagr_kci_2019_2024*100, 2)} %")

    # --- 3. AI/XR 키워드 포함 비율 (제목 + 초록 + 키워드_상세 기준) ---
    # AI/XR 키워드 목록
    ai_xr_keywords = [
        'ai', '인공지능', 'artificial intelligence', 'xr', '확장현실', 'extended reality',
        'vr', '가상현실', 'virtual reality', 'ar', '증강현실', 'augmented reality',
        'digital twin', '디지털 트윈', 'llm', '대규모 언어 모델', 'large language model',
        'deep learning', '딥러닝', 'machine learning', '머신러닝'
    ]

    def contains_keywords_in_all_fields(row, keywords):
        # '제목', '초록', '키워드_상세' 컬럼 모두에서 키워드 검색
        search_text = str(row['제목']) + ' ' + str(row['초록']) + ' ' + str(row['키워드_상세'])
        search_text_lower = search_text.lower()
        return any(kw.lower() in search_text_lower for kw in keywords)

    df_kci_2015_only = df_kci_filtered[df_kci_filtered['발행년도'] == 2015]
    df_kci_2024_only = df_kci_filtered[df_kci_filtered['발행년도'] == 2024]

    # 2015년 AI/XR 관련 논문 수
    ai_xr_count_2015 = df_kci_2015_only[
        df_kci_2015_only.apply(lambda row: contains_keywords_in_all_fields(row, ai_xr_keywords), axis=1)
    ].shape[0]
    total_articles_2015_for_ratio = len(df_kci_2015_only)
    ai_xr_ratio_2015 = (ai_xr_count_2015 / total_articles_2015_for_ratio * 100) if total_articles_2015_for_ratio > 0 else 0

    # 2024년 AI/XR 관련 논문 수
    ai_xr_count_2024 = df_kci_2024_only[
        df_kci_2024_only.apply(lambda row: contains_keywords_in_all_fields(row, ai_xr_keywords), axis=1)
    ].shape[0]
    total_articles_2024_for_ratio = len(df_kci_2024_only)
    ai_xr_ratio_2024 = (ai_xr_count_2024 / total_articles_2024_for_ratio * 100) if total_articles_2024_for_ratio > 0 else 0

    print(f"\n3. AI/XR 키워드 포함 논문 비율 (제목 + 초록 + 키워드_상세 기준):")
    print(f"   - 2015년: {ai_xr_count_2015} / {total_articles_2015_for_ratio} ({round(ai_xr_ratio_2015, 2)} %)")
    print(f"   - 2024년: {ai_xr_count_2024} / {total_articles_2024_for_ratio} ({round(ai_xr_ratio_2024, 2)} %)")
    
    # 추가: 키워드 상세에서 AI/XR 키워드 발견된 논문 수 (제목+초록+키워드_상세 필드 모두를 기준으로)
    ai_xr_total_found = df_kci_filtered.apply(lambda row: contains_keywords_in_all_fields(row, ai_xr_keywords), axis=1).sum()
    print(f"   - 전체 기간(2015-2024) 동안 AI/XR 관련 논문 총 개수: {ai_xr_total_found}편")


    # --- 4. 공저 네트워크 밀도 (저자_상세 컬럼 사용, 중복 제거) ---
    def calculate_network_density_from_detailed_authors(df_subset_network):
        edges = []
        for _, r in df_subset_network.iterrows():
            # 저자_상세 컬럼 사용, 세미콜론으로 분리 후 공백 제거
            authors_raw = str(r["저자_상세"])
            # KCI 데이터에서 '저자_상세'에 중복 저자명이 '; '로 연결되어 있어 set으로 중복 제거
            authors = [a.strip() for a in authors_raw.split(';') if a.strip()]
            
            # **여기서 중요한 수정: 이미 스크래핑 단계에서 중복이 발생했다면, 분석 단계에서 다시 제거**
            authors = list(set(authors)) # 중복 제거

            if len(authors) > 1: # 공동 저자가 2명 이상인 경우에만 엣지 추가
                for i in range(len(authors)):
                    for j in range(i+1, len(authors)):
                        if authors[i] and authors[j]:
                            edges.append((authors[i], authors[j]))
        
        G = nx.Graph()
        G.add_edges_from(edges)
        
        if G.number_of_nodes() > 1:
            return nx.density(G)
        return 0.0 # 노드가 0개 또는 1개인 경우 밀도는 0

    df_kci_2015_2019 = df_kci_filtered[(df_kci_filtered['발행년도'] >= 2015) & (df_kci_filtered['발행년도'] <= 2019)]
    df_kci_2020_2024 = df_kci_filtered[(df_kci_filtered['발행년도'] >= 2020) & (df_kci_filtered['발행년도'] <= 2024)]

    density_2015_2019 = calculate_network_density_from_detailed_authors(df_kci_2015_2019)
    density_2020_2024 = calculate_network_density_from_detailed_authors(df_kci_2020_2024)

    print(f"\n4. KCI 공저 네트워크 밀도 ('저자_상세' 컬럼 기반):")
    print(f"   - 2015-2019년 기간: {round(density_2015_2019, 4)}") # 소수점 자리수 늘림
    print(f"   - 2020-2024년 기간: {round(density_2020_2024, 4)}") # 소수점 자리수 늘림

# 스크립트 실행 부분
if __name__ == "__main__":
    kci_details_file_name = "kci_articles_all_fields_with_details.csv"
    analyze_kci_data_from_details_csv(kci_details_file_name) # 상세 데이터 파일 사용