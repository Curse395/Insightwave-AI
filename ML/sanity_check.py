import pandas as pd

df = pd.read_csv("dataset/netflix_customer_churn (1).csv")

features = [
    "age",
    "watch_hours",
    "last_login_days",
    "monthly_fee",
    "number_of_profiles",
    "avg_watch_time_per_day",
]

print("\n--- CORRELATION WITH CHURN ---")
print(
    df[features + ["churned"]]
    .corr(numeric_only=True)["churned"]
    .sort_values(ascending=False)
)

print("\n--- CHURN GROUP MEDIANS ---")
print(
    df.groupby("churned")[features]
    .median()
)

print("\n--- CHURN GROUP MEANS ---")
print(
    df.groupby("churned")[features]
    .mean()
)