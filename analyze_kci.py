import pandas as pd
import networkx as nx
import math

def analyze_kci_data(file_path):
    """
    KCI 데이터를 분석하여 논문 수, CAGR, AI/XR 키워드 비율, 공저 네트워크 밀도를 계산합니다.

    Args:
        file_path (str): KCI CSV 파일의 경로.
    """
    try:
        # 파일 인코딩 문제 해결을 위해 'cp949' 또는 'euc-kr' 시도
        df_kci = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df_kci = pd.read_csv(file_path, encoding='cp949')
        except UnicodeDecodeError:
            df_kci = pd.read_csv(file_path, encoding='euc-kr')
    except FileNotFoundError:
        print(f"오류: '{file_path}' 파일을 찾을 수 없습니다. 파일 경로를 확인해주세요.")
        return

    # 컬럼 이름 매핑 (사용자 제공 컬럼 이름에 맞춤)
    # 필요한 컬럼이 존재하는지 먼저 확인하는 로직 추가
    required_cols = {'발행년도', '저자', '제목', '저자_상세', '초록', '키워드_상세'} # '초록', '키워드_상세' 추가
    if not required_cols.issubset(df_kci.columns):
        missing_cols = required_cols - set(df_kci.columns)
        print(f"오류: 필수 컬럼이 파일에 없습니다. 누락된 컬럼: {', '.join(missing_cols)}")
        print("파일의 실제 컬럼명:", df_kci.columns.tolist())
        return

    # 데이터 타입 변환 및 누락 값 처리 (수정된 컬럼명 사용)
    df_kci['발행년도'] = pd.to_numeric(df_kci['발행년도'], errors='coerce').fillna(0).astype(int)
    df_kci['저자'] = df_kci['저자'].astype(str)
    df_kci['저자_상세'] = df_kci['저자_상세'].astype(str).fillna('') # '저자_상세' 추가
    df_kci['제목'] = df_kci['제목'].astype(str).fillna('')
    df_kci['초록'] = df_kci['초록'].astype(str).fillna('') # '초록' 추가
    df_kci['키워드_상세'] = df_kci['키워드_상세'].astype(str).fillna('') # '키워드_상세' 추가

    # 2015-2024년 데이터 필터링
    df_kci_filtered = df_kci[(df_kci['발행년도'] >= 2015) & (df_kci['발행년도'] <= 2024)].copy() # .copy()를 추가하여 SettingWithCopyWarning 방지

    print("--- KCI 데이터 분석 결과 ---")

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


    # 초록의 2019-2024년 CAGR 계산
    y0_cagr_abstract = df_grp_kci_yearly.loc[2019] if 2019 in df_grp_kci_yearly.index else 0
    yN_cagr_abstract = df_grp_kci_yearly.loc[2024] if 2024 in df_grp_kci_yearly.index else 0
    cagr_kci_2019_2024 = 0.0
    if y0_cagr_abstract > 0 and (2024 - 2019) > 0:
        cagr_kci_2019_2024 = (yN_cagr_abstract / y0_cagr_abstract) ** (1/(2024-2019)) - 1
    print(f"   - KCI 연평균 성장률(CAGR, 2019-2024): {round(cagr_kci_2019_2024*100, 2)} %")

    # --- 3. AI/XR 키워드 포함 비율 (2015 vs 2024) ---
    def contains_keywords_in_combined_text(text_combined, keywords):
        text_lower = str(text_combined).lower() # Ensure text is string and lowercased
        return any(kw.lower() in text_lower for kw in keywords)

    # 확장된 키워드 목록
    ai_xr_keywords = [
        'ai', '인공지능', 'artificial intelligence', 'xr', '확장현실', 'extended reality',
        'vr', '가상현실', 'virtual reality', 'ar', '증강현실', 'augmented reality',
        'digital twin', '디지털 트윈', 'llm', '대규모 언어 모델', 'large language model',
        'deep learning', '딥러닝', 'machine learning', '머신러닝'
    ]

    # 각 연도별 AI/XR 관련 논문 필터링
    df_kci_2015_only = df_kci_filtered[df_kci_filtered['발행년도'] == 2015]
    df_kci_2024_only = df_kci_filtered[df_kci_filtered['발행년도'] == 2024]

    # 2015년 AI/XR 관련 논문 수 (제목 + 초록 + 키워드_상세 기준)
    ai_xr_count_2015 = df_kci_2015_only[
        df_kci_2015_only.apply(lambda row: contains_keywords_in_combined_text(
            str(row['제목']) + ' ' + str(row['초록']) + ' ' + str(row['키워드_상세']), ai_xr_keywords
        ), axis=1)
    ].shape[0]
    total_articles_2015_for_ratio = len(df_kci_2015_only)
    ai_xr_ratio_2015 = (ai_xr_count_2015 / total_articles_2015_for_ratio * 100) if total_articles_2015_for_ratio > 0 else 0

    # 2024년 AI/XR 관련 논문 수 (제목 + 초록 + 키워드_상세 기준)
    ai_xr_count_2024 = df_kci_2024_only[
        df_kci_2024_only.apply(lambda row: contains_keywords_in_combined_text(
            str(row['제목']) + ' ' + str(row['초록']) + ' ' + str(row['키워드_상세']), ai_xr_keywords
        ), axis=1)
    ].shape[0]
    total_articles_2024_for_ratio = len(df_kci_2024_only)
    ai_xr_ratio_2024 = (ai_xr_count_2024 / total_articles_2024_for_ratio * 100) if total_articles_2024_for_ratio > 0 else 0

    print(f"\n3. AI/XR 키워드 포함 논문 비율 (제목 + 초록 + 키워드_상세 기준):")
    print(f"   - 2015년: {ai_xr_count_2015} / {total_articles_2015_for_ratio} ({round(ai_xr_ratio_2015, 2)} %)")
    print(f"   - 2024년: {ai_xr_count_2024} / {total_articles_2024_for_ratio} ({round(ai_xr_ratio_2024, 2)} %)")

    # --- 4. 공저 네트워크 밀도 (2015-2019 vs 2020-2024) ---
    def calculate_network_density(df_subset_network):
        edges = []
        for _, r in df_subset_network.iterrows():
            # '저자_상세' 컬럼을 사용하여 공저자 분석
            authors_raw = str(r["저자_상세"]).split(";")
            authors = [a.strip() for a in authors_raw if a.strip()]
            
            # KCI 데이터에서 '저자_상세'에 중복 저자명이 '; '로 연결되어 있을 수 있으므로 set으로 중복 제거
            authors = list(set(authors)) # 중복 제거
            
            if len(authors) > 1: # 공저 논문만 고려
                for i in range(len(authors)):
                    for j in range(i+1, len(authors)):
                        if authors[i] and authors[j]:
                            edges.append(tuple(sorted((authors[i], authors[j])))) # 엣지 정렬하여 추가
        G = nx.Graph()
        G.add_edges_from(edges)
        if G.number_of_nodes() > 1:
            return nx.density(G)
        return 0.0 # 노드가 0개 또는 1개인 경우 밀도는 0

    df_kci_2015_2019 = df_kci_filtered[(df_kci_filtered['발행년도'] >= 2015) & (df_kci_filtered['발행년도'] <= 2019)]
    df_kci_2020_2024 = df_kci_filtered[(df_kci_filtered['발행년도'] >= 2020) & (df_kci_filtered['발행년도'] <= 2024)]

    density_2015_2019 = calculate_network_density(df_kci_2015_2019)
    density_2020_2024 = calculate_network_density(df_kci_2020_2024)

    print(f"\n4. KCI 공저 네트워크 밀도 ('저자_상세' 컬럼 기반):")
    print(f"   - 2015-2019년 기간: {round(density_2015_2019, 4)}") # 소수점 자리수 늘림
    print(f"   - 2020-2024년 기간: {round(density_2020_2024, 4)}") # 소수점 자리수 늘림

# 스크립트 실행 부분
if __name__ == "__main__":
    kci_file_name = "kci_articles_all_fields_with_details.csv"
    analyze_kci_data(kci_file_name)