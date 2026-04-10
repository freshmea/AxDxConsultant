# Body Fat Brozek 시각 분석 보고서 (미리보기 중심)

## 1) 데이터 개요
- 데이터 행 수: **252**
- 타겟 변수: `body fat brozek`
- 분석 목표: 분포, 이상치, 상관관계, 변수별 패턴을 직관적으로 확인

초기 분포를 보면 체지방 수치가 단봉형 분포를 가지며, 사분위 그룹은 거의 균등하게 나뉩니다.

![body fat distribution](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/overview/bodyfat_distribution.png)

![body fat group counts](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/overview/bodyfat_group_counts.png)

## 2) 상관관계 중심 해석
Pearson/Spearman 히트맵에서 체지방과 함께 움직이는 핵심 변수는 `abdomen`, `adiposity`, `chest`, `hip`, `weight`입니다.

![pearson heatmap](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/correlation/correlation_heatmap_pearson.png)

![spearman heatmap](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/correlation/correlation_heatmap_spearman.png)

![pairplot top correlated](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/correlation/pairplot_top5.png)

### 체지방과의 Pearson 상관 순위

상위 양의 상관:

|           |   pearson_corr |
|:----------|---------------:|
| abdomen   |       0.813706 |
| adiposity |       0.727994 |
| chest     |       0.702885 |
| hip       |       0.6257   |
| weight    |       0.613156 |
| tight     |       0.561284 |

중간 상관:

|         |   pearson_corr |
|:--------|---------------:|
| knee    |       0.507786 |
| biceps  |       0.493031 |
| neck    |       0.491489 |
| forearm |       0.363277 |

하위(음의 방향 포함):

|        |   pearson_corr |
|:-------|---------------:|
| wrist  |      0.347573  |
| age    |      0.289174  |
| ankle  |      0.266783  |
| height |     -0.0891064 |

## 3) 핵심 변수별 산점도 + 추세선
체지방과의 관계를 직접 보는 섹션입니다. 복부(`abdomen`)는 가장 강한 양의 추세를 보이며, 키(`height`)는 약한 음의 경향을 보입니다.

### abdomen vs body fat
![scatter abdomen](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_abdomen_vs_bodyfat.png)

### adiposity vs body fat
![scatter adiposity](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_adiposity_vs_bodyfat.png)

### chest vs body fat
![scatter chest](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_chest_vs_bodyfat.png)

### hip vs body fat
![scatter hip](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_hip_vs_bodyfat.png)

### weight vs body fat
![scatter weight](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_weight_vs_bodyfat.png)

### height vs body fat
![scatter height](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_height_vs_bodyfat.png)

### age vs body fat
![scatter age](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_age_vs_bodyfat.png)

### wrist vs body fat
![scatter wrist](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/scatter/scatter_wrist_vs_bodyfat.png)

## 4) Box Plot 해석 (체지방 그룹별 분포)
Q1에서 Q4로 갈수록 다수 변수의 중앙값이 상승합니다. 특히 `abdomen`, `chest`, `hip`, `weight`에서 그룹 간 분리가 명확합니다.

### Grouped Box: abdomen
![box group abdomen](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_abdomen.png)

### Grouped Box: chest
![box group chest](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_chest.png)

### Grouped Box: hip
![box group hip](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_hip.png)

### Grouped Box: weight
![box group weight](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_weight.png)

### Grouped Box: adiposity
![box group adiposity](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_adiposity.png)

### Grouped Box: tight
![box group tight](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_tight.png)

### Grouped Box: neck
![box group neck](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_neck.png)

### Grouped Box: height
![box group height](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/boxplot/box_group_height.png)

## 5) Violin Plot 해석 (분포 형태 + 밀도)
Violin plot으로 보면 그룹별 밀도 구조와 꼬리 길이를 확인할 수 있습니다. 일부 변수는 상위 그룹에서 분산이 커집니다.

### Grouped Violin: abdomen
![violin group abdomen](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_abdomen.png)

### Grouped Violin: chest
![violin group chest](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_chest.png)

### Grouped Violin: hip
![violin group hip](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_hip.png)

### Grouped Violin: weight
![violin group weight](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_weight.png)

### Grouped Violin: adiposity
![violin group adiposity](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_adiposity.png)

### Grouped Violin: tight
![violin group tight](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_tight.png)

### Grouped Violin: knee
![violin group knee](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_knee.png)

### Grouped Violin: ankle
![violin group ankle](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_ankle.png)

### Grouped Violin: biceps
![violin group biceps](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_biceps.png)

### Grouped Violin: forearm
![violin group forearm](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_forearm.png)

### Grouped Violin: wrist
![violin group wrist](C:/Users/Administrator/dxAx/orange_example/bodyfat_analysis_plots/violin/violin_group_wrist.png)

## 6) 종합 해석
- 복부 둘레(`abdomen`)가 체지방과 가장 강하게 연결되어, 실무적으로 가장 직관적인 설명 변수입니다.
- `adiposity`, `chest`, `hip`, `weight`도 체지방 증가와 함께 높아지는 경향이 강합니다.
- `height`는 상관이 약하고 음의 방향이라, 체지방 증가를 직접적으로 설명하는 힘은 제한적입니다.
- Box/Violin에서 Q4(고체지방) 그룹은 중심값 상승과 함께 분산 확장 경향이 나타납니다.
- 결론적으로 체지방 해석은 단일 변수보다 `abdomen + chest + adiposity + weight`의 조합으로 보는 것이 가장 설득력 있습니다.
