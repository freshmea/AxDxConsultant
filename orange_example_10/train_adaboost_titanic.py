from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier


def load_titanic(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Remove non-data metadata rows.
    df = df[df["survived"].isin(["yes", "no"])].copy()
    df = df[
        df["status"].isin(["first", "second", "third", "crew"])
        & df["age"].isin(["adult", "child"])
        & df["sex"].isin(["male", "female"])
    ].copy()

    return df.reset_index(drop=True)


def expand_by_kfold_10x(df: pd.DataFrame, random_state: int = 42) -> pd.DataFrame:
    """Expand data to 10x using 10-fold split structure."""
    y = (df["survived"] == "yes").astype(int)
    skf = StratifiedKFold(n_splits=10, shuffle=True, random_state=random_state)

    expanded_parts = []
    for fold_id, (train_idx, valid_idx) in enumerate(skf.split(df, y), start=1):
        fold_full = pd.concat([df.iloc[train_idx], df.iloc[valid_idx]], axis=0)
        fold_full = fold_full.sample(frac=1.0, random_state=random_state + fold_id)
        expanded_parts.append(fold_full.reset_index(drop=True))

    expanded_df = pd.concat(expanded_parts, ignore_index=True)
    return expanded_df


def build_adaboost(random_state: int = 42) -> AdaBoostClassifier:
    stump = DecisionTreeClassifier(max_depth=1, random_state=random_state)
    try:
        model = AdaBoostClassifier(
            estimator=stump,
            n_estimators=300,
            learning_rate=0.5,
            random_state=random_state,
        )
    except TypeError:
        # Backward compatibility for older scikit-learn.
        model = AdaBoostClassifier(
            base_estimator=stump,
            n_estimators=300,
            learning_rate=0.5,
            random_state=random_state,
        )
    return model


def interpret_confusion_matrix(tn: int, fp: int, fn: int, tp: int) -> list[str]:
    lines = []
    total = tn + fp + fn + tp
    neg_total = tn + fp
    pos_total = fn + tp

    if total == 0:
        return ["평가 데이터가 없어 해석할 수 없습니다."]

    lines.append(
        f"전체 500개 샘플 중 실제 비생존(no) {neg_total}건, 실제 생존(yes) {pos_total}건입니다."
    )
    lines.append(
        f"모델은 비생존을 {tn}건 맞췄고(FP={fp}), 생존을 {tp}건 맞췄습니다(FN={fn})."
    )

    recall_yes = tp / pos_total if pos_total else 0.0
    recall_no = tn / neg_total if neg_total else 0.0

    if recall_yes < 0.5:
        lines.append(
            "생존(yes) 재현율이 낮아, 실제 생존자를 비생존으로 놓치는 경향이 있습니다."
        )
    else:
        lines.append("생존(yes) 재현율이 비교적 안정적입니다.")

    if recall_no > recall_yes:
        lines.append(
            "비생존(no) 식별 성능이 생존(yes) 식별 성능보다 높아 보수적으로 분류하는 패턴이 나타납니다."
        )
    else:
        lines.append("생존/비생존 클래스 간 식별 성능이 상대적으로 균형적입니다.")

    return lines


def main() -> None:
    base_dir = Path(r"C:\Users\Administrator\dxAx\orange_example")
    csv_path = base_dir / "titanic.csv"
    model_path = base_dir / "titanic_adaboost_model.joblib"
    report_path = base_dir / "titanic_adaboost_report.md"

    df = load_titanic(csv_path)

    # Step 1) 10-fold based 10x expansion.
    expanded_df = expand_by_kfold_10x(df, random_state=42)

    # Step 2) Random sampling with replacement for 80% of expanded data.
    train_size = int(len(expanded_df) * 0.8)
    train_df = expanded_df.sample(n=train_size, replace=True, random_state=42)

    X_train = train_df[["status", "age", "sex"]]
    y_train = (train_df["survived"] == "yes").astype(int)

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                ["status", "age", "sex"],
            )
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", build_adaboost(random_state=42)),
        ]
    )

    pipeline.fit(X_train, y_train)

    # Save trained model.
    joblib.dump(
        {
            "model": pipeline,
            "features": ["status", "age", "sex"],
            "target": "survived",
            "train_rows": len(train_df),
        },
        model_path,
    )

    # Step 3) Re-sample 500 rows for confusion matrix evaluation.
    eval_df = df.sample(n=500, replace=True, random_state=2026)
    X_eval = eval_df[["status", "age", "sex"]]
    y_eval = (eval_df["survived"] == "yes").astype(int)

    y_pred = pipeline.predict(X_eval)

    cm = confusion_matrix(y_eval, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    acc = accuracy_score(y_eval, y_pred)
    precision = precision_score(y_eval, y_pred, zero_division=0)
    recall = recall_score(y_eval, y_pred, zero_division=0)
    f1 = f1_score(y_eval, y_pred, zero_division=0)

    interpretation_lines = interpret_confusion_matrix(tn, fp, fn, tp)

    print("=== AdaBoost Titanic Training ===")
    print(f"Original rows: {len(df)}")
    print(f"Expanded rows (10x): {len(expanded_df)}")
    print(f"Train rows (80% bootstrap from expanded): {len(train_df)}")
    print(f"Model saved: {model_path}")
    print("\n=== Confusion Matrix on 500 Resampled Rows ===")
    print(cm)
    print(f"Accuracy: {acc:.4f}")
    print(f"Precision(yes): {precision:.4f}")
    print(f"Recall(yes): {recall:.4f}")
    print(f"F1(yes): {f1:.4f}")

    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Titanic AdaBoost 분석 보고서\n\n")
        f.write("## 1) 데이터 및 전처리\n")
        f.write(f"- 원본 데이터 행 수: {len(df)}\n")
        f.write("- 타겟 변수: survived (yes/no)\n")
        f.write("- 입력 변수: status, age, sex\n")
        f.write("- 메타 행 제거 후 유효 카테고리만 사용\n\n")

        f.write("## 2) 요청된 샘플링/학습 절차\n")
        f.write("1. Stratified 10-fold 구조로 데이터를 10배 확장 (중복 포함)\n")
        f.write(f"2. 확장 데이터 {len(expanded_df)}건에서 80%를 랜덤 중복 샘플링하여 훈련셋 구성\n")
        f.write(f"3. 최종 훈련 샘플 수: {len(train_df)}\n")
        f.write("4. 모델: OneHotEncoder + AdaBoostClassifier(Decision Stump 기반)\n")
        f.write(f"5. 모델 저장 경로: `{model_path}`\n\n")

        f.write("## 3) 500개 재샘플링 평가 (Confusion Matrix)\n\n")
        f.write("Confusion Matrix (행=실제, 열=예측, 순서=[no, yes])\n\n")
        f.write("| actual\\pred | no | yes |\n")
        f.write("|---|---:|---:|\n")
        f.write(f"| no  | {tn} | {fp} |\n")
        f.write(f"| yes | {fn} | {tp} |\n\n")

        f.write("### 분류 성능 지표\n")
        f.write(f"- Accuracy: {acc:.4f}\n")
        f.write(f"- Precision(yes): {precision:.4f}\n")
        f.write(f"- Recall(yes): {recall:.4f}\n")
        f.write(f"- F1(yes): {f1:.4f}\n\n")

        f.write("## 4) 결과 해석\n")
        for line in interpretation_lines:
            f.write(f"- {line}\n")

    print(f"Report saved: {report_path}")


if __name__ == "__main__":
    main()
