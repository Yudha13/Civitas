# CIVITAS Backend

FastAPI service exposing the simulation engine.

## Run locally

```bash
pip install -r backend/requirements.txt
uvicorn backend.app:app --reload
```

Initial endpoints:

- `GET /health`
- `POST /simulation/start`
- `POST /simulation/tick`
- `POST /simulation/run`
- `GET /simulation/state`
- `GET /simulation/metrics`
- `GET /simulation/events`
- `WS /simulation/ws`

The API is intentionally thin. Simulation rules remain in `simulation/`.


## WebSocket commands

Send JSON commands: `{"action":"state"}`, `{"action":"tick"}`, or `{"action":"run","days":10}`. Each accepted command returns the current world state and metrics.
