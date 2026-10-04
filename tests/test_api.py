from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_and_state_endpoints():
    response = client.post(
        "/simulation/start",
        json={"seed": 42, "population": 30},
    )
    assert response.status_code == 200
    state = response.json()
    assert state["day"] == 0
    assert state["population"] == 30
    assert len(state["villages"]) == 3


def test_tick_and_metrics_endpoints():
    client.post("/simulation/start", json={"seed": 42, "population": 30})
    tick = client.post("/simulation/tick")
    metrics = client.get("/simulation/metrics")

    assert tick.status_code == 200
    assert tick.json()["day"] == 1
    assert metrics.status_code == 200
    assert metrics.json()["day"] == 1


def test_run_and_event_endpoints():
    client.post("/simulation/start", json={"seed": 7, "population": 20})
    run = client.post("/simulation/run", json={"days": 5})
    events = client.get("/simulation/events?limit=5")

    assert run.status_code == 200
    assert run.json()["day"] == 5
    assert events.status_code == 200
    assert len(events.json()) == 5


def test_event_limit_is_validated():
    response = client.get("/simulation/events?limit=0")
    assert response.status_code == 400
