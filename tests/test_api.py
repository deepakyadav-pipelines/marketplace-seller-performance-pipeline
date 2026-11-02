
from fastapi.testclient import TestClient
from src import api

client = TestClient(api.app)


def test_health_check(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_one",
        lambda *args, **kwargs: {"test": 1}
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["database"] == "connected"


def test_order_not_found(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_one",
        lambda *args, **kwargs: None
    )

    response = client.get("/orders/invalid-order-id")

    assert response.status_code == 404


def test_invalid_scorecard_month():
    response = client.get(
        "/sellers/test-seller/scorecard?month=2018-13"
    )

    assert response.status_code == 400


def test_invalid_top_sellers_metric():
    response = client.get(
        "/sellers/top?month=2018-03&metric=invalid"
    )

    assert response.status_code == 400


def test_campaign_not_found(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_one",
        lambda *args, **kwargs: None
    )

    response = client.get("/campaigns/INVALID/performance")

    assert response.status_code == 404


def test_data_quality_run_not_found(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_one",
        lambda *args, **kwargs: None
    )

    response = client.get("/data-quality/summary?run_id=999999")

    assert response.status_code == 404



def test_existing_order_returns_success():
    response = client.get("/orders/00010242fe8c5a6d1ba2dd792cb16214")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data


def test_existing_campaign_returns_success():
    response = client.get("/campaigns/C001/performance")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert data


def test_monthly_kpis_returns_success():
    response = client.get(
        "/kpis/monthly?start=2018-01&end=2018-03&region=sul"
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (dict, list))


def test_top_sellers_returns_success():
    response = client.get(
        "/sellers/top?month=2018-03&metric=commission_usd&limit=5"
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, (dict, list))
