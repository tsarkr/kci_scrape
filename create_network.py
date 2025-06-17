import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import re

# --- 한글 폰트 자동 설정 ---
def get_korean_font():
    korean_fonts = ['AppleGothic', 'NanumGothic', 'NanumBarunGothic', 'Malgun Gothic']
    for font_name in korean_fonts:
        for path in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
            if font_name in path:
                return fm.FontProperties(fname=path).get_name()
    print("⚠️ AppleGothic 폰트를 찾을 수 없습니다.")
    return 'Arial'

font_name = get_korean_font()
plt.rcParams['font.family'] = font_name
plt.rcParams['axes.unicode_minus'] = False

# --- 데이터 로딩 ---
df = pd.read_csv('kci_articles_all_fields_with_details.csv')
print(df.columns)

# --- 저자 리스트 분리 ---
df['저자_목록'] = df['저자_상세'].fillna('').apply(
    lambda x: [j.strip() for j in re.split(r'[|,;]', str(x)) if j.strip()]
)

# --- 공저 네트워크 생성 ---
G = nx.Graph()
for authors in df['저자_목록']:
    if len(authors) >= 2:
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                a1, a2 = authors[i], authors[j]
                if G.has_edge(a1, a2):
                    G[a1][a2]['weight'] += 1
                else:
                    G.add_edge(a1, a2, weight=1)

print(f"총 노드 수: {G.number_of_nodes()} 총 엣지 수: {G.number_of_edges()}")

# --- 중심성 계산 및 주요 인물 추출 ---
degree_centrality = nx.degree_centrality(G)
top_authors = sorted(degree_centrality, key=degree_centrality.get, reverse=True)[:30]

# --- 시각화 ---
plt.figure(figsize=(14, 12))
pos = nx.spring_layout(G, k=0.6, iterations=100, seed=42)

nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.5)
nx.draw_networkx_nodes(G, pos, node_size=30, node_color='skyblue', edgecolors='gray')

nx.draw_networkx_labels(
    G, pos,
    labels={node: node for node in top_authors},
    font_size=10,
    font_family=font_name
)

plt.title("KCI 문화유산 큐레이션 공저 네트워크", fontsize=16, fontname=font_name)
plt.axis('off')
plt.tight_layout()
plt.show()