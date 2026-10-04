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


def test_websocket_stream_returns_state_and_advances_simulation():
    client.post("/simulation/start", json={"seed": 11, "population": 12})

    with client.websocket_connect("/simulation/ws") as websocket:
        websocket.send_json({"action": "state"})
        state = websocket.receive_json()
        assert state["action"] == "state"
        assert state["state"]["day"] == 0

        websocket.send_json({"action": "tick"})
        tick = websocket.receive_json()
        assert tick["action"] == "tick"
        assert tick["state"]["day"] == 1
        assert tick["metrics"]["day"] == 1


def test_websocket_stream_rejects_invalid_run_days():
    with client.websocket_connect("/simulation/ws") as websocket:
        websocket.send_json({"action": "run", "days": -1})
        response = websocket.receive_json()
        assert response["error"] == "days must be a non-negative integer"


def test_event_limit_is_validated():
    response = client.get("/simulation/events?limit=0")
    assert response.status_code == 400
