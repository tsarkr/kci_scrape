# KCI 논문 분석 및 네트워크 시각화 프로젝트

이 프로젝트는 [kci_articles_all_fields_with_details.csv](kci_articles_all_fields_with_details.csv) 파일에 저장된 KCI 논문 데이터를 분석하고, 특히 "문화유산 큐레이션" 분야의 연구 동향 및 저자 네트워크를 시각화하는 것을 목표로 합니다.

## 프로젝트 구조

```
.
├── analyze_kci.py
├── create_coauthor_network_by_period.py
├── create_network.py
├── data_visualization.py
├── kci_articles_all_fields_with_details.csv
├── scrape_kci_details.py
└── trend_extract.py
```

## 데이터

*   **[kci_articles_all_fields_with_details.csv](kci_articles_all_fields_with_details.csv)**: 분석 대상이 되는 KCI 논문 데이터입니다. 제목, 저자, 초록, 키워드, 발행년도 등의 정보를 포함합니다.

## 주요 스크립트 설명

*   **[scrape_kci_details.py](scrape_kci_details.py)**: KCI 웹사이트에서 논문 상세 정보를 스크래핑하는 스크립트입니다.
*   **[analyze_kci.py](analyze_kci.py)**: KCI 논문 데이터를 분석합니다. 예를 들어, 특정 키워드(예: AI/XR)를 포함하는 논문의 비율을 연도별로 분석합니다.
*   **[create_network.py](create_network.py)**: 논문 데이터를 기반으로 저자들의 공저 네트워크를 생성하고 시각화합니다. 특히 "KCI 문화유산 큐레이션 공저 네트워크"를 생성하는 기능이 포함되어 있습니다.
*   **[create_coauthor_network_by_period.py](create_coauthor_network_by_period.py)**: 발행년도를 기준으로 기간을 나누어(예: 2019년 이전, 2020년 이후) 공저 네트워크를 생성하고 비교 분석합니다. 또한, 단독 저자와 공저자 논문 수를 비교하는 히스토그램을 생성합니다.
*   **[data_visualization.py](data_visualization.py)**: 데이터 분석 결과를 시각화하는 다양한 기능을 포함할 것으로 예상됩니다. (구체적인 내용은 제공되지 않음)
*   **[trend_extract.py](trend_extract.py)**: 논문 데이터에서 특정 연구 트렌드를 추출하는 기능을 수행할 것으로 예상됩니다. (구체적인 내용은 제공되지 않음)

## 실행 방법

각 Python 스크립트는 해당 파일이 위치한 디렉토리에서 직접 실행할 수 있습니다. 필요한 라이브러리(pandas, networkx, matplotlib, seaborn 등)가 설치되어 있어야 합니다.

```bash
python scrape_kci_details.py
python analyze_kci.py
python create_network.py
python create_coauthor_network_by_period.py
```

**참고**: 네트워크 시각화 스크립트([create_network.py](create_network.py), [create_coauthor_network_by_period.py](create_coauthor_network_by_period.py))는 한글 폰트(예: AppleGothic)를 사용하려고 시도합니다. 시스템에 해당 폰트가 없거나 다른 폰트를 사용해야 하는 경우 스크립트 내의 폰트 설정을 수정해야 할 수 있습니다.

## 결과물

스크립트 실행 시 다음과 같은 결과물을 얻을 수 있습니다:

*   콘솔 출력: 데이터 분석 결과 (예: AI/XR 키워드 포함 논문 비율)
*   이미지 파일:
    *   공저 네트워크 시각화 이미지 (예: `kci_coauthor_network.png` - [create_network.py](create_network.py) 실행 시)
    *   기간별 공저 네트워크 비교 이미지 (예: `kci_coauthor_comparison.png` - [create_coauthor_network_by_period.py](create_coauthor_network_by_period.py) 실행 시)
    *   단독/공저자 논문 수 비교 히스토그램 (예: `kci_author_type_histogram.png` - [create_coauthor_network_by_period.py](create_coauthor_network_by_period.py) 실행 시)

(스크립트 내 저장 로직에 따라 파일명은 다를 수 있습니다.)