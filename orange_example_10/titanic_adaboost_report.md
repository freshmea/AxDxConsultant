# Titanic AdaBoost 분석 보고서

## 1) 데이터 및 전처리
- 원본 데이터 행 수: 2201
- 타겟 변수: survived (yes/no)
- 입력 변수: status, age, sex
- 메타 행 제거 후 유효 카테고리만 사용

## 2) 요청된 샘플링/학습 절차
1. Stratified 10-fold 구조로 데이터를 10배 확장 (중복 포함)
2. 확장 데이터 22010건에서 80%를 랜덤 중복 샘플링하여 훈련셋 구성
3. 최종 훈련 샘플 수: 17608
4. 모델: OneHotEncoder + AdaBoostClassifier(Decision Stump 기반)
5. 모델 저장 경로: `C:\Users\Administrator\dxAx\orange_example\titanic_adaboost_model.joblib`

## 3) 500개 재샘플링 평가 (Confusion Matrix)

Confusion Matrix (행=실제, 열=예측, 순서=[no, yes])

| actual\pred | no | yes |
|---|---:|---:|
| no  | 313 | 23 |
| yes | 86 | 78 |

### 분류 성능 지표
- Accuracy: 0.7820
- Precision(yes): 0.7723
- Recall(yes): 0.4756
- F1(yes): 0.5887

## 4) 결과 해석
- 전체 500개 샘플 중 실제 비생존(no) 336건, 실제 생존(yes) 164건입니다.
- 모델은 비생존을 313건 맞췄고(FP=23), 생존을 78건 맞췄습니다(FN=86).
- 생존(yes) 재현율이 낮아, 실제 생존자를 비생존으로 놓치는 경향이 있습니다.
- 비생존(no) 식별 성능이 생존(yes) 식별 성능보다 높아 보수적으로 분류하는 패턴이 나타납니다.
