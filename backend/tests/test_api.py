from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "API is running and model loaded successfully"
    assert data["model_loaded"] is True


def test_predict_valid_request():
    payload = {
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

    response = client.post("/predict", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert set(data.keys()) == {"churn_prediction", "churn_probability", "risk_level"}
    assert data["churn_prediction"] in (0, 1)
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["risk_level"] in {"Low", "Medium", "High"}


def test_predict_invalid_request():
    payload = {
        "age": "not-a-number",
        "watch_hours": 8.0,
        "last_login_days": 10,
        "monthly_fee": 13.99,
        "number_of_profiles": 3,
        "avg_watch_time_per_day": 1.1,
        "gender": "Male",
        "subscription_type": "Basic",
        "region": "Europe",
        "device": "Mobile",
        "payment_method": "Debit Card",
        "favorite_genre": "Comedy",
    }

    response = client.post("/predict", json=payload)
    assert response.status_code == 422
