from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_overview_endpoint():
    response = client.get("/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"total_customers", "churned_customers", "non_churned_customers", "churn_rate"}
    assert data["total_customers"] == 5000
    assert data["churned_customers"] == 2515
    assert data["non_churned_customers"] == 2485
    assert abs(data["churn_rate"] - 0.503) < 1e-6


def test_churn_distribution_endpoint():
    response = client.get("/analytics/churn-distribution")
    assert response.status_code == 200
    data = response.json()
    assert data == {"churned": 2515, "non_churned": 2485}


def test_by_subscription_endpoint():
    response = client.get("/analytics/by-subscription")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    expected = [
        {"subscription_type": "Basic", "total_customers": 1661, "churned_customers": 1027, "churn_rate": 1027 / 1661},
        {"subscription_type": "Premium", "total_customers": 1693, "churned_customers": 740, "churn_rate": 740 / 1693},
        {"subscription_type": "Standard", "total_customers": 1646, "churned_customers": 748, "churn_rate": 748 / 1646},
    ]

    for item in expected:
        record = next(entry for entry in data if entry["subscription_type"] == item["subscription_type"])
        assert record["total_customers"] == item["total_customers"]
        assert record["churned_customers"] == item["churned_customers"]
        assert abs(record["churn_rate"] - item["churn_rate"]) < 1e-9


def test_by_payment_method_endpoint():
    response = client.get("/analytics/by-payment-method")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    expected = [
        {"payment_method": "Credit Card", "total_customers": 973, "churned_customers": 424, "churn_rate": 424 / 973},
        {"payment_method": "Crypto", "total_customers": 995, "churned_customers": 594, "churn_rate": 594 / 995},
        {"payment_method": "Debit Card", "total_customers": 1030, "churned_customers": 450, "churn_rate": 450 / 1030},
        {"payment_method": "Gift Card", "total_customers": 976, "churned_customers": 564, "churn_rate": 564 / 976},
        {"payment_method": "PayPal", "total_customers": 1026, "churned_customers": 483, "churn_rate": 483 / 1026},
    ]

    for item in expected:
        record = next(entry for entry in data if entry["payment_method"] == item["payment_method"])
        assert record["total_customers"] == item["total_customers"]
        assert record["churned_customers"] == item["churned_customers"]
        assert abs(record["churn_rate"] - item["churn_rate"]) < 1e-9


def test_by_region_endpoint():
    response = client.get("/analytics/by-region")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    expected = [
        {"region": "Africa", "total_customers": 803, "churned_customers": 388, "churn_rate": 388 / 803},
        {"region": "Asia", "total_customers": 841, "churned_customers": 426, "churn_rate": 426 / 841},
        {"region": "Europe", "total_customers": 867, "churned_customers": 448, "churn_rate": 448 / 867},
        {"region": "North America", "total_customers": 851, "churned_customers": 421, "churn_rate": 421 / 851},
        {"region": "Oceania", "total_customers": 765, "churned_customers": 383, "churn_rate": 383 / 765},
        {"region": "South America", "total_customers": 873, "churned_customers": 449, "churn_rate": 449 / 873},
    ]

    for item in expected:
        record = next(entry for entry in data if entry["region"] == item["region"])
        assert record["total_customers"] == item["total_customers"]
        assert record["churned_customers"] == item["churned_customers"]
        assert abs(record["churn_rate"] - item["churn_rate"]) < 1e-9


def test_engagement_endpoint():
    response = client.get("/analytics/engagement")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"watch_hours", "last_login_days", "avg_watch_time_per_day"}
    for metric_name in ["watch_hours", "last_login_days", "avg_watch_time_per_day"]:
        assert set(data[metric_name].keys()) == {"churned", "non_churned"}
        for label in ["churned", "non_churned"]:
            stats = data[metric_name][label]
            assert set(stats.keys()) == {"mean", "median", "min", "max"}
            assert all(isinstance(stats[k], (int, float)) for k in stats)
