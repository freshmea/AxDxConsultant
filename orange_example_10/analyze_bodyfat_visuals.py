from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def load_bodyfat(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Remove metadata rows and keep only numeric observations.
    df = df[~df['body fat brozek'].isin(['continuous', 'class'])].copy()

    numeric_cols = [
        'body fat brozek', 'age', 'weight', 'height', 'adiposity', 'neck',
        'chest', 'abdomen', 'hip', 'tight', 'knee', 'ankle', 'biceps',
        'forearm', 'wrist'
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Keep id as string for traceability, but remove unusable rows.
    df = df.dropna(subset=numeric_cols).reset_index(drop=True)

    # Intuitive category for violin/box grouped analysis.
    df['body_fat_group'] = pd.qcut(
        df['body fat brozek'],
        q=4,
        labels=['Q1 Low', 'Q2 Mid-Low', 'Q3 Mid-High', 'Q4 High']
    )

    return df


def save_fig(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches='tight')
    plt.close()


def generate_plots(df: pd.DataFrame, out_dir: Path) -> dict:
    sns.set_theme(style='whitegrid')

    target = 'body fat brozek'
    features = [
        'age', 'weight', 'height', 'adiposity', 'neck', 'chest', 'abdomen',
        'hip', 'tight', 'knee', 'ankle', 'biceps', 'forearm', 'wrist'
    ]
    numeric_cols = [target] + features

    plot_paths = {
        'overview': [],
        'distribution': [],
        'boxplot': [],
        'violin': [],
        'scatter': [],
        'correlation': []
    }

    # 1) Overview plots
    plt.figure(figsize=(9, 6))
    sns.histplot(df[target], kde=True, bins=25, color='#2E86AB')
    plt.title('Body Fat Brozek Distribution')
    plt.xlabel('Body Fat Brozek')
    p = out_dir / 'overview' / 'bodyfat_distribution.png'
    save_fig(p)
    plot_paths['overview'].append(p)

    plt.figure(figsize=(8, 5))
    sns.countplot(data=df, x='body_fat_group', palette='viridis')
    plt.title('Body Fat Group Counts (Quartiles)')
    plt.xlabel('Body Fat Group')
    p = out_dir / 'overview' / 'bodyfat_group_counts.png'
    save_fig(p)
    plot_paths['overview'].append(p)

    # 2) Distribution plots for all numeric columns
    for col in numeric_cols:
        plt.figure(figsize=(9, 6))
        sns.histplot(df[col], kde=True, bins=24, color='#247BA0')
        plt.title(f'Distribution: {col}')
        plt.xlabel(col)
        p = out_dir / 'distribution' / f'hist_{col.replace(" ", "_")}.png'
        save_fig(p)
        plot_paths['distribution'].append(p)

    # 3) Box plots
    for col in numeric_cols:
        plt.figure(figsize=(9, 6))
        sns.boxplot(y=df[col], color='#F4A261')
        plt.title(f'Box Plot: {col}')
        p = out_dir / 'boxplot' / f'box_{col.replace(" ", "_")}.png'
        save_fig(p)
        plot_paths['boxplot'].append(p)

    # Grouped box plots by body fat quartile
    for col in features:
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=df, x='body_fat_group', y=col, palette='Set2')
        plt.title(f'Box Plot by Body Fat Group: {col}')
        p = out_dir / 'boxplot' / f'box_group_{col.replace(" ", "_")}.png'
        save_fig(p)
        plot_paths['boxplot'].append(p)

    # 4) Violin plots grouped by body fat quartile
    for col in features:
        plt.figure(figsize=(10, 6))
        sns.violinplot(data=df, x='body_fat_group', y=col, palette='coolwarm', inner='quartile')
        plt.title(f'Violin Plot by Body Fat Group: {col}')
        p = out_dir / 'violin' / f'violin_group_{col.replace(" ", "_")}.png'
        save_fig(p)
        plot_paths['violin'].append(p)

    # 5) Scatter plots with regression line against target
    for col in features:
        plt.figure(figsize=(9, 6))
        sns.regplot(data=df, x=col, y=target, scatter_kws={'alpha': 0.7, 's': 30}, line_kws={'color': 'red'})
        plt.title(f'Scatter + Trend: {col} vs {target}')
        p = out_dir / 'scatter' / f'scatter_{col.replace(" ", "_")}_vs_bodyfat.png'
        save_fig(p)
        plot_paths['scatter'].append(p)

    # 6) Correlation visualizations
    pearson_corr = df[numeric_cols].corr(method='pearson')
    spearman_corr = df[numeric_cols].corr(method='spearman')

    plt.figure(figsize=(13, 10))
    sns.heatmap(pearson_corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0)
    plt.title('Pearson Correlation Heatmap')
    p = out_dir / 'correlation' / 'correlation_heatmap_pearson.png'
    save_fig(p)
    plot_paths['correlation'].append(p)

    plt.figure(figsize=(13, 10))
    sns.heatmap(spearman_corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
    plt.title('Spearman Correlation Heatmap')
    p = out_dir / 'correlation' / 'correlation_heatmap_spearman.png'
    save_fig(p)
    plot_paths['correlation'].append(p)

    # Pairplot for top correlated features with target
    corr_with_target = pearson_corr[target].drop(target).abs().sort_values(ascending=False)
    top5 = corr_with_target.head(5).index.tolist()
    pair_cols = [target] + top5

    pairplot = sns.pairplot(df[pair_cols], corner=True, diag_kind='hist')
    pairplot.fig.suptitle('Pair Plot: Target + Top5 Correlated Features', y=1.02)
    p = out_dir / 'correlation' / 'pairplot_top5.png'
    pairplot.savefig(p, dpi=180, bbox_inches='tight')
    plt.close('all')
    plot_paths['correlation'].append(p)

    return plot_paths


def build_report(df: pd.DataFrame, plot_paths: dict, report_path: Path) -> None:
    target = 'body fat brozek'
    numeric_cols = [
        'body fat brozek', 'age', 'weight', 'height', 'adiposity', 'neck',
        'chest', 'abdomen', 'hip', 'tight', 'knee', 'ankle', 'biceps',
        'forearm', 'wrist'
    ]

    desc = df[numeric_cols].describe().T
    q1 = df[numeric_cols].quantile(0.25)
    q3 = df[numeric_cols].quantile(0.75)
    iqr = q3 - q1
    outlier_counts = ((df[numeric_cols] < (q1 - 1.5 * iqr)) | (df[numeric_cols] > (q3 + 1.5 * iqr))).sum().sort_values(ascending=False)

    corr = df[numeric_cols].corr(method='pearson')[target].drop(target).sort_values(ascending=False)
    top_pos = corr.head(5)
    top_neg = corr.tail(5)

    def md_image_list(paths):
        lines = []
        for p in paths:
            lines.append(f'- [{p.name}]({p.as_posix()})')
        return '\n'.join(lines)

    with report_path.open('w', encoding='utf-8') as f:
        f.write('# Body Fat Brozek 데이터 시각 분석 보고서\n\n')
        f.write('## 1. 데이터 개요\n')
        f.write(f'- 원본 파일: `{report_path.parent / "body-fat-brozek.csv"}`\n')
        f.write(f'- 정제 후 데이터 크기: **{df.shape[0]}행 x {df.shape[1]}열**\n')
        f.write('- 타겟 관점 변수: `body fat brozek`\n')
        f.write('- 수치형 변수 전부를 대상으로 분포/이상치/상관/산점도 분석 수행\n\n')

        f.write('## 2. 기술 통계 요약\n\n')
        f.write(desc.to_markdown())
        f.write('\n\n')

        f.write('## 3. 직관적 해석\n')
        f.write('- `abdomen`, `chest`, `hip`, `adiposity`, `weight`는 체지방과 같은 방향(양의 상관)으로 움직이는 경향이 큽니다.\n')
        f.write('- `height`는 체지방과 반대 방향(음의 상관) 경향을 보이며, 키가 클수록 같은 조건에서 체지방률이 상대적으로 낮아지는 패턴이 일부 보입니다.\n')
        f.write('- Box/Violin plot에서 체지방 상위 사분위(Q4)로 갈수록 복부(`abdomen`)와 가슴(`chest`) 분포의 중심값이 뚜렷하게 증가합니다.\n')
        f.write('- 일부 변수는 IQR 기준 이상치가 관찰되며, 특히 체중/복부/가슴 둘레에서 꼬리가 두껍게 나타납니다.\n')
        f.write('- 산점도 회귀선 기준으로 복부 둘레(`abdomen`)는 체지방률 설명력이 매우 직관적으로 높은 변수입니다.\n\n')

        f.write('## 4. 체지방과의 상관관계 (Pearson)\n\n')
        f.write('### 4.1 상위 양의 상관 5개\n\n')
        f.write(top_pos.to_frame('pearson_corr').to_markdown())
        f.write('\n\n### 4.2 하위(음의 방향 포함) 5개\n\n')
        f.write(top_neg.to_frame('pearson_corr').to_markdown())
        f.write('\n\n')

        f.write('## 5. IQR 기준 이상치 개수\n\n')
        f.write(outlier_counts.to_frame('outlier_count').to_markdown())
        f.write('\n\n')

        f.write('## 6. 그래프 링크 모음\n\n')
        for section in ['overview', 'distribution', 'boxplot', 'violin', 'scatter', 'correlation']:
            title = section.capitalize()
            f.write(f'### {title}\n')
            f.write(md_image_list(plot_paths[section]))
            f.write('\n\n')

        f.write('## 7. 대표 그래프 미리보기\n\n')
        # Representative embedded images
        reps = [
            plot_paths['overview'][0],
            plot_paths['scatter'][0],
            plot_paths['scatter'][6] if len(plot_paths['scatter']) > 6 else plot_paths['scatter'][-1],
            plot_paths['correlation'][0],
            plot_paths['correlation'][1],
            plot_paths['correlation'][2],
        ]
        for rp in reps:
            f.write(f'![{rp.name}]({rp.as_posix()})\n\n')


def main() -> None:
    base_dir = Path(r'C:\Users\Administrator\dxAx\orange_example')
    csv_path = base_dir / 'body-fat-brozek.csv'
    out_dir = base_dir / 'bodyfat_analysis_plots'
    report_path = base_dir / 'bodyfat_analysis_report.md'

    df = load_bodyfat(csv_path)
    plot_paths = generate_plots(df, out_dir)
    build_report(df, plot_paths, report_path)

    total_plots = sum(len(v) for v in plot_paths.values())
    print('Analysis completed.')
    print(f'Rows after cleaning: {len(df)}')
    print(f'Generated plots: {total_plots}')
    print(f'Plot directory: {out_dir}')
    print(f'Report: {report_path}')


if __name__ == '__main__':
    main()
