from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
import polars as pl
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DEFAULT_INPUT = Path(r"C:\Users\Administrator\dxAx\실습결과물\17\14 Marketing Campaigns.xlsx")
DEFAULT_OUTPUT_DIR = Path(r"C:\Users\Administrator\dxAx\실습결과물\17\marketing_campaigns_assets")
NOTION_PARENT_URL = "https://www.notion.so/343541956f7a80008cb9d08ac25ad3e6"
RANDOM_STATE = 42


@dataclass
class ModelMetrics:
    r2: float
    mae: float
    rmse: float


def setup_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    font_path = Path(r"C:\Windows\Fonts\NotoSansKR-Regular.ttf")
    if font_path.exists():
        fm.fontManager.addfont(str(font_path))
        font_name = fm.FontProperties(fname=str(font_path)).get_name()
        plt.rcParams["font.family"] = font_name
    plt.rcParams["axes.unicode_minus"] = False


def safe_divide(numerator: str, denominator: str) -> pl.Expr:
    return (
        pl.when(pl.col(denominator).is_null() | (pl.col(denominator) == 0))
        .then(None)
        .otherwise(pl.col(numerator) / pl.col(denominator))
    )


def load_campaigns(input_path: Path) -> pl.DataFrame:
    workbook = openpyxl.load_workbook(input_path, read_only=True, data_only=True)
    worksheet = workbook[workbook.sheetnames[0]]
    rows = list(worksheet.iter_rows(values_only=True))
    headers = [str(value) for value in rows[0]]
    records = [row for row in rows[1:] if any(value is not None for value in row)]
    frame = pl.DataFrame(records, schema=headers, orient="row")

    frame = frame.with_columns(
        [
            pl.col("Start Date").cast(pl.Date),
            pl.col("End Date").cast(pl.Date),
            pl.col("Budget Allocated").cast(pl.Float64),
            pl.col("Amount Spent").cast(pl.Float64),
            pl.col("Impressions").cast(pl.Float64),
            pl.col("Clicks").cast(pl.Float64),
            pl.col("Conversions").cast(pl.Float64),
            pl.col("Revenue Generated").cast(pl.Float64),
        ]
    )

    return frame.with_columns(
        [
            (pl.col("End Date") - pl.col("Start Date")).dt.total_days().alias("Campaign Duration Days"),
            safe_divide("Clicks", "Impressions").alias("CTR"),
            safe_divide("Conversions", "Clicks").alias("CVR"),
            safe_divide("Amount Spent", "Clicks").alias("CPC"),
            safe_divide("Amount Spent", "Conversions").alias("CPA"),
            safe_divide("Revenue Generated", "Amount Spent").alias("ROAS"),
            safe_divide("Amount Spent", "Budget Allocated").alias("Budget Utilization"),
            safe_divide("Revenue Generated", "Conversions").alias("Revenue per Conversion"),
            pl.col("Start Date").dt.year().alias("Start Year"),
            pl.col("Start Date").dt.quarter().alias("Start Quarter"),
        ]
    )


def model_metrics(y_true, y_pred) -> ModelMetrics:
    return ModelMetrics(
        r2=round(float(r2_score(y_true, y_pred)), 4),
        mae=round(float(mean_absolute_error(y_true, y_pred)), 4),
        rmse=round(float(mean_squared_error(y_true, y_pred) ** 0.5), 4),
    )


def as_python(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: as_python(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_python(item) for item in value]
    return value


def build_summary(
    frame: pl.DataFrame,
    baseline_metrics: ModelMetrics,
    rf_metrics: ModelMetrics,
    feature_importance: list[dict[str, Any]],
    cluster_summary: list[dict[str, Any]],
    cluster_choice: int,
    silhouette: float,
    output_dir: Path,
) -> dict[str, Any]:
    channel_summary = (
        frame.group_by("Channel")
        .agg(
            [
                pl.len().alias("campaign_count"),
                pl.col("Budget Allocated").sum().round(2).alias("budget_allocated_sum"),
                pl.col("Amount Spent").sum().round(2).alias("amount_spent_sum"),
                pl.col("Revenue Generated").sum().round(2).alias("revenue_sum"),
                pl.col("Impressions").sum().round(0).alias("impressions_sum"),
                pl.col("Clicks").sum().round(0).alias("clicks_sum"),
                pl.col("Conversions").sum().round(0).alias("conversions_sum"),
                pl.col("ROAS").mean().round(4).alias("avg_roas"),
                pl.col("CTR").mean().round(4).alias("avg_ctr"),
                pl.col("CVR").mean().round(4).alias("avg_cvr"),
            ]
        )
        .sort("revenue_sum", descending=True)
    )

    quarterly_summary = (
        frame.group_by(["Start Year", "Start Quarter"])
        .agg(
            [
                pl.len().alias("campaign_count"),
                pl.col("Amount Spent").sum().round(2).alias("amount_spent_sum"),
                pl.col("Revenue Generated").sum().round(2).alias("revenue_sum"),
                pl.col("ROAS").mean().round(4).alias("avg_roas"),
            ]
        )
        .sort(["Start Year", "Start Quarter"])
    )

    top_campaigns = (
        frame.select(
            [
                "Campaign ID",
                "Campaign Name",
                "Channel",
                "Amount Spent",
                "Revenue Generated",
                "ROAS",
                "CTR",
                "CVR",
            ]
        )
        .sort("Revenue Generated", descending=True)
        .head(10)
    )

    graph_paths = sorted(str(path.resolve()) for path in output_dir.glob("*.png"))

    return {
        "input_file": str(DEFAULT_INPUT.resolve()),
        "output_dir": str(output_dir.resolve()),
        "rows": frame.height,
        "columns": frame.columns,
        "date_range": {
            "start": as_python(frame.select(pl.col("Start Date").min()).item()),
            "end": as_python(frame.select(pl.col("End Date").max()).item()),
        },
        "overview": {
            "campaign_count": frame.height,
            "channel_count": frame.select(pl.col("Channel").n_unique()).item(),
            "total_budget_allocated": round(float(frame.select(pl.col("Budget Allocated").sum()).item()), 2),
            "total_amount_spent": round(float(frame.select(pl.col("Amount Spent").sum()).item()), 2),
            "total_revenue_generated": round(float(frame.select(pl.col("Revenue Generated").sum()).item()), 2),
            "avg_campaign_duration_days": round(
                float(frame.select(pl.col("Campaign Duration Days").mean()).item()), 2
            ),
            "avg_roas": round(float(frame.select(pl.col("ROAS").mean()).item()), 4),
            "avg_ctr": round(float(frame.select(pl.col("CTR").mean()).item()), 4),
            "avg_cvr": round(float(frame.select(pl.col("CVR").mean()).item()), 4),
        },
        "channel_summary": channel_summary.to_dicts(),
        "quarterly_summary": quarterly_summary.to_dicts(),
        "top_campaigns": top_campaigns.to_dicts(),
        "modeling": {
            "baseline_linear_regression": asdict(baseline_metrics),
            "random_forest_regressor": asdict(rf_metrics),
            "feature_importance_top10": feature_importance,
        },
        "clustering": {
            "selected_k": cluster_choice,
            "silhouette_score": round(float(silhouette), 4),
            "cluster_summary": cluster_summary,
        },
        "artifacts": {
            "graphs": graph_paths,
            "report_markdown": str((output_dir / "marketing_campaigns_report.md").resolve()),
            "cleaned_csv": str((output_dir / "cleaned_campaigns.csv").resolve()),
            "summary_json": str((output_dir / "marketing_campaigns_summary.json").resolve()),
            "infographic_prompt": str((output_dir / "infographic_prompt.md").resolve()),
            "infographic_image": str((output_dir / "marketing_campaigns_infographic.png").resolve()),
        },
        "notion_parent_url": NOTION_PARENT_URL,
    }


def choose_cluster_labels(cluster_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labeled = []
    sorted_rows = sorted(cluster_rows, key=lambda row: row["avg_roas"], reverse=True)
    label_map: dict[int, str] = {}
    if sorted_rows:
        label_map[sorted_rows[0]["cluster"]] = "고효율 고수익"
    if len(sorted_rows) > 1:
        label_map[sorted_rows[-1]["cluster"]] = "저효율 개선대상"
    for row in cluster_rows:
        cluster_id = row["cluster"]
        if cluster_id not in label_map:
            if row["avg_amount_spent"] >= sum(item["avg_amount_spent"] for item in cluster_rows) / len(cluster_rows):
                label_map[cluster_id] = "고집행 고매출"
            else:
                label_map[cluster_id] = "균형형 캠페인"
        row["label"] = label_map[cluster_id]
        labeled.append(row)
    return labeled


def create_visualizations(
    frame: pl.DataFrame,
    predictions_frame: pl.DataFrame,
    feature_importance: list[dict[str, Any]],
    cluster_plot_frame: pl.DataFrame,
    output_dir: Path,
) -> None:
    setup_plot_style()
    frame_pd = pd.DataFrame(frame.to_dicts())

    channel_roas = frame.group_by("Channel").agg(pl.col("ROAS").mean().alias("avg_roas")).sort(
        "avg_roas", descending=True
    )
    plt.figure(figsize=(12, 7))
    channel_roas_pd = pd.DataFrame(channel_roas.to_dicts())
    sns.barplot(
        data=channel_roas_pd,
        x="Channel",
        y="avg_roas",
        hue="Channel",
        palette="Blues_r",
        legend=False,
    )
    plt.title("채널별 평균 ROAS")
    plt.xlabel("채널")
    plt.ylabel("평균 ROAS")
    plt.tight_layout()
    plt.savefig(output_dir / "channel_avg_roas.png", dpi=200)
    plt.close()

    ctr_cvr = frame.select(["Channel", "CTR", "CVR"]).unpivot(
        index="Channel", on=["CTR", "CVR"], variable_name="metric", value_name="value"
    )
    plt.figure(figsize=(14, 8))
    sns.boxplot(data=pd.DataFrame(ctr_cvr.to_dicts()), x="Channel", y="value", hue="metric")
    plt.title("채널별 CTR/CVR 분포")
    plt.xlabel("채널")
    plt.ylabel("비율")
    plt.legend(title="지표")
    plt.tight_layout()
    plt.savefig(output_dir / "channel_ctr_cvr_boxplot.png", dpi=200)
    plt.close()

    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=frame_pd,
        x="Amount Spent",
        y="Revenue Generated",
        hue="Channel",
        size="Conversions",
        palette="tab10",
    )
    plt.title("집행금액 대비 매출")
    plt.xlabel("Amount Spent")
    plt.ylabel("Revenue Generated")
    plt.tight_layout()
    plt.savefig(output_dir / "spent_vs_revenue.png", dpi=200)
    plt.close()

    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=frame_pd,
        x="Impressions",
        y="Clicks",
        hue="Channel",
        size="Budget Allocated",
        palette="tab10",
    )
    plt.title("노출수 대비 클릭수")
    plt.xlabel("Impressions")
    plt.ylabel("Clicks")
    plt.tight_layout()
    plt.savefig(output_dir / "impressions_vs_clicks.png", dpi=200)
    plt.close()

    top_campaigns = frame.sort("Revenue Generated", descending=True).head(10).select(
        ["Campaign Name", "Revenue Generated", "ROAS"]
    )
    top_campaigns_pd = pd.DataFrame(top_campaigns.to_dicts())
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    sns.barplot(
        data=top_campaigns_pd,
        y="Campaign Name",
        x="Revenue Generated",
        hue="Campaign Name",
        ax=axes[0],
        palette="Greens_r",
        legend=False,
    )
    axes[0].set_title("상위 10개 캠페인 매출")
    axes[0].set_xlabel("Revenue Generated")
    axes[0].set_ylabel("Campaign Name")
    sns.barplot(
        data=top_campaigns_pd,
        y="Campaign Name",
        x="ROAS",
        hue="Campaign Name",
        ax=axes[1],
        palette="Oranges_r",
        legend=False,
    )
    axes[1].set_title("상위 10개 캠페인 ROAS")
    axes[1].set_xlabel("ROAS")
    axes[1].set_ylabel("")
    plt.tight_layout()
    plt.savefig(output_dir / "top_campaigns_revenue_roas.png", dpi=200)
    plt.close()

    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=pd.DataFrame(predictions_frame.to_dicts()), x="actual", y="predicted")
    min_val = float(predictions_frame.select(pl.min_horizontal(["actual", "predicted"]).min()).item())
    max_val = float(predictions_frame.select(pl.max_horizontal(["actual", "predicted"]).max()).item())
    plt.plot([min_val, max_val], [min_val, max_val], color="red", linestyle="--")
    plt.title("실제 매출 vs 예측 매출")
    plt.xlabel("실제 매출")
    plt.ylabel("예측 매출")
    plt.tight_layout()
    plt.savefig(output_dir / "actual_vs_predicted_revenue.png", dpi=200)
    plt.close()

    plt.figure(figsize=(12, 8))
    importance_pd = pd.DataFrame(feature_importance)
    sns.barplot(
        data=importance_pd,
        x="importance",
        y="feature",
        hue="feature",
        palette="Purples_r",
        legend=False,
    )
    plt.title("RandomForest 중요 피처 Top 10")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance_top10.png", dpi=200)
    plt.close()

    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=pd.DataFrame(cluster_plot_frame.to_dicts()),
        x="pca_x",
        y="pca_y",
        hue="cluster_label",
        style="Channel",
        palette="Set2",
    )
    plt.title("캠페인 군집 결과 (PCA 2D)")
    plt.xlabel("PCA 1")
    plt.ylabel("PCA 2")
    plt.tight_layout()
    plt.savefig(output_dir / "campaign_cluster_pca.png", dpi=200)
    plt.close()


def generate_report(summary: dict[str, Any], output_dir: Path) -> str:
    overview = summary["overview"]
    top_channel = summary["channel_summary"][0]
    cluster_rows = summary["clustering"]["cluster_summary"]
    best_cluster = max(cluster_rows, key=lambda row: row["avg_roas"])
    weak_cluster = min(cluster_rows, key=lambda row: row["avg_roas"])
    linear_r2 = summary["modeling"]["baseline_linear_regression"]["r2"]
    rf_r2 = summary["modeling"]["random_forest_regressor"]["r2"]
    if linear_r2 >= rf_r2:
        model_read = "이번 데이터에서는 LinearRegression 기준선이 RandomForest보다 더 높은 설명력을 보였습니다."
    else:
        model_read = "이번 데이터에서는 RandomForest가 기준선보다 더 높은 설명력을 보였습니다."

    report = f"""# Marketing Campaigns 분석 보고서

## 분석 개요
- 대상 파일: `{summary['input_file']}`
- 분석 건수: {summary['rows']}개 캠페인
- 기간: {summary['date_range']['start']} ~ {summary['date_range']['end']}
- 채널 수: {overview['channel_count']}개
- 산출물 폴더: `{summary['output_dir']}`

## 핵심 KPI
- 총 예산: {overview['total_budget_allocated']:.2f}
- 총 집행금액: {overview['total_amount_spent']:.2f}
- 총 매출: {overview['total_revenue_generated']:.2f}
- 평균 캠페인 기간: {overview['avg_campaign_duration_days']:.2f}일
- 평균 ROAS: {overview['avg_roas']:.4f}
- 평균 CTR: {overview['avg_ctr']:.4f}
- 평균 CVR: {overview['avg_cvr']:.4f}

## 채널별 성과 요약
- 매출 기준 최상위 채널은 `{top_channel['Channel']}`이며 총매출 {top_channel['revenue_sum']:.2f}, 평균 ROAS {top_channel['avg_roas']:.4f}를 기록했습니다.
- 채널별 효율은 ROAS, CTR, CVR이 균일하지 않아 단순 집행 증액보다 채널별 운영 전략 차별화가 필요합니다.
- 분모가 0인 경우 CTR, CVR, CPC, CPA, ROAS, Budget Utilization, Revenue per Conversion은 `null`로 처리했고 평균 계산에서 제외했습니다.

## 회귀 모델 결과
- 기준선 LinearRegression: R² {summary['modeling']['baseline_linear_regression']['r2']:.4f}, MAE {summary['modeling']['baseline_linear_regression']['mae']:.4f}, RMSE {summary['modeling']['baseline_linear_regression']['rmse']:.4f}
- RandomForestRegressor: R² {summary['modeling']['random_forest_regressor']['r2']:.4f}, MAE {summary['modeling']['random_forest_regressor']['mae']:.4f}, RMSE {summary['modeling']['random_forest_regressor']['rmse']:.4f}
- {model_read}
- 중요 피처 상위권은 노출수, 집행금액, 클릭수, 예산 활용률 계열로 나타나며 매출 설명력이 운영 효율 지표와 직접 성과 지표에 집중됩니다.

## 군집 인사이트
- 선택된 군집 수: {summary['clustering']['selected_k']}개
- 실루엣 점수: {summary['clustering']['silhouette_score']:.4f}
- 최고 효율 군집: `{best_cluster['label']}` / 평균 ROAS {best_cluster['avg_roas']:.4f}, 평균 CVR {best_cluster['avg_cvr']:.4f}
- 최저 효율 군집: `{weak_cluster['label']}` / 평균 ROAS {weak_cluster['avg_roas']:.4f}, 평균 CVR {weak_cluster['avg_cvr']:.4f}
- 캠페인은 단일 우승 패턴보다 `고효율`, `고집행`, `개선대상` 유형으로 구분되며 채널·집행·전환 구조별 운영 최적화가 가능합니다.

## 실행 제안
1. ROAS 상위 군집의 예산 활용 패턴을 기준 템플릿으로 만들고 유사 캠페인에 재적용합니다.
2. 고집행 저효율 군집은 CTR/CVR 병목을 우선 점검해 소재·랜딩·타기팅을 분리 실험합니다.
3. RandomForest 중요 피처 기준으로 대시보드 핵심 지표를 `Amount Spent`, `Conversions`, `CTR`, `CVR`, `Budget Utilization` 중심으로 재구성합니다.

## 로컬 산출물 경로
- 요약 JSON: `{summary['artifacts']['summary_json']}`
- 정제 CSV: `{summary['artifacts']['cleaned_csv']}`
- 마크다운 보고서: `{summary['artifacts']['report_markdown']}`
- 인포그래픽 프롬프트: `{summary['artifacts']['infographic_prompt']}`
- 인포그래픽 이미지: `{summary['artifacts']['infographic_image']}`

## 그래프 파일
"""
    for graph_path in summary["artifacts"]["graphs"]:
        report += f"- `{graph_path}`\n"
    return report


def generate_infographic_prompt(summary: dict[str, Any]) -> str:
    overview = summary["overview"]
    top_channel = summary["channel_summary"][0]
    best_cluster = max(summary["clustering"]["cluster_summary"], key=lambda row: row["avg_roas"])
    weak_cluster = min(summary["clustering"]["cluster_summary"], key=lambda row: row["avg_roas"])

    return f"""# Marketing Campaigns Infographic Prompt

Use case: infographic-diagram
Asset type: executive one-page business infographic
Primary request: 2025 marketing campaign performance infographic in Korean for executives
Style/medium: clean corporate infographic, data-storytelling layout, sharp typography, modern dashboard aesthetic
Composition/framing: one-page vertical infographic, A4-ish ratio, strong section dividers, KPI cards at top, charts and insights in middle, action items at bottom
Lighting/mood: bright, crisp, professional, high-clarity presentation style
Color palette: white background, navy, teal, sky blue, muted orange accents
Text (verbatim): "마케팅 캠페인 분석 요약", "총 매출", "평균 ROAS", "평균 CTR", "평균 CVR", "채널별 성과", "회귀 모델 결과", "군집 인사이트", "실행 제안"
Constraints: all text must be in Korean, no watermark, no fake logos, no unrelated icons, no clutter, numeric emphasis must be large and readable
Avoid: dark mode, poster-like advertising style, 3D gimmicks, stock-photo collage

Required content:
- Title: 마케팅 캠페인 분석 요약
- Subtitle: Marketing Campaigns.xlsx 기반 성과 분석
- KPI cards with these values:
  - 총 매출: {overview['total_revenue_generated']:.2f}
  - 평균 ROAS: {overview['avg_roas']:.4f}
  - 평균 CTR: {overview['avg_ctr']:.4f}
  - 평균 CVR: {overview['avg_cvr']:.4f}
- Channel highlight:
  - 최고 매출 채널: {top_channel['Channel']}
  - 채널 매출: {top_channel['revenue_sum']:.2f}
  - 채널 평균 ROAS: {top_channel['avg_roas']:.4f}
- Model summary:
  - RandomForest R²: {summary['modeling']['random_forest_regressor']['r2']:.4f}
  - RandomForest MAE: {summary['modeling']['random_forest_regressor']['mae']:.4f}
- Cluster summary:
  - 최고 효율 군집: {best_cluster['label']} / ROAS {best_cluster['avg_roas']:.4f}
  - 개선 필요 군집: {weak_cluster['label']} / ROAS {weak_cluster['avg_roas']:.4f}
- Top 3 insights:
  1. 집행금액과 전환수가 매출 설명력의 핵심
  2. 채널별 효율 차이가 커서 균등 배분보다 선택과 집중이 유리
  3. 저효율 군집은 CTR/CVR 병목 개선이 우선
- Bottom action strip with 3 actions:
  - 고효율 군집 운영 패턴 확장
  - 저효율 채널/캠페인 A/B 테스트 강화
  - 핵심 지표 중심 대시보드 재정의

Visual direction:
- Include icon-like shapes, arrows, mini trend bars, KPI cards, cluster badges, and abstract chart motifs
- The infographic should look like a polished board-report summary slide converted into a poster
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze marketing campaigns with polars, scikit-learn, and seaborn.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = load_campaigns(input_path)
    frame.write_csv(output_dir / "cleaned_campaigns.csv")

    feature_columns = [
        "Channel",
        "Budget Allocated",
        "Amount Spent",
        "Impressions",
        "Clicks",
        "Conversions",
        "Campaign Duration Days",
        "CTR",
        "CVR",
        "CPC",
        "CPA",
        "Budget Utilization",
    ]
    target_column = "Revenue Generated"

    model_frame = frame.select(feature_columns + [target_column]).drop_nulls(target_column)
    train_df, test_df = train_test_split(
        pd.DataFrame(model_frame.to_dicts()), test_size=0.2, random_state=RANDOM_STATE
    )

    categorical_features = ["Channel"]
    numeric_features = [column for column in feature_columns if column not in categorical_features]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
        ]
    )

    baseline_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", LinearRegression()),
        ]
    )
    baseline_model.fit(train_df[feature_columns], train_df[target_column])
    baseline_predictions = baseline_model.predict(test_df[feature_columns])
    baseline_metrics = model_metrics(test_df[target_column], baseline_predictions)

    rf_model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=300, random_state=RANDOM_STATE)),
        ]
    )
    rf_model.fit(train_df[feature_columns], train_df[target_column])
    rf_predictions = rf_model.predict(test_df[feature_columns])
    rf_metrics = model_metrics(test_df[target_column], rf_predictions)

    transformed_feature_names = rf_model.named_steps["preprocessor"].get_feature_names_out()
    importances = rf_model.named_steps["regressor"].feature_importances_
    feature_importance = (
        pl.DataFrame({"feature": transformed_feature_names, "importance": importances})
        .sort("importance", descending=True)
        .head(10)
        .with_columns(pl.col("importance").round(6))
        .to_dicts()
    )

    cluster_columns = [
        "CTR",
        "CVR",
        "CPC",
        "CPA",
        "ROAS",
        "Budget Utilization",
        "Amount Spent",
        "Revenue Generated",
        "Conversions",
    ]
    cluster_data = frame.select(cluster_columns + ["Channel", "Campaign Name"]).drop_nulls()
    scaler = StandardScaler()
    cluster_matrix = scaler.fit_transform(pd.DataFrame(cluster_data.select(cluster_columns).to_dicts()))

    best_score = -1.0
    best_k = 3
    best_labels = None
    for cluster_count in range(3, 7):
        model = KMeans(n_clusters=cluster_count, random_state=RANDOM_STATE, n_init=10)
        labels = model.fit_predict(cluster_matrix)
        score = silhouette_score(cluster_matrix, labels)
        if score > best_score:
            best_score = score
            best_k = cluster_count
            best_labels = labels

    assert best_labels is not None
    cluster_labeled = cluster_data.with_columns(pl.Series("cluster", best_labels))
    cluster_summary = (
        cluster_labeled.group_by("cluster")
        .agg(
            [
                pl.len().alias("campaign_count"),
                pl.col("ROAS").mean().round(4).alias("avg_roas"),
                pl.col("CTR").mean().round(4).alias("avg_ctr"),
                pl.col("CVR").mean().round(4).alias("avg_cvr"),
                pl.col("Amount Spent").mean().round(2).alias("avg_amount_spent"),
                pl.col("Revenue Generated").mean().round(2).alias("avg_revenue"),
            ]
        )
        .sort("cluster")
        .to_dicts()
    )
    cluster_summary = choose_cluster_labels(cluster_summary)
    cluster_label_map = {row["cluster"]: row["label"] for row in cluster_summary}
    cluster_plot_frame = cluster_labeled.with_columns(
        pl.col("cluster").replace_strict(cluster_label_map).alias("cluster_label")
    )

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    pca_projection = pca.fit_transform(cluster_matrix)
    cluster_plot_frame = cluster_plot_frame.with_columns(
        [
            pl.Series("pca_x", pca_projection[:, 0]),
            pl.Series("pca_y", pca_projection[:, 1]),
        ]
    )

    predictions_frame = pl.DataFrame(
        {"actual": test_df[target_column].tolist(), "predicted": rf_predictions.tolist()}
    ).with_columns(
        [
            pl.col("actual").round(2),
            pl.col("predicted").round(2),
        ]
    )

    create_visualizations(frame, predictions_frame, feature_importance, cluster_plot_frame, output_dir)

    summary = build_summary(
        frame=frame,
        baseline_metrics=baseline_metrics,
        rf_metrics=rf_metrics,
        feature_importance=feature_importance,
        cluster_summary=cluster_summary,
        cluster_choice=best_k,
        silhouette=best_score,
        output_dir=output_dir,
    )

    report_text = generate_report(summary, output_dir)
    infographic_prompt = generate_infographic_prompt(summary)

    (output_dir / "marketing_campaigns_report.md").write_text(report_text, encoding="utf-8-sig")
    (output_dir / "infographic_prompt.md").write_text(infographic_prompt, encoding="utf-8-sig")
    (output_dir / "marketing_campaigns_summary.json").write_text(
        json.dumps(as_python(summary), ensure_ascii=False, indent=2),
        encoding="utf-8-sig",
    )

    print(json.dumps(as_python(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
