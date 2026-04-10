from pathlib import Path
import pandas as pd


def load_df(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[~df['body fat brozek'].isin(['continuous', 'class'])].copy()
    cols = [
        'body fat brozek', 'age', 'weight', 'height', 'adiposity', 'neck',
        'chest', 'abdomen', 'hip', 'tight', 'knee', 'ankle', 'biceps',
        'forearm', 'wrist'
    ]
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.dropna(subset=cols).reset_index(drop=True)
    df['body_fat_group'] = pd.qcut(
        df['body fat brozek'],
        q=4,
        labels=['Q1 Low', 'Q2 Mid-Low', 'Q3 Mid-High', 'Q4 High']
    )
    return df


def p(path: Path) -> str:
    return path.as_posix()


def main() -> None:
    base = Path(r'C:\Users\Administrator\dxAx\orange_example')
    plots = base / 'bodyfat_analysis_plots'
    report = base / 'bodyfat_analysis_report.md'
    csv_path = base / 'body-fat-brozek.csv'

    df = load_df(csv_path)
    target = 'body fat brozek'
    features = [
        'age', 'weight', 'height', 'adiposity', 'neck', 'chest', 'abdomen',
        'hip', 'tight', 'knee', 'ankle', 'biceps', 'forearm', 'wrist'
    ]

    corr = df[[target] + features].corr(method='pearson')[target].drop(target).sort_values(ascending=False)
    top_pos = corr.head(6)
    top_mid = corr.iloc[6:10]
    top_neg = corr.tail(4)

    overview_dist = plots / 'overview' / 'bodyfat_distribution.png'
    overview_group = plots / 'overview' / 'bodyfat_group_counts.png'
    corr_pearson = plots / 'correlation' / 'correlation_heatmap_pearson.png'
    corr_spearman = plots / 'correlation' / 'correlation_heatmap_spearman.png'
    pairplot = plots / 'correlation' / 'pairplot_top5.png'

    def scatter_img(feat: str) -> Path:
        return plots / 'scatter' / f'scatter_{feat}_vs_bodyfat.png'

    def box_group_img(feat: str) -> Path:
        return plots / 'boxplot' / f'box_group_{feat}.png'

    def violin_group_img(feat: str) -> Path:
        return plots / 'violin' / f'violin_group_{feat}.png'

    with report.open('w', encoding='utf-8') as f:
        f.write('# Body Fat Brozek 시각 분석 보고서 (미리보기 중심)\n\n')
        f.write('## 1) 데이터 개요\n')
        f.write(f'- 데이터 행 수: **{len(df)}**\n')
        f.write('- 타겟 변수: `body fat brozek`\n')
        f.write('- 분석 목표: 분포, 이상치, 상관관계, 변수별 패턴을 직관적으로 확인\n\n')

        f.write('초기 분포를 보면 체지방 수치가 단봉형 분포를 가지며, 사분위 그룹은 거의 균등하게 나뉩니다.\n\n')
        f.write(f'![body fat distribution]({p(overview_dist)})\n\n')
        f.write(f'![body fat group counts]({p(overview_group)})\n\n')

        f.write('## 2) 상관관계 중심 해석\n')
        f.write('Pearson/Spearman 히트맵에서 체지방과 함께 움직이는 핵심 변수는 `abdomen`, `adiposity`, `chest`, `hip`, `weight`입니다.\n\n')
        f.write(f'![pearson heatmap]({p(corr_pearson)})\n\n')
        f.write(f'![spearman heatmap]({p(corr_spearman)})\n\n')
        f.write(f'![pairplot top correlated]({p(pairplot)})\n\n')

        f.write('### 체지방과의 Pearson 상관 순위\n\n')
        f.write('상위 양의 상관:\n\n')
        f.write(top_pos.to_frame('pearson_corr').to_markdown())
        f.write('\n\n중간 상관:\n\n')
        f.write(top_mid.to_frame('pearson_corr').to_markdown())
        f.write('\n\n하위(음의 방향 포함):\n\n')
        f.write(top_neg.to_frame('pearson_corr').to_markdown())
        f.write('\n\n')

        f.write('## 3) 핵심 변수별 산점도 + 추세선\n')
        f.write('체지방과의 관계를 직접 보는 섹션입니다. 복부(`abdomen`)는 가장 강한 양의 추세를 보이며, 키(`height`)는 약한 음의 경향을 보입니다.\n\n')

        for feat in ['abdomen', 'adiposity', 'chest', 'hip', 'weight', 'height', 'age', 'wrist']:
            f.write(f'### {feat} vs body fat\n')
            f.write(f'![scatter {feat}]({p(scatter_img(feat))})\n\n')

        f.write('## 4) Box Plot 해석 (체지방 그룹별 분포)\n')
        f.write('Q1에서 Q4로 갈수록 다수 변수의 중앙값이 상승합니다. 특히 `abdomen`, `chest`, `hip`, `weight`에서 그룹 간 분리가 명확합니다.\n\n')

        for feat in ['abdomen', 'chest', 'hip', 'weight', 'adiposity', 'tight', 'neck', 'height']:
            f.write(f'### Grouped Box: {feat}\n')
            f.write(f'![box group {feat}]({p(box_group_img(feat))})\n\n')

        f.write('## 5) Violin Plot 해석 (분포 형태 + 밀도)\n')
        f.write('Violin plot으로 보면 그룹별 밀도 구조와 꼬리 길이를 확인할 수 있습니다. 일부 변수는 상위 그룹에서 분산이 커집니다.\n\n')

        for feat in ['abdomen', 'chest', 'hip', 'weight', 'adiposity', 'tight', 'knee', 'ankle', 'biceps', 'forearm', 'wrist']:
            f.write(f'### Grouped Violin: {feat}\n')
            f.write(f'![violin group {feat}]({p(violin_group_img(feat))})\n\n')

        f.write('## 6) 종합 해석\n')
        f.write('- 복부 둘레(`abdomen`)가 체지방과 가장 강하게 연결되어, 실무적으로 가장 직관적인 설명 변수입니다.\n')
        f.write('- `adiposity`, `chest`, `hip`, `weight`도 체지방 증가와 함께 높아지는 경향이 강합니다.\n')
        f.write('- `height`는 상관이 약하고 음의 방향이라, 체지방 증가를 직접적으로 설명하는 힘은 제한적입니다.\n')
        f.write('- Box/Violin에서 Q4(고체지방) 그룹은 중심값 상승과 함께 분산 확장 경향이 나타납니다.\n')
        f.write('- 결론적으로 체지방 해석은 단일 변수보다 `abdomen + chest + adiposity + weight`의 조합으로 보는 것이 가장 설득력 있습니다.\n')

    print(f'Report rewritten with preview-first layout: {report}')


if __name__ == '__main__':
    main()
