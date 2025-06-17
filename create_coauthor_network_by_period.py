import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import re
from collections import Counter

# CSV 파일 로드
df = pd.read_csv("kci_articles_all_fields_with_details.csv")

# 저자 필드 정제
df["저자_목록"] = df["저자"].fillna("").apply(
    lambda x: [j.strip() for j in re.split(r"[|,;]", str(x)) if j.strip()]
)

# 시기별 분할
early_df = df[df["발행년도"].astype(str).str[:4].astype(int) <= 2019]
late_df = df[df["발행년도"].astype(str).str[:4].astype(int) >= 2020]

# 공저 네트워크 생성 함수
def build_graph(df_subset):
    G = nx.Graph()
    for authors in df_subset["저자_목록"]:
        if len(authors) < 2:
            continue
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                a, b = authors[i], authors[j]
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    return G

# 그래프 생성
G_early = build_graph(early_df)
G_late = build_graph(late_df)

# 밀도 계산
density_early = nx.density(G_early)
density_late = nx.density(G_late)

# 한글 폰트 설정
font_path = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
if not fm.findSystemFonts(fontpaths=None, fontext="ttf"):
    print("⚠️ 한글 폰트가 없습니다.")
font_prop = fm.FontProperties(fname=font_path)

# 시각화
fig, axes = plt.subplots(1, 2, figsize=(18, 9))

if len(G_early.nodes) > 0:
    pos_early = nx.spring_layout(G_early, seed=42)
    nx.draw_networkx(
        G_early,
        pos=pos_early,
        ax=axes[0],
        with_labels=False,
        node_size=20,
        node_color="skyblue",
        edge_color="gray",
        width=0.5,
    )
axes[0].set_title(f"2015–2019 공저 네트워크 (밀도: {density_early:.4f})", fontproperties=font_prop)

if len(G_late.nodes) > 0:
    pos_late = nx.spring_layout(G_late, seed=42)
    nx.draw_networkx(
        G_late,
        pos=pos_late,
        ax=axes[1],
        with_labels=False,
        node_size=20,
        node_color="lightgreen",
        edge_color="gray",
        width=0.5,
    )
axes[1].set_title(f"2020–2024 공저 네트워크 (밀도: {density_late:.4f})", fontproperties=font_prop)

plt.suptitle("KCI 문화유산 큐레이션 공저 네트워크 비교 (시기별)", fontproperties=font_prop, fontsize=16)
plt.tight_layout()
plt.subplots_adjust(top=0.9)
plt.savefig("kci_coauthor_comparison.png", dpi=300)
plt.show()

# 단독저자 vs 공저자 히스토그램 시각화
df["저자수"] = df["저자_목록"].apply(len)
df["저자유형"] = df["저자수"].apply(lambda x: "단독 저자" if x == 1 else "공저")

plt.figure(figsize=(8, 6))
sns.countplot(data=df, x="저자유형", hue="저자유형", palette="Set2", legend=False)
plt.title("KCI 문화유산 큐레이션 연구 단독/공저자 편수 비교", fontproperties=font_prop)
plt.xlabel("저자 유형", fontproperties=font_prop)
plt.ylabel("논문 수", fontproperties=font_prop)
plt.tight_layout()
plt.savefig("kci_author_type_hist.png", dpi=300)
plt.show()