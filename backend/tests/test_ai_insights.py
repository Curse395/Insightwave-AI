from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend import app as app_module
from backend.app import app

client = TestClient(app)

PAYLOAD = {
    "age": 34,
    "watch_hours": 12.5,
    "last_login_days": 8,
    "monthly_fee": 13.99,
    "number_of_profiles": 2,
    "avg_watch_time_per_day": 1.8,
    "gender": "Female",
    "subscription_type": "Standard",
    "region": "North America",
    "device": "TV",
    "payment_method": "Credit Card",
    "favorite_genre": "Drama",
}


def groq_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def test_ai_insights_valid_request(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["model"] == "openai/gpt-oss-120b"
            assert kwargs["response_format"] == {"type": "json_object"}
            return groq_response(
                '{"explanation":"Low risk based on the supplied profile.",'
                '"behavioral_insights":["Recent login activity is favorable."],'
                '"retention_recommendations":["Offer personalized content discovery."]}'
            )

    class FakeGroq:
        def __init__(self, api_key):
            assert api_key == "test-key"
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "Groq", FakeGroq)

    response = client.post("/ai/insights", json=PAYLOAD)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {
        "churn_prediction",
        "churn_probability",
        "risk_level",
        "explanation",
        "behavioral_insights",
        "retention_recommendations",
    }
    assert data["churn_prediction"] in (0, 1)
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["risk_level"] in {"Low", "Medium", "High"}
    assert isinstance(data["behavioral_insights"], list)
    assert isinstance(data["retention_recommendations"], list)


def test_ai_insights_invalid_request():
    invalid_payload = {**PAYLOAD, "watch_hours": "not-a-number"}

    response = client.post("/ai/insights", json=invalid_payload)
    assert response.status_code == 422


def test_ai_insights_groq_failure(monkeypatch):
    class FailingGroq:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=self)

        def create(self, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "Groq", FailingGroq)

    response = client.post("/ai/insights", json=PAYLOAD)
    assert response.status_code == 502
    assert response.json()["detail"] == "Unable to retrieve insights from Groq."


def test_ai_insights_missing_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    response = client.post("/ai/insights", json=PAYLOAD)
    assert response.status_code == 503
    assert response.json()["detail"] == "GROQ_API_KEY is not configured."
