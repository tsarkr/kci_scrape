import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정
font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

# CSV 파일 로드
df = pd.read_csv("kci_articles_all_fields_with_details.csv")

# 키워드 + 초록 결합
df["텍스트"] = df["키워드_상세"].fillna('') + ' ' + df["초록"].fillna('')

# 연도 전처리
df["발행년도"] = df["발행년도"].astype(str).str[:4]

# 연도별 TF-IDF 추출
trend_by_year = {}

for year in sorted(df["발행년도"].unique()):
    texts = df[df["발행년도"] == year]["텍스트"].tolist()
    if not texts:
        continue

    vectorizer = TfidfVectorizer(max_features=500, stop_words=["연구", "논문", "대상", "분석", "방법"])
    tfidf_matrix = vectorizer.fit_transform(texts)
    tfidf_scores = tfidf_matrix.mean(axis=0).A1
    feature_names = vectorizer.get_feature_names_out()

    tfidf_series = pd.Series(tfidf_scores, index=feature_names).sort_values(ascending=False)
    trend_by_year[year] = tfidf_series.head(10)

# 연도별 상위 키워드 출력
for year, top_words in trend_by_year.items():
    print(f"\n📅 {year}년 상위 키워드:")
    print(top_words)

# 예시: 특정 키워드들의 연도별 변화 시각화
target_keywords = ['ai', '큐레이션', '몰입', '디지털', 'ar', 'vr', '메타버스']
df["텍스트_소문자"] = df["텍스트"].str.lower()

# 키워드 빈도 계산
year_keyword_freq = {
    year: {
        kw: ' '.join(df[df["발행년도"] == year]["텍스트_소문자"].tolist()).count(kw)
        for kw in target_keywords
    }
    for year in sorted(df["발행년도"].unique())
}

trend_df = pd.DataFrame(year_keyword_freq).T.fillna(0)
scaler = MinMaxScaler()
trend_df_scaled = pd.DataFrame(scaler.fit_transform(trend_df), index=trend_df.index, columns=trend_df.columns)

# 시각화
plt.figure(figsize=(12, 6))
for kw in target_keywords:
    plt.plot(trend_df_scaled.index, trend_df_scaled[kw], label=kw)
plt.title("주요 키워드 연도별 트렌드", fontproperties=font_prop)
plt.xlabel("발행년도", fontproperties=font_prop)
plt.ylabel("상대적 빈도 (정규화)", fontproperties=font_prop)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("kci_keyword_trend.png", dpi=300)
plt.show()