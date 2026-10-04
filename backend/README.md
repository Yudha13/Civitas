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

The API is intentionally thin. Simulation rules remain in `simulation/`.
