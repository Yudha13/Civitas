# Frontend

React + TypeScript client for CIVITAS, built with Vite.

The frontend observes and controls the simulation through the backend. It must not contain authoritative simulation rules.

## Current dashboard

- world overview for the three villages
- live simulation day and population metrics
- Food, Wood, Stone, trust, and faction metrics
- simulation controls: new simulation, tick, and run
- WebSocket live state updates
- faction overview
- recent event log
- responsive dark interface

## Local development

Run the backend from the repository root:

```bash
PYTHONPATH=. uvicorn backend.app:app --reload
```

Then run the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000` by default. Override it with `VITE_API_URL` and `VITE_WS_URL` when needed.

## Remaining Phase 4 work

- agent inspector
- historical charts
- richer world visualization
