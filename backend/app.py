from __future__ import annotations

import json
import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError

try:
    from groq import Groq
except ImportError:
    Groq = None

ROOT_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT_DIR / "ml" / "artifacts" / "gradient_boosting_pipeline.joblib"
DATASET_PATH = ROOT_DIR / "dataset" / "netflix_customer_churn (1).csv"

load_dotenv(ROOT_DIR / ".env")


class CustomerFeatures(BaseModel):
    age: int
    watch_hours: float
    last_login_days: int
    monthly_fee: float
    number_of_profiles: int
    avg_watch_time_per_day: float
    gender: str
    subscription_type: str
    region: str
    device: str
    payment_method: str
    favorite_genre: str

    model_config = ConfigDict(extra="forbid")


class AIInsights(BaseModel):
    explanation: str
    behavioral_insights: list[str]
    retention_recommendations: list[str]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class ChatResponse(BaseModel):
    answer: str
    data_used: list[str]


app = FastAPI(title="InsightWave Prediction API")


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


MODEL = load_model()


def get_risk_level(probability: float) -> str:
    if probability < 0.40:
        return "Low"
    if probability < 0.70:
        return "Medium"
    return "High"


def get_prediction(payload: CustomerFeatures) -> dict:
    feature_row = pd.DataFrame([payload.model_dump()])
    probability = float(MODEL.predict_proba(feature_row)[0, 1])
    return {
        "churn_prediction": int(probability >= 0.5),
        "churn_probability": probability,
        "risk_level": get_risk_level(probability),
    }


def request_groq_json(system_message: str, user_message: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured.")
    if Groq is None:
        raise HTTPException(status_code=503, detail="Groq SDK is not installed.")

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )
        content = completion.choices[0].message.content
        return json.loads(content)
    except HTTPException:
        raise
    except (json.JSONDecodeError, IndexError, AttributeError) as error:
        raise HTTPException(status_code=502, detail="Groq returned a malformed insights response.") from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="Unable to retrieve insights from Groq.") from error


def request_ai_insights(payload: CustomerFeatures, prediction: dict) -> AIInsights:
    customer_data = payload.model_dump()
    prompt = {
        "customer_features": customer_data,
        "ml_prediction": prediction,
        "behavioral_indicators": {
            "watch_hours": customer_data["watch_hours"],
            "last_login_days": customer_data["last_login_days"],
            "avg_watch_time_per_day": customer_data["avg_watch_time_per_day"],
        },
    }
    system_message = (
        "You provide concise churn explanations for a media streaming business dashboard. "
        "The churn prediction, probability, and risk level are produced by the ML model and "
        "must not be changed or recalculated. Explain only the supplied customer information. "
        "Focus on observable behavior, avoid unsupported certainty, do not invent facts, and "
        "recommend realistic retention actions. Return JSON with exactly these fields: "
        "explanation (string), behavioral_insights (array of concise strings), and "
        "retention_recommendations (array of concise strings)."
    )
    try:
        return AIInsights.model_validate(request_groq_json(system_message, json.dumps(prompt)))
    except HTTPException:
        raise
    except ValidationError as error:
        raise HTTPException(status_code=502, detail="Groq returned a malformed insights response.") from error


def build_chat_context(message: str, df: pd.DataFrame) -> tuple[list[str], dict | None]:
    question = message.lower()
    if (
        any(term in question for term in ["overall churn", "churn rate", "total customers", "churned customers", "non-churned"])
        and not any(term in question for term in ["subscription", "plan"])
    ):
        total = len(df)
        churned = int(df["churned"].sum())
        return ["overall churn statistics"], {
            "total_customers": int(total),
            "churned_customers": churned,
            "non_churned_customers": int(total - churned),
            "churn_rate": float(churned / total),
        }
    if any(term in question for term in ["subscription", "plan"]):
        grouped = (
            df.groupby("subscription_type", as_index=False)
            .agg(total_customers=("customer_id", "count"), churned_customers=("churned", "sum"))
            .assign(churn_rate=lambda x: x["churned_customers"] / x["total_customers"])
        )
        return ["churn by subscription type"], grouped.to_dict(orient="records")
    if any(term in question for term in ["payment", "billing"]):
        grouped = (
            df.groupby("payment_method", as_index=False)
            .agg(total_customers=("customer_id", "count"), churned_customers=("churned", "sum"))
            .assign(churn_rate=lambda x: x["churned_customers"] / x["total_customers"])
        )
        return ["churn by payment method"], grouped.to_dict(orient="records")
    if any(term in question for term in ["region", "geographic", "geography"]):
        grouped = (
            df.groupby("region", as_index=False)
            .agg(total_customers=("customer_id", "count"), churned_customers=("churned", "sum"))
            .assign(churn_rate=lambda x: x["churned_customers"] / x["total_customers"])
        )
        return ["churn by region"], grouped.to_dict(orient="records")
    if any(term in question for term in ["engagement", "watch", "login", "behavior", "behavioral"]):
        context = {}
        for column in ["watch_hours", "last_login_days", "avg_watch_time_per_day"]:
            grouped = df.groupby("churned")[column].agg(["mean", "median", "min", "max"])
            context[column] = {
                "churned": grouped.loc[1].to_dict(),
                "non_churned": grouped.loc[0].to_dict(),
            }
        return ["engagement comparisons"], context
    return [], None


def load_dataset() -> pd.DataFrame:
    return pd.read_csv(DATASET_PATH)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "message": "API is running and model loaded successfully",
        "model_loaded": True,
    }


@app.post("/predict")
def predict(payload: CustomerFeatures) -> dict:
    return get_prediction(payload)


@app.post("/ai/insights")
def ai_insights(payload: CustomerFeatures) -> dict:
    prediction = get_prediction(payload)
    insights = request_ai_insights(payload, prediction)
    return {**prediction, **insights.model_dump()}


@app.post("/ai/chat", response_model=ChatResponse)
def ai_chat(payload: ChatRequest) -> ChatResponse:
    data_used, context = build_chat_context(payload.message, load_dataset())
    if context is None:
        return ChatResponse(
            answer="The available InsightWave data does not contain enough information to answer that question.",
            data_used=["no matching InsightWave data"],
        )

    system_message = (
        "You are the InsightWave business analytics assistant. Answer concisely using only the "
        "supplied InsightWave context and user question. Do not invent statistics, customer "
        "information, or calculations that were not supplied. If the context is insufficient, "
        "say so clearly. Distinguish calculated facts from recommendations. Do not perform churn "
        "prediction; ML predictions remain the responsibility of the existing Gradient Boosting "
        "model. Return JSON with exactly two fields: answer (string) and data_used (array of "
        "short strings identifying the supplied data types)."
    )
    user_message = json.dumps({
        "question": payload.message,
        "insightwave_context": context,
        "context_types": data_used,
    })
    try:
        return ChatResponse.model_validate(request_groq_json(system_message, user_message))
    except HTTPException:
        raise
    except ValidationError as error:
        raise HTTPException(status_code=502, detail="Groq returned a malformed chat response.") from error


@app.get("/analytics/overview")
def analytics_overview() -> dict:
    df = load_dataset()
    total_customers = int(len(df))
    churned_customers = int(df["churned"].sum())
    non_churned_customers = total_customers - churned_customers
    churn_rate = float(churned_customers / total_customers) if total_customers else 0.0

    return {
        "total_customers": total_customers,
        "churned_customers": churned_customers,
        "non_churned_customers": non_churned_customers,
        "churn_rate": churn_rate,
    }


@app.get("/analytics/churn-distribution")
def analytics_churn_distribution() -> dict:
    df = load_dataset()
    total = int(len(df))
    churned = int(df["churned"].sum())
    non_churned = total - churned

    return {
        "churned": churned,
        "non_churned": non_churned,
    }


@app.get("/analytics/by-subscription")
def analytics_by_subscription() -> list[dict]:
    df = load_dataset()
    grouped = (
        df.groupby("subscription_type", as_index=False)
        .agg(total_customers=("customer_id", "count"), churned_customers=("churned", "sum"))
        .assign(churn_rate=lambda x: x["churned_customers"] / x["total_customers"])
    )
    return grouped[["subscription_type", "total_customers", "churned_customers", "churn_rate"]].to_dict(orient="records")


@app.get("/analytics/by-payment-method")
def analytics_by_payment_method() -> list[dict]:
    df = load_dataset()
    grouped = (
        df.groupby("payment_method", as_index=False)
        .agg(total_customers=("customer_id", "count"), churned_customers=("churned", "sum"))
        .assign(churn_rate=lambda x: x["churned_customers"] / x["total_customers"])
    )
    return grouped[["payment_method", "total_customers", "churned_customers", "churn_rate"]].to_dict(orient="records")


@app.get("/analytics/by-region")
def analytics_by_region() -> list[dict]:
    df = load_dataset()
    grouped = (
        df.groupby("region", as_index=False)
        .agg(total_customers=("customer_id", "count"), churned_customers=("churned", "sum"))
        .assign(churn_rate=lambda x: x["churned_customers"] / x["total_customers"])
    )
    return grouped[["region", "total_customers", "churned_customers", "churn_rate"]].to_dict(orient="records")


@app.get("/analytics/engagement")
def analytics_engagement() -> dict:
    df = load_dataset()
    metrics = {}
    for column in ["watch_hours", "last_login_days", "avg_watch_time_per_day"]:
        grouped = df.groupby("churned")[column].agg(["mean", "median", "min", "max"])
        metrics[column] = {
            "churned": grouped.loc[1].to_dict(),
            "non_churned": grouped.loc[0].to_dict(),
        }
    return metrics
