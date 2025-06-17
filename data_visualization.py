import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
# 시각화 관련 코드 전
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

plt.rcParams["font.family"] = "AppleGothic"  # 한글 폰트 설정

# CSV 로드
df = pd.read_csv("kci_articles_all_fields_with_details.csv")

# 발행년도 정리
df["발행년도"] = df["발행년도"].astype(str).str[:4].astype(int)

# 연도별 논문 수
yearly_counts = df["발행년도"].value_counts().sort_index()

# CAGR 계산 (2015~2024)
start, end = 2015, 2024
n_start = yearly_counts.get(start, 1)
n_end = yearly_counts.get(end, 1)
cagr = ((n_end / n_start) ** (1 / (end - start))) - 1

# 기술 키워드 포함 여부 판단
tech_keywords = ["AI", "XR", "VR", "AR", "메타버스", "인공지능", "가상현실", "확장현실", "디지털트윈"]
df["기술포함"] = df["제목"].fillna("").apply(
    lambda x: any(kw.lower() in x.lower() for kw in tech_keywords)
)

# 연도별 기술 포함 비율
tech_ratio_by_year = df.groupby("발행년도")["기술포함"].mean().mul(100).round(2)

# 시각화
fig, axes = plt.subplots(2, 1, figsize=(10, 10))

# 1. 논문 수
sns.barplot(x=yearly_counts.index, y=yearly_counts.values, ax=axes[0], palette="Blues_d")
axes[0].set_title(f"KCI 문화유산 큐레이션 논문 수 (연평균 성장률: {cagr:.2%})")
axes[0].set_xlabel("발행년도")
axes[0].set_ylabel("논문 수")

# 2. 기술 키워드 포함 비율
tech_ratio_by_year.plot(kind="line", marker="o", ax=axes[1], color="darkorange")
axes[1].set_title("기술 키워드 포함 논문 비율 (%)")
axes[1].set_xlabel("발행년도")
axes[1].set_ylabel("포함 비율 (%)")
axes[1].grid(True)

plt.tight_layout()
plt.show()