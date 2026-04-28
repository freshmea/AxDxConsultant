# Marketing Campaigns 분석 보고서

## 분석 개요
- 대상 파일: `C:\Users\Administrator\dxAx\실습결과물\17\14 Marketing Campaigns.xlsx`
- 분석 건수: 1000개 캠페인
- 기간: 2024-01-02 ~ 2026-01-17
- 채널 수: 5개
- 산출물 폴더: `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets`

## 핵심 KPI
- 총 예산: 12976200.00
- 총 집행금액: 11676846.71
- 총 매출: 64943234.30
- 평균 캠페인 기간: 33.73일
- 평균 ROAS: 5.6701
- 평균 CTR: 0.0396
- 평균 CVR: 0.0542

## 채널별 성과 요약
- 매출 기준 최상위 채널은 `Email`이며 총매출 21021486.18, 평균 ROAS 12.8928를 기록했습니다.
- 채널별 효율은 ROAS, CTR, CVR이 균일하지 않아 단순 집행 증액보다 채널별 운영 전략 차별화가 필요합니다.
- 분모가 0인 경우 CTR, CVR, CPC, CPA, ROAS, Budget Utilization, Revenue per Conversion은 `null`로 처리했고 평균 계산에서 제외했습니다.

## 회귀 모델 결과
- 기준선 LinearRegression: R² 0.6348, MAE 22582.8906, RMSE 32212.2794
- RandomForestRegressor: R² 0.5396, MAE 24278.1303, RMSE 36165.5178
- 이번 데이터에서는 LinearRegression 기준선이 RandomForest보다 더 높은 설명력을 보였습니다.
- 중요 피처 상위권은 노출수, 집행금액, 클릭수, 예산 활용률 계열로 나타나며 매출 설명력이 운영 효율 지표와 직접 성과 지표에 집중됩니다.

## 군집 인사이트
- 선택된 군집 수: 3개
- 실루엣 점수: 0.4117
- 최고 효율 군집: `고효율 고수익` / 평균 ROAS 13.5261, 평균 CVR 0.0785
- 최저 효율 군집: `저효율 개선대상` / 평균 ROAS 4.5862, 평균 CVR 0.0519
- 캠페인은 단일 우승 패턴보다 `고효율`, `고집행`, `개선대상` 유형으로 구분되며 채널·집행·전환 구조별 운영 최적화가 가능합니다.

## 실행 제안
1. ROAS 상위 군집의 예산 활용 패턴을 기준 템플릿으로 만들고 유사 캠페인에 재적용합니다.
2. 고집행 저효율 군집은 CTR/CVR 병목을 우선 점검해 소재·랜딩·타기팅을 분리 실험합니다.
3. RandomForest 중요 피처 기준으로 대시보드 핵심 지표를 `Amount Spent`, `Conversions`, `CTR`, `CVR`, `Budget Utilization` 중심으로 재구성합니다.

## 로컬 산출물 경로
- 요약 JSON: `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\marketing_campaigns_summary.json`
- 정제 CSV: `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\cleaned_campaigns.csv`
- 마크다운 보고서: `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\marketing_campaigns_report.md`
- 인포그래픽 프롬프트: `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\infographic_prompt.md`
- 인포그래픽 이미지: `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\marketing_campaigns_infographic.png`

## 그래프 파일
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\actual_vs_predicted_revenue.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\campaign_cluster_pca.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\channel_avg_roas.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\channel_ctr_cvr_boxplot.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\feature_importance_top10.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\impressions_vs_clicks.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\spent_vs_revenue.png`
- `C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets\top_campaigns_revenue_roas.png`
