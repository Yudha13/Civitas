# Backend

FastAPI will expose the simulation engine through REST and WebSocket interfaces.

The backend stays thin: simulation rules belong in the engine, not in API routes.

Planned endpoints:
- simulation lifecycle
- world state
- events
- metrics
- WebSocket state stream
