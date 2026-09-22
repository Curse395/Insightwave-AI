import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend import app as app_module
from backend.app import app

client = TestClient(app)


def groq_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class FakeCompletions:
    def __init__(self, response_content):
        self.response_content = response_content
        self.last_user_message = None

    def create(self, **kwargs):
        self.last_user_message = json.loads(kwargs["messages"][1]["content"])
        return groq_response(self.response_content)


class FakeGroq:
    completions = None

    def __init__(self, api_key):
        self.chat = SimpleNamespace(completions=FakeGroq.completions)


def install_fake_groq(monkeypatch, response_content):
    completions = FakeCompletions(response_content)
    FakeGroq.completions = completions
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "Groq", FakeGroq)
    return completions


def test_chat_overall_churn_question(monkeypatch):
    completions = install_fake_groq(
        monkeypatch,
        '{"answer":"The overall churn rate is 50.3%.","data_used":["overall churn statistics"]}',
    )

    response = client.post("/ai/chat", json={"message": "What is the overall churn rate?"})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "The overall churn rate is 50.3%.",
        "data_used": ["overall churn statistics"],
    }
    assert completions.last_user_message["insightwave_context"]["total_customers"] == 5000
    assert completions.last_user_message["insightwave_context"]["churned_customers"] == 2515


def test_chat_subscription_question(monkeypatch):
    completions = install_fake_groq(
        monkeypatch,
        '{"answer":"Basic has the highest churn rate.","data_used":["churn by subscription type"]}',
    )

    response = client.post("/ai/chat", json={"message": "Which subscription type has the highest churn?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Basic has the highest churn rate."
    records = completions.last_user_message["insightwave_context"]
    basic = next(item for item in records if item["subscription_type"] == "Basic")
    assert basic["churned_customers"] == 1027
    assert basic["total_customers"] == 1661


def test_chat_engagement_question(monkeypatch):
    completions = install_fake_groq(
        monkeypatch,
        '{"answer":"Churned customers show lower average watch hours.","data_used":["engagement comparisons"]}',
    )

    response = client.post("/ai/chat", json={"message": "How does watch time differ by churn status?"})
    assert response.status_code == 200
    assert response.json()["data_used"] == ["engagement comparisons"]
    context = completions.last_user_message["insightwave_context"]
    assert set(context) == {"watch_hours", "last_login_days", "avg_watch_time_per_day"}
    assert "churned" in context["watch_hours"]
    assert "non_churned" in context["watch_hours"]


def test_chat_unsupported_question_does_not_call_groq(monkeypatch):
    monkeypatch.setattr(app_module, "Groq", None)

    response = client.post("/ai/chat", json={"message": "What is our quarterly revenue forecast?"})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "The available InsightWave data does not contain enough information to answer that question.",
        "data_used": ["no matching InsightWave data"],
    }


def test_chat_empty_message_validation():
    response = client.post("/ai/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_groq_failure(monkeypatch):
    class FailingCompletions:
        def create(self, **kwargs):
            raise RuntimeError("provider unavailable")

    class FailingGroq:
        def __init__(self, api_key):
            self.chat = SimpleNamespace(completions=FailingCompletions())

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "Groq", FailingGroq)

    response = client.post("/ai/chat", json={"message": "Which region has the highest churn?"})
    assert response.status_code == 502
    assert response.json()["detail"] == "Unable to retrieve insights from Groq."
