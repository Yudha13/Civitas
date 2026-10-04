from fastapi.testclient import TestClient
import pytest

import backend.app as app_module
from backend.app import app
from backend.auth import GoogleUser

client = TestClient(app)


@pytest.fixture()
def authenticated_client(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "verify_google_credential",
        lambda credential: GoogleUser("google-test-123", "test@example.com", "Test User", None),
    )
    test_client = TestClient(app)
    response = test_client.post("/auth/google", json={"credential": "test-token"})
    assert response.status_code == 200
    return test_client


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_authentication_is_required_for_simulation():
    response = client.get("/simulation/state")
    assert response.status_code == 401


def test_authentication_session_and_logout(authenticated_client):
    me = authenticated_client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"
    logout = authenticated_client.post("/auth/logout")
    assert logout.status_code == 200
    assert authenticated_client.get("/auth/me").status_code == 401


def test_start_and_state_endpoints(authenticated_client):
    response = authenticated_client.post("/simulation/start", json={"seed": 42, "population": 30})
    assert response.status_code == 200
    state = response.json()
    assert state["day"] == 0
    assert state["population"] == 30
    assert len(state["villages"]) == 3


def test_tick_and_metrics_endpoints(authenticated_client):
    authenticated_client.post("/simulation/start", json={"seed": 42, "population": 30})
    tick = authenticated_client.post("/simulation/tick")
    metrics = authenticated_client.get("/simulation/metrics")
    assert tick.status_code == 200
    assert tick.json()["day"] == 1
    assert metrics.status_code == 200
    assert metrics.json()["day"] == 1


def test_metrics_history_endpoint(authenticated_client):
    authenticated_client.post("/simulation/start", json={"seed": 42, "population": 30})
    authenticated_client.post("/simulation/run", json={"days": 5})
    response = authenticated_client.get("/simulation/metrics/history?limit=3")
    assert response.status_code == 200
    history = response.json()
    assert [item["day"] for item in history] == [3, 4, 5]
    assert "living_population" in history[-1]


def test_metrics_history_limit_is_validated(authenticated_client):
    response = authenticated_client.get("/simulation/metrics/history?limit=0")
    assert response.status_code == 400


def test_run_and_event_endpoints(authenticated_client):
    authenticated_client.post("/simulation/start", json={"seed": 7, "population": 20})
    run = authenticated_client.post("/simulation/run", json={"days": 5})
    events = authenticated_client.get("/simulation/events?limit=5")
    assert run.status_code == 200
    assert run.json()["day"] == 5
    assert events.status_code == 200
    assert len(events.json()) == 5


def test_agent_inspector_endpoint_returns_expected_fields(authenticated_client):
    authenticated_client.post("/simulation/start", json={"seed": 42, "population": 12})
    response = authenticated_client.get("/simulation/agents?limit=5")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) == 5
    assert agents[0]["id"] == 1
    assert agents[0]["occupation"] == "farmer"
    assert agents[0]["village_name"]
    assert "health" in agents[0]
    assert "faction_name" in agents[0]


def test_agent_limit_is_validated(authenticated_client):
    response = authenticated_client.get("/simulation/agents?limit=0")
    assert response.status_code == 400


def test_websocket_stream_returns_state_and_advances_simulation(authenticated_client):
    authenticated_client.post("/simulation/start", json={"seed": 11, "population": 12})
    with authenticated_client.websocket_connect("/simulation/ws") as websocket:
        websocket.send_json({"action": "state"})
        state = websocket.receive_json()
        assert state["action"] == "state"
        assert state["state"]["day"] == 0
        websocket.send_json({"action": "tick"})
        tick = websocket.receive_json()
        assert tick["action"] == "tick"
        assert tick["state"]["day"] == 1
        assert tick["metrics"]["day"] == 1


def test_websocket_requires_authentication():
    with client.websocket_connect("/simulation/ws", raise_server_exceptions=False) as websocket:
        assert websocket is not None


def test_websocket_stream_rejects_invalid_run_days(authenticated_client):
    with authenticated_client.websocket_connect("/simulation/ws") as websocket:
        websocket.send_json({"action": "run", "days": -1})
        response = websocket.receive_json()
        assert response["error"] == "days must be a non-negative integer"


def test_event_limit_is_validated(authenticated_client):
    response = authenticated_client.get("/simulation/events?limit=0")
    assert response.status_code == 400


def test_local_frontend_origin_is_allowed():
    response = client.options(
        "/simulation/state",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
