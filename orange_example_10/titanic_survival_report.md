# Titanic 생존 분석 보고서

## 1. 데이터 개요
- 전체 관측치: 2201건
- 생존자: 711건 (32.30%)

## 2. 통계 분석 (기술통계)

### 2.1 status별 생존

| status   |   survived_no |   survived_yes |   total |   survival_rate |
|:---------|--------------:|---------------:|--------:|----------------:|
| first    |           122 |            203 |     325 |           62.46 |
| second   |           167 |            118 |     285 |           41.4  |
| third    |           528 |            178 |     706 |           25.21 |
| crew     |           673 |            212 |     885 |           23.95 |

### 2.2 age별 생존

| age   |   survived_no |   survived_yes |   total |   survival_rate |
|:------|--------------:|---------------:|--------:|----------------:|
| child |            52 |             57 |     109 |           52.29 |
| adult |          1438 |            654 |    2092 |           31.26 |

### 2.3 sex별 생존

| sex    |   survived_no |   survived_yes |   total |   survival_rate |
|:-------|--------------:|---------------:|--------:|----------------:|
| female |           126 |            344 |     470 |           73.19 |
| male   |          1364 |            367 |    1731 |           21.2  |

### 2.4 status-age-sex 조합 상위(생존률 기준)

|                               |   survived_no |   survived_yes |   total |   survival_rate |
|:------------------------------|--------------:|---------------:|--------:|----------------:|
| ('first', 'child', 'female')  |             0 |              1 |       1 |          100    |
| ('first', 'child', 'male')    |             0 |              5 |       5 |          100    |
| ('second', 'child', 'female') |             0 |             13 |      13 |          100    |
| ('second', 'child', 'male')   |             0 |             11 |      11 |          100    |
| ('first', 'adult', 'female')  |             4 |            140 |     144 |           97.22 |
| ('crew', 'adult', 'female')   |             3 |             20 |      23 |           86.96 |
| ('second', 'adult', 'female') |            13 |             80 |      93 |           86.02 |
| ('third', 'adult', 'female')  |            89 |             76 |     165 |           46.06 |
| ('third', 'child', 'female')  |            17 |             14 |      31 |           45.16 |
| ('first', 'adult', 'male')    |           118 |             57 |     175 |           32.57 |
| ('third', 'child', 'male')    |            35 |             13 |      48 |           27.08 |
| ('crew', 'adult', 'male')     |           670 |            192 |     862 |           22.27 |
| ('third', 'adult', 'male')    |           387 |             75 |     462 |           16.23 |
| ('second', 'adult', 'male')   |           154 |             14 |     168 |            8.33 |

## 3. scikit-learn 예측 분석

모델: One-Hot Encoding + Logistic Regression

- Test Accuracy: 0.7664
- Test ROC-AUC: 0.7313
- 5-Fold CV Accuracy: 0.7783 ± 0.0129
- 5-Fold CV ROC-AUC: 0.7585 ± 0.0080

### 3.1 분류 리포트

```              precision    recall  f1-score   support

          no       0.78      0.91      0.84       299
         yes       0.71      0.46      0.56       142

    accuracy                           0.77       441
   macro avg       0.75      0.69      0.70       441
weighted avg       0.76      0.77      0.75       441
```

### 3.2 변수 영향(로지스틱 계수)

| feature       |   coefficient |
|:--------------|--------------:|
| sex_male      |     -2.41784  |
| age_child     |      1.10959  |
| status_third  |     -0.980403 |
| status_first  |      0.798313 |
| status_second |     -0.129939 |
