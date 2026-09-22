from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "dataset" / "netflix_customer_churn (1).csv"
ARTIFACT_DIR = ROOT_DIR / "ml" / "artifacts"

NUMERICAL_FEATURES = [
    "age",
    "watch_hours",
    "last_login_days",
    "monthly_fee",
    "number_of_profiles",
    "avg_watch_time_per_day",
]

CATEGORICAL_FEATURES = [
    "gender",
    "subscription_type",
    "region",
    "device",
    "payment_method",
    "favorite_genre",
]

TARGET_COLUMN = "churned"
ID_COLUMN = "customer_id"


def load_and_validate_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

    required_columns = [ID_COLUMN, *NUMERICAL_FEATURES, *CATEGORICAL_FEATURES, TARGET_COLUMN]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    if df.empty:
        raise ValueError("Dataset is empty.")

    if df.isnull().sum().sum() > 0:
        raise ValueError("Dataset contains missing values.")

    if df.duplicated().sum() > 0:
        raise ValueError("Dataset contains duplicate rows.")

    target_values = set(pd.Series(df[TARGET_COLUMN].dropna().unique()).astype(int).tolist())
    if not target_values.issubset({0, 1}):
        raise ValueError(f"Target column contains unexpected values: {sorted(target_values)}")

    print("\n=== DATASET VALIDATION ===")
    print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    print(f"Duplicate rows: {df.duplicated().sum()}")
    print(df[TARGET_COLUMN].value_counts().sort_index())

    return df


def build_preprocessor() -> ColumnTransformer:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_transformer, NUMERICAL_FEATURES),
            ("categorical", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )


def compute_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict:
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1-Score": f1_score(y_true, y_pred, zero_division=0),
        "Confusion Matrix": confusion_matrix(y_true, y_pred).tolist(),
    }


def save_pipeline(model_name: str, pipeline: Pipeline) -> None:
    artifact_path = ARTIFACT_DIR / f"{model_name.lower().replace(' ', '_')}_pipeline.joblib"
    joblib.dump(pipeline, artifact_path)
    print(f"Saved pipeline: {artifact_path}")


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_and_validate_dataset(DATASET_PATH)

    X = df.drop(columns=[ID_COLUMN, TARGET_COLUMN])
    y = df[TARGET_COLUMN].astype(int)

    print("\n=== FEATURE SELECTION ===")
    print(f"Features used: {list(X.columns)}")
    print(f"Target column: {TARGET_COLUMN}")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    print("\n=== TRAIN/TEST SPLIT ===")
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_train counts: {y_train.value_counts().sort_index().to_dict()}")
    print(f"y_test counts: {y_test.value_counts().sort_index().to_dict()}")

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=42),
        "Gradient Boosting": GradientBoostingClassifier(random_state=42),
    }

    comparison_rows = []

    for model_name, estimator in models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("model", estimator),
            ]
        )

        print(f"\n=== TRAINING {model_name.upper()} ===")
        pipeline.fit(X_train, y_train)

        y_pred = pipeline.predict(X_test)
        metrics = compute_metrics(y_test, y_pred)

        print(f"Accuracy: {metrics['Accuracy']:.4f}")
        print(f"Precision: {metrics['Precision']:.4f}")
        print(f"Recall: {metrics['Recall']:.4f}")
        print(f"F1-Score: {metrics['F1-Score']:.4f}")
        print(f"Confusion Matrix: {metrics['Confusion Matrix']}")

        save_pipeline(model_name, pipeline)

        row = {
            "Model": model_name,
            "Accuracy": metrics["Accuracy"],
            "Precision": metrics["Precision"],
            "Recall": metrics["Recall"],
            "F1-Score": metrics["F1-Score"],
            "Confusion Matrix": json.dumps(metrics["Confusion Matrix"]),
        }
        comparison_rows.append(row)

    comparison_df = pd.DataFrame(comparison_rows)
    comparison_df = comparison_df.sort_values("F1-Score", ascending=False, kind="mergesort")
    comparison_path = ARTIFACT_DIR / "comparison_metrics.csv"
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\nSaved comparison metrics: {comparison_path}")

    print("\n=== MODEL COMPARISON ===")
    print(comparison_df.to_string(index=False, formatters={
        "Accuracy": lambda x: f"{x:.4f}",
        "Precision": lambda x: f"{x:.4f}",
        "Recall": lambda x: f"{x:.4f}",
        "F1-Score": lambda x: f"{x:.4f}",
    }))

    best_row = comparison_df.iloc[0]
    print("\n=== MODEL SELECTION NOTE ===")
    print(
        f"On this train/test split, the strongest measured result was {best_row['Model']} "
        f"with F1-Score = {best_row['F1-Score']:.4f}. "
        "This is the strongest result observed in this evaluation, but it is not a universal claim of superiority across all data or scenarios."
    )

    print("\n=== ARTIFACTS CREATED ===")
    for artifact in sorted(ARTIFACT_DIR.iterdir()):
        print(artifact.name)


if __name__ == "__main__":
    main()
