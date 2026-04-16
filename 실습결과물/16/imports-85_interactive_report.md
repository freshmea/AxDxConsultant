# 자동차 모델 가격·성능·연비 관계 인터랙티브 보고서

[전체 인터랙티브 대시보드](C:/Users/Administrator/dxAx/실습결과물/16/imports-85_interactive_dashboard.html)

## 1부. 데이터 개요

- 원본 파일: [imports-85.csv](C:/Users/Administrator/dxAx/실습결과물/16/imports-85.csv)
- 정제 기준: 설명행/메타행 2건 제거 후 분석용 205건 사용
- 변수 수: 정제 후 36개
- 처리 원칙:
  - 수치형 결측치: 그룹 중앙값 우선, 부족 시 전체 중앙값
  - 범주형 결측치: 그룹 최빈값 우선, 부족 시 전체 최빈값
  - 컬럼명 공백 제거, 숫자형 문자열을 숫자로 변환, 파생변수 생성

### 데이터 현황 요약
### 핵심 데이터 요약표
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/overview_table.html)

보고서 출발점에서 표본 규모, 브랜드 수, 차체 유형 수, 중앙값 수준을 한 번에 확인할 수 있다. 경영진은 데이터의 해석 범위와 표본 구조를 먼저 이해해야 이후 차트의 의미를 정확히 읽을 수 있다.

판단 포인트: 샘플 구성이 특정 브랜드나 차체에 치우쳤는지, 그리고 가격·출력의 중앙값 수준이 어느 정도인지 빠르게 파악할 수 있다.

### 결측 현황
| column            |   missing_before |   missing_after |
|:------------------|-----------------:|----------------:|
| normalized-losses |               41 |               0 |
| price             |                4 |               0 |
| bore              |                4 |               0 |
| stroke            |                4 |               0 |
| num-of-doors      |                2 |               0 |
| horsepower        |                2 |               0 |
| peak-rpm          |                2 |               0 |

### 변수 설명
| variable               | type        | meaning           |
|:-----------------------|:------------|:------------------|
| price                  | numeric     | 차량 가격             |
| engine-size            | numeric     | 엔진 배기량 크기         |
| horsepower             | numeric     | 엔진 출력             |
| curb-weight            | numeric     | 차량 공차중량           |
| city-mpg / highway-mpg | numeric     | 도심/고속 연비          |
| avg_mpg                | derived     | 평균 연비             |
| footprint              | derived     | 길이*너비 기반 차체 면적 지표 |
| price_per_hp           | derived     | 마력당 가격            |
| make                   | categorical | 브랜드               |
| body-style             | categorical | 차체 유형             |
| drive-wheels           | categorical | 구동 방식             |
| fuel-type              | categorical | 연료 방식             |
| segment                | derived     | 가격·마력·연비 기반 세그먼트  |

## 2부. 핵심 인사이트 5가지

- 가격은 `engine-size`, `curb-weight`, `horsepower`와 강한 양의 상관을 보인다. 이 데이터셋에서 가격은 사실상 성능·차체 규모 패키지의 결과다.
- 연비는 가격과 반대로 움직인다. 특히 `avg_mpg`가 높은 차량일수록 저가·실속형으로 몰리고, 고가 차량은 평균적으로 연비가 낮다.
- `hardtop`, `convertible`, `rwd` 조합은 평균 가격과 출력이 높고, `hatchback`, `fwd` 조합은 실속형 포지션에 가깝다.
- 브랜드별로는 Jaguar, Mercedes-Benz, Porsche, BMW가 고가·고성능 축에 집중되고, Toyota·Honda·Nissan은 상대적으로 대중형 구간에 넓게 분포한다.
- 세그먼트 관점에서 `Premium Performance`, `Balanced Core`, `Value Efficiency`, `Budget Practical` 네 그룹으로 나누면 상품 포트폴리오와 가격 전략을 훨씬 명확하게 설명할 수 있다.


가격 관련 주요 변수 TOP 5:

| variable     |   correlation |
|:-------------|--------------:|
| engine-size  |        0.8729 |
| curb-weight  |        0.8323 |
| horsepower   |        0.7839 |
| price_per_hp |        0.7743 |
| width        |        0.747  |

세그먼트 차별화 요약:
- `Premium Performance`: 고가·고마력 차량군. 브랜드 프리미엄과 성능 패키지가 가격을 견인한다.
- `Balanced Core`: 중간 가격대의 핵심 볼륨 구간. 성능과 연비의 균형이 상대적으로 좋다.
- `Value Efficiency`: 낮은 가격과 높은 연비 조합. 유지비 관점에서 설득력이 높다.
- `Budget Practical`: 저가 실속형이지만 상품성은 제한적일 수 있어, 옵션 전략과 트림 차별화가 중요하다.

## 3부. 차트별 분석 결과

### A. 데이터 구조와 기본 분포
### 브랜드별 표본 수 Top 12
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/brand_counts.html)

Toyota, Nissan, Mazda가 가장 많은 표본을 차지한다. 따라서 전체 평균을 해석할 때는 이들 대중 브랜드의 영향력이 크고, 소수 프리미엄 브랜드는 평균값보다 분포의 상단을 넓히는 역할을 한다.

판단 포인트: 표본이 많은 브랜드는 시장의 기준선 역할을 하고, 표본이 적은 프리미엄 브랜드는 평균 가격을 끌어올리는 특수 세그먼트인지 판단할 수 있다.

### 연료 방식 비중
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/fuel_share.html)

가솔린 차량 비중이 압도적으로 높고 디젤은 제한적이다. 따라서 연비와 압축비 해석에서 디젤 차량은 별도 포지션으로 보는 것이 합리적이다.

판단 포인트: 연료 방식별 정책이나 포트폴리오 논의를 할 때, 전체 평균보다 표본 구성을 먼저 확인할 수 있다.

### 핵심 수치형 변수 분포
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/distribution_panel.html)

가격, 엔진 크기, 마력은 우측 꼬리가 긴 분포를 보여 일부 고가·고성능 차량이 상단을 끌어올린다. 반면 평균 연비는 상대적으로 좁은 구간에 몰려 있어, 연비 경쟁은 제한된 범위 안에서 벌어진다.

판단 포인트: 고가 구간이 소수 차량에 집중되는지, 엔진과 마력이 몇 개의 군집으로 나뉘는지, 연비 개선 여지가 큰지 판단할 수 있다.

### B. 가격 결정 요인 분석
### 엔진 크기와 가격의 관계
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/scatter_engine_price.html)

엔진 크기가 커질수록 가격이 상승하는 명확한 우상향 추세가 보인다. 같은 엔진 크기에서도 차체 유형과 연료 방식에 따라 가격 차이가 벌어지는 점은, 단순 배기량 외에 브랜드와 차체 포지셔닝이 프리미엄을 만든다는 뜻이다.

판단 포인트: 대배기량 전략이 실제로 가격 프리미엄으로 연결되는지, 그리고 어떤 차체 유형이 같은 엔진 크기 대비 더 높은 가격을 받는지 확인할 수 있다.

### 마력과 가격의 관계
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/scatter_hp_price.html)

마력 또한 가격과 강하게 연결되지만, 일부 브랜드는 같은 출력 대비 더 높은 가격을 받는다. 이는 브랜드 프리미엄 또는 고급 사양 패키지 영향으로 해석할 수 있다.

판단 포인트: 출력 상승이 가격 인상 논리를 충분히 뒷받침하는지, 혹은 브랜드 파워가 더 큰지 구분할 수 있다.

### 차량 중량과 가격의 관계
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/scatter_weight_price.html)

중량이 높은 차량일수록 가격도 높아지는 경향이 강하다. 실제로는 차체 크기, 안전/편의사양, 엔진 구성이 함께 묶여 있는 결과로 보는 것이 적절하다.

판단 포인트: 고급화 전략이 차체·사양 확대와 함께 가는지, 혹은 지나친 중량 증가가 가격 대비 효율을 해치는지 판단할 수 있다.

### 평균 연비와 가격의 관계
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/scatter_mpg_price.html)

평균 연비가 높을수록 가격은 낮아지는 역관계가 보인다. 즉 이 데이터에서는 성능과 가격을 올릴수록 연비 손실을 감수하는 구조가 강하며, 고연비 차량은 실속형 세그먼트에 집중된다.

판단 포인트: 고연비 전략이 프리미엄과 양립하는지, 아니면 별도 실속형 포트폴리오로 운영해야 하는지 판단할 수 있다.

### C. 비교 분석
### 주요 브랜드별 가격·마력·연비 비교
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/brand_metrics.html)

Jaguar, Mercedes-Benz, Porsche, BMW는 평균 가격과 출력이 높고, 연비는 상대적으로 낮다. 반대로 Toyota, Honda, Nissan은 상대적으로 낮은 가격과 중간 수준의 마력, 더 나은 연비로 대중형 포지션을 형성한다.

판단 포인트: 브랜드 포트폴리오를 프리미엄 중심으로 볼지, 볼륨 중심으로 볼지, 혹은 양쪽을 분리 운영할지 결정하는 데 도움을 준다.

### 차체 유형과 구동 방식별 평균 가격
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/body_drive_price.html)

`rwd`는 대체로 높은 가격과 연결되고, `fwd`는 대중형 세그먼트에 집중된다. `hardtop`과 `convertible`은 차체 유형 자체가 프리미엄 가격대를 형성하는 반면, `hatchback`은 실속형에 가깝다.

판단 포인트: 차체와 구동 방식을 어떤 조합으로 가져갈 때 프리미엄 가격을 만들 수 있는지 판단할 수 있다.

### D. 관계 구조와 세그먼트
### 수치형 변수 상관관계 구조
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/correlation_heatmap.html)

가격은 엔진 크기, 중량, 마력과 같은 방향으로 움직이고, 연비와는 반대 방향으로 움직인다. 상관관계가 매우 높은 변수들이 함께 존재하므로, 실제 가격 정책에서는 단일 스펙보다 패키지 조합으로 접근해야 한다.

판단 포인트: 어떤 변수를 묶어서 상품기획 패키지를 설계해야 하는지, 서로 대체 가능한 설명 변수가 무엇인지 판단할 수 있다.

### 가격 구간별 성능·엔진·연비 변화
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/price_decile_line.html)

가격 구간이 올라갈수록 평균 마력과 엔진 크기는 상승하고 평균 연비는 하락한다. 특히 상위 가격 구간에서 성능 지표가 가파르게 상승해, 고가 구간은 단순 가격 인상이 아니라 명확한 성능 차별화로 설명된다.

판단 포인트: 가격대별로 어떤 사양을 더해야 소비자가 가격 차이를 납득하는지 판단할 수 있다.

### 세그먼트별 차량 포지셔닝 맵
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/segment_map.html)

차량군은 대략 네 개 세그먼트로 구분된다. 고가·고성능군은 연비가 낮고, 실속형은 높은 연비와 낮은 가격에 집중되며, 중간 다수는 균형형 구간에 모여 있다.

판단 포인트: 포트폴리오 공백이 어디인지, 프리미엄 강화가 필요한지, 혹은 실속형 보강이 필요한지 판단할 수 있다.

### 세그먼트 요약표
[인터랙티브 보기](C:/Users/Administrator/dxAx/실습결과물/16/imports85_report_assets/segment_table.html)

세그먼트별 차량 수, 평균 가격, 평균 마력, 평균 연비, 대표 브랜드를 함께 보면 포트폴리오 구조가 명확해진다. 경영진은 이 표만 봐도 어느 세그먼트가 수익성 중심인지, 어느 세그먼트가 볼륨 중심인지 빠르게 파악할 수 있다.

판단 포인트: 브랜드별 역할을 세그먼트 관점에서 재정의하고, 상품기획·마케팅·영업 전략을 분리 설계할 수 있다.

## 4부. 종합 결론 및 실행 제안

### 가격 결정에 중요한 요인
- 가장 중요한 가격 결정 변수는 `engine-size`, `curb-weight`, `horsepower`다.
- 결국 가격은 단일 옵션보다 엔진, 차체, 출력이 묶인 패키지 가치로 결정된다.
- 동일 출력에서도 브랜드와 차체 유형이 가격 프리미엄을 만든다.

### 연비와 성능의 트레이드오프
- 고성능 차량은 평균 연비가 낮다.
- 연비 우수 차량은 대체로 저가 세그먼트에 모인다.
- 따라서 상품기획 단계에서 프리미엄과 효율을 동시에 추구하려면, 경량화나 파워트레인 개선 같은 구조적 해법이 필요하다.

### 브랜드·차체·구동 방식 시사점
- 브랜드: 프리미엄 브랜드는 출력과 가격으로 차별화되고, 대중 브랜드는 실속형과 균형형 수요를 흡수한다.
- 차체 유형: `hardtop`, `convertible`은 이미지 프리미엄이 강하고, `hatchback`은 실용형 포지션이 명확하다.
- 구동 방식: `rwd`는 성능과 고급감, `fwd`는 효율과 대중성을 상징한다.

### 실행 제안
- 상품기획:
  - 상위 가격 구간은 단순 가격 인상보다 출력·차체·구동 조합을 함께 올리는 패키지 전략으로 설계한다.
  - 실속형 세그먼트는 연비와 가격 경쟁력을 강화하되, 옵션 구성을 단순화해 포지셔닝을 선명하게 만든다.
- 마케팅:
  - 프리미엄 세그먼트는 브랜드·성능 중심 메시지, 실속형 세그먼트는 유지비·효율 중심 메시지로 분리 운영한다.
  - 같은 브랜드 안에서도 세그먼트별 크리에이티브를 분리해 가격 저항을 낮춘다.
- 영업:
  - 고가 차량은 성능 체감 포인트와 고급 사양을 패키지로 제안해 업셀링한다.
  - 대중형 차량은 총소유비용 관점의 상담 스크립트를 강화해 전환율을 높인다.

## 5부. 부록: 주요 표(Table)와 변수 설명

### 가격 관련 상관계수 전체표
| variable          |   correlation |
|:------------------|--------------:|
| price             |        1      |
| engine-size       |        0.8729 |
| curb-weight       |        0.8323 |
| horsepower        |        0.7839 |
| price_per_hp      |        0.7743 |
| width             |        0.747  |
| length            |        0.6903 |
| wheel-base        |        0.5844 |
| power_density     |        0.146  |
| compression-ratio |        0.0728 |
| city-mpg          |       -0.6829 |
| avg_mpg           |       -0.6967 |
| highway-mpg       |       -0.7    |

### 세그먼트 요약표
| segment             |   vehicles |   avg_price |   avg_hp |   avg_mpg | lead_brands                 |
|:--------------------|-----------:|------------:|---------:|----------:|:----------------------------|
| Premium Performance |         38 |       26150 |    163.4 |      20.8 | mercedes-benz, bmw, porsche |
| Balanced Core       |         71 |       13670 |    109.2 |      24.9 | peugot, mazda, toyota       |
| Value Efficiency    |         45 |        6614 |     67.6 |      36.5 | honda, nissan, toyota       |
| Budget Practical    |         51 |        8601 |     84.7 |      30.1 | toyota, subaru, volkswagen  |

### Python 코드 실행 안내
- 전체 스크립트: [imports85_plotly_report.py](C:/Users/Administrator/dxAx/실습결과물/16/imports85_plotly_report.py)
- 실행 환경: [`.venv-report`](C:/Users/Administrator/dxAx/.venv-report)
- 실행 명령:

```powershell
.\.venv-report\Scripts\python .\실습결과물\16\imports85_plotly_report.py
```

### 코드 예시
```python
import pandas as pd
import plotly.express as px

df = pd.read_csv("imports-85.csv", dtype=str)
df.columns = [c.strip() for c in df.columns]
df = df[~df["price"].isin(["continuous", "class"])].replace({"?": pd.NA, "": pd.NA})
df["price"] = pd.to_numeric(df["price"], errors="coerce")
df["engine-size"] = pd.to_numeric(df["engine-size"], errors="coerce")
df["horsepower"] = pd.to_numeric(df["horsepower"], errors="coerce")

fig = px.scatter(
    df,
    x="engine-size",
    y="price",
    color="body-style",
    size="horsepower",
    symbol="drive-wheels",
    trendline="ols",
    title="엔진 크기와 가격의 관계"
)
fig.show()
```

`trendline="ols"`를 쓰려면 `statsmodels`가 필요하다. 본 결과물은 `plotly.express`와 `plotly.graph_objects`를 병행해 생성했다.
