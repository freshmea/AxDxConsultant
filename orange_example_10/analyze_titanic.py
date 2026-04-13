from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def load_titanic(path: Path) -> pd.DataFrame:
    """Load and clean Titanic categorical dataset from the provided CSV."""
    df = pd.read_csv(path)

    # Remove metadata rows and keep only valid category rows.
    df = df[df["survived"].isin(["yes", "no"])].copy()
    valid_status = {"first", "second", "third", "crew"}
    valid_age = {"adult", "child"}
    valid_sex = {"male", "female"}

    df = df[
        df["status"].isin(valid_status)
        & df["age"].isin(valid_age)
        & df["sex"].isin(valid_sex)
    ].copy()

    return df.reset_index(drop=True)


def survival_table(df: pd.DataFrame, col: str) -> pd.DataFrame:
    table = (
        df.groupby([col, "survived"]).size().unstack(fill_value=0).rename(columns={"yes": "survived_yes", "no": "survived_no"})
    )
    table["total"] = table.sum(axis=1)
    table["survival_rate"] = (table["survived_yes"] / table["total"] * 100).round(2)
    return table.sort_values("survival_rate", ascending=False)


def run_analysis(csv_path: Path) -> None:
    df = load_titanic(csv_path)

    # 1) Statistical analysis first
    n_total = len(df)
    n_survived = (df["survived"] == "yes").sum()
    overall_rate = n_survived / n_total * 100

    status_tbl = survival_table(df, "status")
    age_tbl = survival_table(df, "age")
    sex_tbl = survival_table(df, "sex")

    combo_tbl = (
        df.groupby(["status", "age", "sex", "survived"]).size().unstack(fill_value=0).rename(columns={"yes": "survived_yes", "no": "survived_no"})
    )
    combo_tbl["total"] = combo_tbl.sum(axis=1)
    combo_tbl["survival_rate"] = (combo_tbl["survived_yes"] / combo_tbl["total"] * 100).round(2)
    combo_tbl = combo_tbl.sort_values("survival_rate", ascending=False)

    # 2) Machine learning analysis with scikit-learn
    X = df[["status", "age", "sex"]]
    y = (df["survived"] == "yes").astype(int)

    categorical_features = ["status", "age", "sex"]
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(drop="first", handle_unknown="ignore"),
                categorical_features,
            )
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    test_accuracy = accuracy_score(y_test, y_pred)
    test_auc = roc_auc_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, target_names=["no", "yes"])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_acc = cross_val_score(model, X, y, cv=cv, scoring="accuracy")
    cv_auc = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")

    ohe = model.named_steps["preprocessor"].named_transformers_["cat"]
    feature_names = ohe.get_feature_names_out(categorical_features)
    coefficients = model.named_steps["classifier"].coef_[0]
    coef_tbl = (
        pd.DataFrame({"feature": feature_names, "coefficient": coefficients})
        .assign(abs_coef=lambda d: d["coefficient"].abs())
        .sort_values("abs_coef", ascending=False)
        .drop(columns=["abs_coef"])
    )

    # Console output
    print("=== Titanic Survival Analysis (status, age, sex) ===")
    print(f"Total rows: {n_total}")
    print(f"Survived: {n_survived} ({overall_rate:.2f}%)")
    print("\n[Survival by status]")
    print(status_tbl)
    print("\n[Survival by age]")
    print(age_tbl)
    print("\n[Survival by sex]")
    print(sex_tbl)
    print("\n[Top 15 combinations by survival rate]")
    print(combo_tbl.head(15))

    print("\n=== Logistic Regression Results ===")
    print(f"Test Accuracy: {test_accuracy:.4f}")
    print(f"Test ROC-AUC: {test_auc:.4f}")
    print(f"CV Accuracy (5-fold): {cv_acc.mean():.4f} +/- {cv_acc.std():.4f}")
    print(f"CV ROC-AUC (5-fold): {cv_auc.mean():.4f} +/- {cv_auc.std():.4f}")
    print("\n[Classification Report]")
    print(report)
    print("[Feature Coefficients]")
    print(coef_tbl.to_string(index=False))

    # Markdown report file
    report_path = csv_path.parent / "titanic_survival_report.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Titanic 생존 분석 보고서\n\n")
        f.write("## 1. 데이터 개요\n")
        f.write(f"- 전체 관측치: {n_total}건\n")
        f.write(f"- 생존자: {n_survived}건 ({overall_rate:.2f}%)\n\n")

        f.write("## 2. 통계 분석 (기술통계)\n\n")
        f.write("### 2.1 status별 생존\n\n")
        f.write(status_tbl.to_markdown())
        f.write("\n\n### 2.2 age별 생존\n\n")
        f.write(age_tbl.to_markdown())
        f.write("\n\n### 2.3 sex별 생존\n\n")
        f.write(sex_tbl.to_markdown())
        f.write("\n\n### 2.4 status-age-sex 조합 상위(생존률 기준)\n\n")
        f.write(combo_tbl.head(15).to_markdown())
        f.write("\n\n")

        f.write("## 3. scikit-learn 예측 분석\n\n")
        f.write("모델: One-Hot Encoding + Logistic Regression\n\n")
        f.write(f"- Test Accuracy: {test_accuracy:.4f}\n")
        f.write(f"- Test ROC-AUC: {test_auc:.4f}\n")
        f.write(f"- 5-Fold CV Accuracy: {cv_acc.mean():.4f} ± {cv_acc.std():.4f}\n")
        f.write(f"- 5-Fold CV ROC-AUC: {cv_auc.mean():.4f} ± {cv_auc.std():.4f}\n\n")

        f.write("### 3.1 분류 리포트\n\n```")
        f.write(report)
        f.write("```\n\n")

        f.write("### 3.2 변수 영향(로지스틱 계수)\n\n")
        f.write(coef_tbl.to_markdown(index=False))
        f.write("\n")

    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    csv_file = Path(r"C:\Users\Administrator\dxAx\orange_example\titanic.csv")
    run_analysis(csv_file)
