import pandas as pd

df = pd.read_csv("dataset/netflix_customer_churn (1).csv")

print("\n--- DATASET SHAPE ---")
print(df.shape)

print("\n--- DATA TYPES ---")
print(df.dtypes)

print("\n--- MISSING VALUES ---")
print(df.isnull().sum())

print("\n--- DUPLICATES ---")
print(df.duplicated().sum())

print("\n--- CHURN DISTRIBUTION ---")
print(df["churned"].value_counts())
print(df["churned"].value_counts(normalize=True) * 100)

print("\n--- NUMERICAL SUMMARY ---")
print(df.describe())

print("\n--- CATEGORICAL VALUES ---")
for column in df.select_dtypes(include="object").columns:
    print(f"\n{column}:")
    print(df[column].value_counts())

print("\n--- NUMERICAL FEATURES BY CHURN ---")
numeric_columns = df.select_dtypes(include="number").columns.drop(
    "customer_id", errors="ignore"
)

print(df.groupby("churned")[numeric_columns].mean())

print("\n--- CATEGORICAL FEATURES BY CHURN ---")
categorical_columns = df.select_dtypes(include="object").columns

for column in categorical_columns:
    print(f"\n{column}")
    print(pd.crosstab(df[column], df["churned"], normalize="index") * 100)

print("\n--- CHURN RATE BY NUMERICAL FEATURES ---")

for column in numeric_columns:
    if column != "churned":
        print(f"\n{column}")
        print(
            df.groupby("churned")[column]
            .agg(["min", "max", "mean", "median"])
        )

print("\n--- CHURN RATE BY CATEGORICAL FEATURES ---")

for column in categorical_columns:
    if column != "customer_id":
        print(f"\n{column}")
        print(
            df.groupby(column)["churned"]
            .agg(["count", "mean"])
            .assign(churn_rate=lambda x: x["mean"] * 100)
        )