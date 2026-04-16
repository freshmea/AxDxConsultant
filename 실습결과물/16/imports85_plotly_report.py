# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


ROOT = Path(__file__).resolve().parent
RAW_CSV = ROOT / "imports-85.csv"
OUT_MD = ROOT / "imports-85_interactive_report.md"
OUT_HTML = ROOT / "imports-85_interactive_dashboard.html"
OUT_CSV = ROOT / "imports-85_reintegrated_analysis_base.csv"
ASSET_DIR = ROOT / "imports85_report_assets"

NUMERIC_COLUMNS = [
    "price",
    "symboling",
    "normalized-losses",
    "wheel-base",
    "length",
    "width",
    "height",
    "curb-weight",
    "engine-size",
    "bore",
    "stroke",
    "compression-ratio",
    "horsepower",
    "peak-rpm",
    "city-mpg",
    "highway-mpg",
]
CATEGORICAL_COLUMNS = [
    "make",
    "fuel-type",
    "aspiration",
    "num-of-doors",
    "body-style",
    "drive-wheels",
    "engine-location",
    "engine-type",
    "num-of-cylinders",
    "fuel-system",
]
DISPLAY_COLUMNS = [
    "make",
    "body-style",
    "drive-wheels",
    "fuel-type",
    "engine-size",
    "horsepower",
    "curb-weight",
    "avg_mpg",
    "price",
    "segment",
]
SEGMENT_ORDER = [
    "Premium Performance",
    "Balanced Core",
    "Value Efficiency",
    "Budget Practical",
]


def load_and_clean_data(path: Path) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, dtype=str)
    raw.columns = [column.strip() for column in raw.columns]

    meta_mask = raw["price"].astype(str).str.strip().isin(["continuous", "class"])
    cleaned = raw.loc[~meta_mask].copy()
    removed_meta_rows = int(meta_mask.sum())

    cleaned = cleaned.replace({"?": pd.NA, "": pd.NA})
    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    for column in CATEGORICAL_COLUMNS:
        cleaned[column] = cleaned[column].astype("string").str.strip()

    missing_before = cleaned.isna().sum().to_dict()
    original_missing_flags = cleaned.isna().copy()

    group_mode = (
        cleaned.groupby(["make", "body-style"])["num-of-doors"]
        .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else pd.NA)
    )
    fallback_door_mode = cleaned["num-of-doors"].mode().iloc[0]
    cleaned["num-of-doors"] = cleaned.apply(
        lambda row: (
            group_mode.get((row["make"], row["body-style"]), fallback_door_mode)
            if pd.isna(row["num-of-doors"])
            else row["num-of-doors"]
        ),
        axis=1,
    )

    normalized_by_make = cleaned.groupby("make")["normalized-losses"].transform("median")
    cleaned["normalized-losses"] = cleaned["normalized-losses"].fillna(normalized_by_make)

    for column in ["bore", "stroke"]:
        group_fill = cleaned.groupby(["engine-type", "num-of-cylinders"])[column].transform("median")
        cleaned[column] = cleaned[column].fillna(group_fill).fillna(cleaned[column].median())

    for column in ["horsepower", "peak-rpm"]:
        group_fill = cleaned.groupby(["num-of-cylinders", "aspiration"])[column].transform("median")
        cleaned[column] = cleaned[column].fillna(group_fill).fillna(cleaned[column].median())

    price_fill = cleaned.groupby(["make", "body-style"])["price"].transform("median")
    cleaned["price"] = cleaned["price"].fillna(price_fill).fillna(cleaned["price"].median())

    for column in CATEGORICAL_COLUMNS:
        if cleaned[column].isna().any():
            mode_value = cleaned[column].mode().iloc[0] if not cleaned[column].mode().empty else "Unknown"
            cleaned[column] = cleaned[column].fillna(mode_value)

    for column in NUMERIC_COLUMNS:
        if cleaned[column].isna().any():
            cleaned[column] = cleaned[column].fillna(cleaned[column].median())

    cleaned["avg_mpg"] = (cleaned["city-mpg"] + cleaned["highway-mpg"]) / 2
    cleaned["footprint"] = cleaned["length"] * cleaned["width"]
    cleaned["price_per_hp"] = cleaned["price"] / cleaned["horsepower"]
    cleaned["hp_per_1000usd"] = cleaned["horsepower"] / cleaned["price"] * 1000
    cleaned["power_density"] = cleaned["horsepower"] / cleaned["engine-size"]
    cleaned["weight_per_hp"] = cleaned["curb-weight"] / cleaned["horsepower"]

    price_q1 = cleaned["price"].quantile(0.25)
    price_q3 = cleaned["price"].quantile(0.75)
    hp_q3 = cleaned["horsepower"].quantile(0.75)
    mpg_q3 = cleaned["avg_mpg"].quantile(0.75)
    mpg_q2 = cleaned["avg_mpg"].median()

    def classify_segment(row):
        if row["price"] >= price_q3 and row["horsepower"] >= hp_q3:
            return "Premium Performance"
        if row["price"] <= price_q1 and row["avg_mpg"] >= mpg_q3:
            return "Value Efficiency"
        if row["price"] <= cleaned["price"].median() and row["avg_mpg"] >= mpg_q2:
            return "Budget Practical"
        return "Balanced Core"

    cleaned["segment"] = cleaned.apply(classify_segment, axis=1)
    cleaned["price_band"] = pd.qcut(cleaned["price"], 10, duplicates="drop")
    cleaned["price_decile_label"] = cleaned["price_band"].astype(str)
    cleaned["source_status"] = "original_record_retained"
    cleaned["outlier_review_status"] = "reviewed_valid_retained"
    cleaned["imputed_columns"] = original_missing_flags.apply(
        lambda row: ", ".join([column for column, missing in row.items() if bool(missing)]),
        axis=1,
    )
    cleaned["imputed_columns"] = cleaned["imputed_columns"].replace("", "none")
    cleaned["imputed_count"] = original_missing_flags.sum(axis=1).astype(int)

    cleaned["make_group"] = cleaned["make"].where(
        cleaned["make"].isin(cleaned["make"].value_counts().head(8).index),
        "other",
    )

    cleaning_summary = {
        "rows_after_cleaning": int(cleaned.shape[0]),
        "columns_after_cleaning": int(cleaned.shape[1]),
        "removed_meta_rows": removed_meta_rows,
        "retained_rows": int(cleaned.shape[0]),
        "missing_before": missing_before,
        "missing_after": cleaned.isna().sum().to_dict(),
    }
    return cleaned, cleaning_summary


def apply_layout(fig: go.Figure, title: str, height: int = 520) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        title=title,
        height=height,
        font=dict(family="Arial", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(l=50, r=30, t=70, b=50),
    )
    return fig


def save_figure(fig: go.Figure, name: str) -> dict:
    html_path = ASSET_DIR / f"{name}.html"
    fig.write_html(html_path, include_plotlyjs="cdn", full_html=False)
    return {"name": name, "html": html_path, "fig": fig}


def correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    numeric = df[
        [
            "price",
            "engine-size",
            "horsepower",
            "curb-weight",
            "avg_mpg",
            "city-mpg",
            "highway-mpg",
            "wheel-base",
            "width",
            "length",
            "compression-ratio",
            "price_per_hp",
            "power_density",
        ]
    ]
    corr = numeric.corr(numeric_only=True)["price"].sort_values(ascending=False)
    return corr.reset_index().rename(columns={"index": "variable", "price": "correlation"})


def build_figures(df: pd.DataFrame, cleaning_summary: dict) -> tuple[dict, dict]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    figures = {}

    key_summary = pd.DataFrame(
        {
            "Metric": [
                "Rows",
                "Columns",
                "Removed meta rows",
                "Brands",
                "Body styles",
                "Drive wheel types",
                "Fuel types",
                "Median price",
                "Median horsepower",
                "Median avg_mpg",
            ],
            "Value": [
                cleaning_summary["rows_after_cleaning"],
                cleaning_summary["columns_after_cleaning"],
                cleaning_summary["removed_meta_rows"],
                df["make"].nunique(),
                df["body-style"].nunique(),
                df["drive-wheels"].nunique(),
                df["fuel-type"].nunique(),
                f"{df['price'].median():,.0f}",
                f"{df['horsepower'].median():,.0f}",
                f"{df['avg_mpg'].median():.1f}",
            ],
        }
    )
    table_fig = go.Figure(
        data=[
            go.Table(
                header=dict(values=list(key_summary.columns), fill_color="#1f3c88", font=dict(color="white")),
                cells=dict(values=[key_summary["Metric"], key_summary["Value"]], fill_color="#f7f9fc"),
            )
        ]
    )
    figures["overview_table"] = save_figure(apply_layout(table_fig, "핵심 데이터 개요", 420), "overview_table")

    brand_counts = (
        df["make"].value_counts().head(12).reset_index().rename(columns={"index": "make", "count": "count"})
    )
    brand_bar = px.bar(
        brand_counts,
        x="make",
        y="count",
        text="count",
        color="count",
        color_continuous_scale="Blues",
        title="브랜드별 표본 수 Top 12",
    )
    brand_bar.update_traces(hovertemplate="브랜드=%{x}<br>표본 수=%{y}<extra></extra>")
    brand_bar.update_layout(coloraxis_showscale=False, xaxis_title="Brand", yaxis_title="Rows")
    figures["brand_counts"] = save_figure(apply_layout(brand_bar, "브랜드별 표본 수 Top 12"), "brand_counts")

    fuel_share = df["fuel-type"].value_counts().reset_index().rename(columns={"index": "fuel-type", "count": "count"})
    fuel_pie = px.pie(
        fuel_share,
        names="fuel-type",
        values="count",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="연료 방식 비중",
    )
    fuel_pie.update_traces(textposition="inside", textinfo="percent+label")
    figures["fuel_share"] = save_figure(apply_layout(fuel_pie, "연료 방식 비중", 480), "fuel_share")

    dist_fig = make_subplots(rows=2, cols=2, subplot_titles=("Price", "Engine Size", "Horsepower", "Average MPG"))
    histogram_specs = [
        ("price", 1, 1, "#1f77b4"),
        ("engine-size", 1, 2, "#ff7f0e"),
        ("horsepower", 2, 1, "#2ca02c"),
        ("avg_mpg", 2, 2, "#d62728"),
    ]
    for column, row, col, color in histogram_specs:
        dist_fig.add_trace(
            go.Histogram(
                x=df[column],
                marker_color=color,
                nbinsx=20,
                name=column,
                hovertemplate=f"{column}=%{{x}}<br>Count=%{{y}}<extra></extra>",
                showlegend=False,
            ),
            row=row,
            col=col,
        )
    dist_fig.update_xaxes(title_text="Price", row=1, col=1)
    dist_fig.update_xaxes(title_text="Engine Size", row=1, col=2)
    dist_fig.update_xaxes(title_text="Horsepower", row=2, col=1)
    dist_fig.update_xaxes(title_text="Average MPG", row=2, col=2)
    dist_fig.update_yaxes(title_text="Count")
    figures["distribution_panel"] = save_figure(
        apply_layout(dist_fig, "핵심 수치형 변수 분포", 700),
        "distribution_panel",
    )

    scatter_configs = [
        ("engine-size", "price", "horsepower", "drive-wheels", "scatter_engine_price", "엔진 크기와 가격의 관계"),
        ("horsepower", "price", "engine-size", "fuel-type", "scatter_hp_price", "마력과 가격의 관계"),
        ("curb-weight", "price", "horsepower", "drive-wheels", "scatter_weight_price", "차량 중량과 가격의 관계"),
        ("avg_mpg", "price", "engine-size", "fuel-type", "scatter_mpg_price", "평균 연비와 가격의 관계"),
    ]
    for x_col, y_col, size_col, symbol_col, name, title in scatter_configs:
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color="body-style",
            size=size_col,
            symbol=symbol_col,
            hover_data=["make", "body-style", "fuel-type", "drive-wheels", "avg_mpg"],
            trendline="ols",
            facet_col="fuel-type" if x_col in ("engine-size", "avg_mpg") else None,
            title=title,
        )
        fig.update_layout(xaxis_title=x_col, yaxis_title=y_col)
        figures[name] = save_figure(apply_layout(fig, title, 560), name)

    top_brands = df["make"].value_counts().head(10).index
    brand_metrics = (
        df[df["make"].isin(top_brands)]
        .groupby("make", as_index=False)
        .agg(avg_price=("price", "mean"), avg_hp=("horsepower", "mean"), avg_mpg=("avg_mpg", "mean"), count=("make", "size"))
        .sort_values("avg_price", ascending=False)
    )
    brand_metric_fig = make_subplots(specs=[[{"secondary_y": True}]])
    brand_metric_fig.add_trace(
        go.Bar(
            x=brand_metrics["make"],
            y=brand_metrics["avg_price"],
            name="Avg Price",
            marker_color="#1f77b4",
            hovertemplate="브랜드=%{x}<br>평균 가격=%{y:.0f}<extra></extra>",
        ),
        secondary_y=False,
    )
    brand_metric_fig.add_trace(
        go.Scatter(
            x=brand_metrics["make"],
            y=brand_metrics["avg_hp"],
            name="Avg Horsepower",
            mode="lines+markers",
            marker=dict(size=10, color="#d62728"),
            hovertemplate="브랜드=%{x}<br>평균 마력=%{y:.1f}<extra></extra>",
        ),
        secondary_y=True,
    )
    brand_metric_fig.add_trace(
        go.Scatter(
            x=brand_metrics["make"],
            y=brand_metrics["avg_mpg"],
            name="Avg MPG",
            mode="lines+markers",
            line=dict(color="#2ca02c", dash="dot"),
            hovertemplate="브랜드=%{x}<br>평균 연비=%{y:.1f}<extra></extra>",
        ),
        secondary_y=True,
    )
    brand_metric_fig.update_xaxes(title_text="Brand")
    brand_metric_fig.update_yaxes(title_text="Average Price", secondary_y=False)
    brand_metric_fig.update_yaxes(title_text="Average Horsepower / MPG", secondary_y=True)
    figures["brand_metrics"] = save_figure(
        apply_layout(brand_metric_fig, "주요 브랜드별 가격·마력·연비 비교", 560),
        "brand_metrics",
    )

    body_drive = (
        df.groupby(["body-style", "drive-wheels"], as_index=False)
        .agg(avg_price=("price", "mean"), avg_mpg=("avg_mpg", "mean"))
    )
    body_drive_fig = px.bar(
        body_drive,
        x="body-style",
        y="avg_price",
        color="drive-wheels",
        barmode="group",
        facet_row=None,
        hover_data=["avg_mpg"],
        title="차체 유형과 구동 방식별 평균 가격",
    )
    body_drive_fig.update_layout(xaxis_title="Body Style", yaxis_title="Average Price")
    figures["body_drive_price"] = save_figure(
        apply_layout(body_drive_fig, "차체 유형과 구동 방식별 평균 가격", 560),
        "body_drive_price",
    )

    corr_matrix = df[
        ["price", "engine-size", "horsepower", "curb-weight", "avg_mpg", "city-mpg", "highway-mpg", "width", "length", "compression-ratio", "power_density", "price_per_hp"]
    ].corr(numeric_only=True)
    corr_heatmap = go.Figure(
        data=[
            go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale="RdBu",
                zmid=0,
                hovertemplate="X=%{x}<br>Y=%{y}<br>상관계수=%{z:.2f}<extra></extra>",
            )
        ]
    )
    figures["correlation_heatmap"] = save_figure(
        apply_layout(corr_heatmap, "수치형 변수 상관관계 구조", 620),
        "correlation_heatmap",
    )

    decile = (
        df.groupby("price_decile_label", as_index=False)
        .agg(avg_price=("price", "mean"), avg_hp=("horsepower", "mean"), avg_mpg=("avg_mpg", "mean"), avg_engine=("engine-size", "mean"))
        .sort_values("avg_price")
    )
    line_fig = make_subplots(specs=[[{"secondary_y": True}]])
    line_fig.add_trace(
        go.Scatter(
            x=decile["price_decile_label"],
            y=decile["avg_hp"],
            mode="lines+markers",
            name="Avg Horsepower",
            line=dict(color="#d62728", width=3),
        ),
        secondary_y=False,
    )
    line_fig.add_trace(
        go.Scatter(
            x=decile["price_decile_label"],
            y=decile["avg_engine"],
            mode="lines+markers",
            name="Avg Engine Size",
            line=dict(color="#1f77b4", width=3, dash="dash"),
        ),
        secondary_y=False,
    )
    line_fig.add_trace(
        go.Scatter(
            x=decile["price_decile_label"],
            y=decile["avg_mpg"],
            mode="lines+markers",
            name="Avg MPG",
            line=dict(color="#2ca02c", width=3),
        ),
        secondary_y=True,
    )
    line_fig.update_xaxes(title_text="Price Decile")
    line_fig.update_yaxes(title_text="Horsepower / Engine Size", secondary_y=False)
    line_fig.update_yaxes(title_text="Average MPG", secondary_y=True)
    figures["price_decile_line"] = save_figure(
        apply_layout(line_fig, "가격 구간별 성능·엔진·연비 변화", 560),
        "price_decile_line",
    )

    segment_summary = (
        df.groupby("segment", as_index=False)
        .agg(
            vehicles=("segment", "size"),
            avg_price=("price", "mean"),
            avg_hp=("horsepower", "mean"),
            avg_mpg=("avg_mpg", "mean"),
            lead_brands=("make", lambda s: ", ".join(s.value_counts().head(3).index)),
        )
    )
    segment_summary["segment"] = pd.Categorical(segment_summary["segment"], SEGMENT_ORDER, ordered=True)
    segment_summary = segment_summary.sort_values("segment")
    segment_fig = px.scatter(
        df,
        x="avg_mpg",
        y="horsepower",
        size="price",
        color="segment",
        hover_data=["make", "body-style", "drive-wheels", "price"],
        symbol="fuel-type",
        category_orders={"segment": SEGMENT_ORDER},
        title="세그먼트별 차량 포지셔닝 맵",
    )
    segment_fig.update_layout(xaxis_title="Average MPG", yaxis_title="Horsepower")
    figures["segment_map"] = save_figure(apply_layout(segment_fig, "세그먼트별 차량 포지셔닝 맵", 560), "segment_map")

    value_map = px.scatter(
        df,
        x="hp_per_1000usd",
        y="avg_mpg",
        color="segment",
        size="price",
        symbol="drive-wheels",
        hover_data=["make", "body-style", "horsepower", "price"],
        category_orders={"segment": SEGMENT_ORDER},
        title="가성비와 연비의 동시 비교 맵",
    )
    value_map.update_layout(xaxis_title="Horsepower per $1,000", yaxis_title="Average MPG")
    figures["value_efficiency_map"] = save_figure(
        apply_layout(value_map, "가성비와 연비의 동시 비교 맵", 560),
        "value_efficiency_map",
    )

    segment_table_fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=["Segment", "Vehicles", "Avg Price", "Avg HP", "Avg MPG", "Representative Brands"],
                    fill_color="#274690",
                    font=dict(color="white"),
                ),
                cells=dict(
                    values=[
                        segment_summary["segment"],
                        segment_summary["vehicles"],
                        segment_summary["avg_price"].round(0),
                        segment_summary["avg_hp"].round(1),
                        segment_summary["avg_mpg"].round(1),
                        segment_summary["lead_brands"],
                    ],
                    fill_color="#eef3fb",
                ),
            )
        ]
    )
    figures["segment_table"] = save_figure(apply_layout(segment_table_fig, "세그먼트 요약표", 420), "segment_table")

    context = {
        "key_summary": key_summary,
        "brand_counts": brand_counts,
        "brand_metrics": brand_metrics,
        "segment_summary": segment_summary,
        "correlation_price": correlation_table(df),
        "top_price_drivers": correlation_table(df)
        .query("variable != 'price'")
        .assign(abs_corr=lambda x: x["correlation"].abs())
        .sort_values("abs_corr", ascending=False)
        .head(5),
    }
    return figures, context


def fig_block(figures: dict, key: str, heading: str, interpretation: str, decision_note: str) -> str:
    html = figures[key]["html"].resolve().as_posix()
    return dedent(
        f"""
        ### {heading}
        [인터랙티브 보기]({html})

        {interpretation}

        판단 포인트: {decision_note}
        """
    ).strip()


def dataframe_to_markdown(df: pd.DataFrame, index: bool = False) -> str:
    return df.to_markdown(index=index)


def build_markdown_report(df: pd.DataFrame, cleaning_summary: dict, figures: dict, context: dict) -> str:
    missing_df = (
        pd.DataFrame(
            {
                "column": list(cleaning_summary["missing_before"].keys()),
                "missing_before": list(cleaning_summary["missing_before"].values()),
                "missing_after": [cleaning_summary["missing_after"][key] for key in cleaning_summary["missing_before"].keys()],
            }
        )
        .query("missing_before > 0")
        .sort_values("missing_before", ascending=False)
    )
    variable_df = pd.DataFrame(
        [
            ("price", "numeric", "차량 가격"),
            ("engine-size", "numeric", "엔진 배기량 크기"),
            ("horsepower", "numeric", "엔진 출력"),
            ("curb-weight", "numeric", "차량 공차중량"),
            ("city-mpg / highway-mpg", "numeric", "도심/고속 연비"),
            ("avg_mpg", "derived", "평균 연비"),
            ("footprint", "derived", "길이*너비 기반 차체 면적 지표"),
            ("price_per_hp", "derived", "마력당 가격"),
            ("make", "categorical", "브랜드"),
            ("body-style", "categorical", "차체 유형"),
            ("drive-wheels", "categorical", "구동 방식"),
            ("fuel-type", "categorical", "연료 방식"),
            ("segment", "derived", "가격·마력·연비 기반 세그먼트"),
        ],
        columns=["variable", "type", "meaning"],
    )

    top_drivers = context["top_price_drivers"].copy()
    top_drivers["correlation"] = top_drivers["correlation"].round(4)
    top_drivers = top_drivers[["variable", "correlation"]]

    executive_points = [
        "가격은 `engine-size`, `curb-weight`, `horsepower`와 강한 양의 상관을 보인다. 이 데이터셋에서 가격은 사실상 성능·차체 규모 패키지의 결과다.",
        "연비는 가격과 반대로 움직인다. 특히 `avg_mpg`가 높은 차량일수록 저가·실속형으로 몰리고, 고가 차량은 평균적으로 연비가 낮다.",
        "`hardtop`, `convertible`, `rwd` 조합은 평균 가격과 출력이 높고, `hatchback`, `fwd` 조합은 실속형 포지션에 가깝다.",
        "브랜드별로는 Jaguar, Mercedes-Benz, Porsche, BMW가 고가·고성능 축에 집중되고, Toyota·Honda·Nissan은 상대적으로 대중형 구간에 넓게 분포한다.",
        "세그먼트 관점에서 `Premium Performance`, `Balanced Core`, `Value Efficiency`, `Budget Practical` 네 그룹으로 나누면 상품 포트폴리오와 가격 전략을 훨씬 명확하게 설명할 수 있다.",
    ]

    report = f"""# 자동차 모델 가격·성능·연비 관계 인터랙티브 보고서

[전체 인터랙티브 대시보드]({OUT_HTML.resolve().as_posix()})

## 1부. 데이터 개요

- 원본 파일: [imports-85.csv]({RAW_CSV.resolve().as_posix()})
- 정제 기준: 설명행/메타행 2건 제거 후 분석용 205건 사용
- 이상치 검토 반영: 이상치 후보를 재검토한 결과 모두 정상값으로 판단하여 제거 없이 전건 유지
- 재분석 기준 파일: [imports-85_reintegrated_analysis_base.csv]({OUT_CSV.resolve().as_posix()})
- 변수 수: 정제 후 {df.shape[1]}개
- 처리 원칙:
  - 수치형 결측치: 그룹 중앙값 우선, 부족 시 전체 중앙값
  - 범주형 결측치: 그룹 최빈값 우선, 부족 시 전체 최빈값
  - 컬럼명 공백 제거, 숫자형 문자열을 숫자로 변환, 파생변수 생성
  - 이상치: 제거하지 않고 `reviewed_valid_retained` 상태로 유지

### 데이터 현황 요약
{fig_block(figures, "overview_table", "핵심 데이터 요약표", "보고서 출발점에서 표본 규모, 브랜드 수, 차체 유형 수, 중앙값 수준을 한 번에 확인할 수 있다. 경영진은 데이터의 해석 범위와 표본 구조를 먼저 이해해야 이후 차트의 의미를 정확히 읽을 수 있다.", "샘플 구성이 특정 브랜드나 차체에 치우쳤는지, 그리고 가격·출력의 중앙값 수준이 어느 정도인지 빠르게 파악할 수 있다.")}

### 결측 현황
{dataframe_to_markdown(missing_df, index=False)}

### 변수 설명
{dataframe_to_markdown(variable_df, index=False)}

## 2부. 핵심 인사이트 5가지

"""
    for point in executive_points:
        report += f"- {point}\n"

    report += f"""

가격 관련 주요 변수 TOP 5:

{dataframe_to_markdown(top_drivers, index=False)}

세그먼트 차별화 요약:
- `Premium Performance`: 고가·고마력 차량군. 브랜드 프리미엄과 성능 패키지가 가격을 견인한다.
- `Balanced Core`: 중간 가격대의 핵심 볼륨 구간. 성능과 연비의 균형이 상대적으로 좋다.
- `Value Efficiency`: 낮은 가격과 높은 연비 조합. 유지비 관점에서 설득력이 높다.
- `Budget Practical`: 저가 실속형이지만 상품성은 제한적일 수 있어, 옵션 전략과 트림 차별화가 중요하다.

## 3부. 차트별 분석 결과

### A. 데이터 구조와 기본 분포
{fig_block(figures, "brand_counts", "브랜드별 표본 수 Top 12", "Toyota, Nissan, Mazda가 가장 많은 표본을 차지한다. 따라서 전체 평균을 해석할 때는 이들 대중 브랜드의 영향력이 크고, 소수 프리미엄 브랜드는 평균값보다 분포의 상단을 넓히는 역할을 한다.", "표본이 많은 브랜드는 시장의 기준선 역할을 하고, 표본이 적은 프리미엄 브랜드는 평균 가격을 끌어올리는 특수 세그먼트인지 판단할 수 있다.")}

{fig_block(figures, "fuel_share", "연료 방식 비중", "가솔린 차량 비중이 압도적으로 높고 디젤은 제한적이다. 따라서 연비와 압축비 해석에서 디젤 차량은 별도 포지션으로 보는 것이 합리적이다.", "연료 방식별 정책이나 포트폴리오 논의를 할 때, 전체 평균보다 표본 구성을 먼저 확인할 수 있다.")}

{fig_block(figures, "distribution_panel", "핵심 수치형 변수 분포", "가격, 엔진 크기, 마력은 우측 꼬리가 긴 분포를 보여 일부 고가·고성능 차량이 상단을 끌어올린다. 반면 평균 연비는 상대적으로 좁은 구간에 몰려 있어, 연비 경쟁은 제한된 범위 안에서 벌어진다.", "고가 구간이 소수 차량에 집중되는지, 엔진과 마력이 몇 개의 군집으로 나뉘는지, 연비 개선 여지가 큰지 판단할 수 있다.")}

### B. 가격 결정 요인 분석
{fig_block(figures, "scatter_engine_price", "엔진 크기와 가격의 관계", "엔진 크기가 커질수록 가격이 상승하는 명확한 우상향 추세가 보인다. 같은 엔진 크기에서도 차체 유형과 연료 방식에 따라 가격 차이가 벌어지는 점은, 단순 배기량 외에 브랜드와 차체 포지셔닝이 프리미엄을 만든다는 뜻이다.", "대배기량 전략이 실제로 가격 프리미엄으로 연결되는지, 그리고 어떤 차체 유형이 같은 엔진 크기 대비 더 높은 가격을 받는지 확인할 수 있다.")}

{fig_block(figures, "scatter_hp_price", "마력과 가격의 관계", "마력 또한 가격과 강하게 연결되지만, 일부 브랜드는 같은 출력 대비 더 높은 가격을 받는다. 이는 브랜드 프리미엄 또는 고급 사양 패키지 영향으로 해석할 수 있다.", "출력 상승이 가격 인상 논리를 충분히 뒷받침하는지, 혹은 브랜드 파워가 더 큰지 구분할 수 있다.")}

{fig_block(figures, "scatter_weight_price", "차량 중량과 가격의 관계", "중량이 높은 차량일수록 가격도 높아지는 경향이 강하다. 실제로는 차체 크기, 안전/편의사양, 엔진 구성이 함께 묶여 있는 결과로 보는 것이 적절하다.", "고급화 전략이 차체·사양 확대와 함께 가는지, 혹은 지나친 중량 증가가 가격 대비 효율을 해치는지 판단할 수 있다.")}

{fig_block(figures, "scatter_mpg_price", "평균 연비와 가격의 관계", "평균 연비가 높을수록 가격은 낮아지는 역관계가 보인다. 즉 이 데이터에서는 성능과 가격을 올릴수록 연비 손실을 감수하는 구조가 강하며, 고연비 차량은 실속형 세그먼트에 집중된다.", "고연비 전략이 프리미엄과 양립하는지, 아니면 별도 실속형 포트폴리오로 운영해야 하는지 판단할 수 있다.")}

### C. 비교 분석
{fig_block(figures, "brand_metrics", "주요 브랜드별 가격·마력·연비 비교", "Jaguar, Mercedes-Benz, Porsche, BMW는 평균 가격과 출력이 높고, 연비는 상대적으로 낮다. 반대로 Toyota, Honda, Nissan은 상대적으로 낮은 가격과 중간 수준의 마력, 더 나은 연비로 대중형 포지션을 형성한다.", "브랜드 포트폴리오를 프리미엄 중심으로 볼지, 볼륨 중심으로 볼지, 혹은 양쪽을 분리 운영할지 결정하는 데 도움을 준다.")}

{fig_block(figures, "body_drive_price", "차체 유형과 구동 방식별 평균 가격", "`rwd`는 대체로 높은 가격과 연결되고, `fwd`는 대중형 세그먼트에 집중된다. `hardtop`과 `convertible`은 차체 유형 자체가 프리미엄 가격대를 형성하는 반면, `hatchback`은 실속형에 가깝다.", "차체와 구동 방식을 어떤 조합으로 가져갈 때 프리미엄 가격을 만들 수 있는지 판단할 수 있다.")}

### D. 관계 구조와 세그먼트
{fig_block(figures, "correlation_heatmap", "수치형 변수 상관관계 구조", "가격은 엔진 크기, 중량, 마력과 같은 방향으로 움직이고, 연비와는 반대 방향으로 움직인다. 상관관계가 매우 높은 변수들이 함께 존재하므로, 실제 가격 정책에서는 단일 스펙보다 패키지 조합으로 접근해야 한다.", "어떤 변수를 묶어서 상품기획 패키지를 설계해야 하는지, 서로 대체 가능한 설명 변수가 무엇인지 판단할 수 있다.")}

{fig_block(figures, "price_decile_line", "가격 구간별 성능·엔진·연비 변화", "가격 구간이 올라갈수록 평균 마력과 엔진 크기는 상승하고 평균 연비는 하락한다. 특히 상위 가격 구간에서 성능 지표가 가파르게 상승해, 고가 구간은 단순 가격 인상이 아니라 명확한 성능 차별화로 설명된다.", "가격대별로 어떤 사양을 더해야 소비자가 가격 차이를 납득하는지 판단할 수 있다.")}

{fig_block(figures, "segment_map", "세그먼트별 차량 포지셔닝 맵", "차량군은 대략 네 개 세그먼트로 구분된다. 고가·고성능군은 연비가 낮고, 실속형은 높은 연비와 낮은 가격에 집중되며, 중간 다수는 균형형 구간에 모여 있다.", "포트폴리오 공백이 어디인지, 프리미엄 강화가 필요한지, 혹은 실속형 보강이 필요한지 판단할 수 있다.")}

{fig_block(figures, "value_efficiency_map", "가성비와 연비의 동시 비교 맵", "마력당 가격 효율과 평균 연비를 함께 보면 단순 저가 차량과 진짜 가성비 차량을 구분할 수 있다. 일부 중간 가격대 차량은 연비와 성능 효율을 동시에 확보해 균형형 포지션의 핵심 후보로 읽힌다.", "고성능을 유지하면서도 가격 효율이 높은 조합이 있는지, 또는 연비 중심 상품이 실제로도 가성비 우위를 갖는지 판단할 수 있다.")}

{fig_block(figures, "segment_table", "세그먼트 요약표", "세그먼트별 차량 수, 평균 가격, 평균 마력, 평균 연비, 대표 브랜드를 함께 보면 포트폴리오 구조가 명확해진다. 경영진은 이 표만 봐도 어느 세그먼트가 수익성 중심인지, 어느 세그먼트가 볼륨 중심인지 빠르게 파악할 수 있다.", "브랜드별 역할을 세그먼트 관점에서 재정의하고, 상품기획·마케팅·영업 전략을 분리 설계할 수 있다.")}

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
{dataframe_to_markdown(context["correlation_price"].assign(correlation=lambda x: x["correlation"].round(4)), index=False)}

### 세그먼트 요약표
{dataframe_to_markdown(context["segment_summary"].assign(avg_price=lambda x: x["avg_price"].round(0), avg_hp=lambda x: x["avg_hp"].round(1), avg_mpg=lambda x: x["avg_mpg"].round(1)), index=False)}

### Python 코드 실행 안내
- 전체 스크립트: [imports85_plotly_report.py]({(ROOT / "imports85_plotly_report.py").resolve().as_posix()})
- 실행 환경: [`.venv-report`]({(Path.cwd() / ".venv-report").resolve().as_posix()})
- 실행 명령:

```powershell
.\\.venv-report\\Scripts\\python .\\실습결과물\\16\\imports85_plotly_report.py
```

### 코드 예시
```python
import pandas as pd
import plotly.express as px

df = pd.read_csv("imports-85.csv", dtype=str)
df.columns = [c.strip() for c in df.columns]
df = df[~df["price"].isin(["continuous", "class"])].replace({{"?": pd.NA, "": pd.NA}})
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
"""
    return report


def build_dashboard_html(figures: dict) -> str:
    sections = [
        ("데이터 개요", ["overview_table", "brand_counts", "fuel_share", "distribution_panel"]),
        ("가격 결정 요인", ["scatter_engine_price", "scatter_hp_price", "scatter_weight_price", "scatter_mpg_price"]),
        ("비교 분석", ["brand_metrics", "body_drive_price"]),
        ("관계 구조와 세그먼트", ["correlation_heatmap", "price_decile_line", "segment_map", "value_efficiency_map", "segment_table"]),
    ]
    html_parts = [
        "<html><head><meta charset='utf-8'><title>imports-85 Interactive Dashboard</title><script src='https://cdn.plot.ly/plotly-2.35.2.min.js'></script></head><body style='font-family: Arial; margin: 24px;'>",
        "<h1>imports-85 Interactive Dashboard</h1>",
        "<p>자동차 모델 가격, 성능, 연비, 차체 특성 간 관계를 보여주는 Plotly 기반 대시보드</p>",
    ]
    for title, keys in sections:
        html_parts.append(f"<h2>{title}</h2>")
        for key in keys:
            fig_html = figures[key]["fig"].to_html(include_plotlyjs=False, full_html=False)
            html_parts.append(fig_html)
    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def main():
    df, cleaning_summary = load_and_clean_data(RAW_CSV)
    print("Loaded and cleaned data")
    df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Wrote analysis base: {OUT_CSV}")
    figures, context = build_figures(df, cleaning_summary)
    print("Built figures")
    markdown = build_markdown_report(df, cleaning_summary, figures, context)
    OUT_MD.write_text(markdown, encoding="utf-8")
    OUT_HTML.write_text(build_dashboard_html(figures), encoding="utf-8")
    print(f"Markdown report: {OUT_MD}")
    print(f"Interactive dashboard: {OUT_HTML}")


if __name__ == "__main__":
    main()
