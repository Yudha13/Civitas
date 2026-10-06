# CIVITAS Closed Beta

## Status

CIVITAS is now entering **Closed Beta** after completion and regression verification of Stages 1–10.

Verification baseline:

- GitHub Actions Run #199
- Frontend build: **PASS**
- Pytest: **64 passed**
- Pytest warnings: 1 dependency deprecation warning
- Stage 10 historical analysis: implemented and documented

## Beta Goal

Closed Beta is for controlled use, validation, and observation of emergent simulation behavior. It is not a production release.

The beta should answer:

1. Does the simulation remain valid during longer runs?
2. Do emergent systems interact without producing runaway or invalid state?
3. Is the dashboard sufficient to understand what happened?
4. Are persistence, replay, and historical analysis reliable?
5. Which behaviors feel emergent versus accidentally scripted?

## Current Scope

The completed system includes:

- deterministic seeded simulation
- population, production, consumption, births, deaths
- villages, migration, trade, trust, conflict
- factions and political pressure
- inequality and bounded social effects
- environmental disasters
- faction war
- epidemics and immunity
- ideologies and bounded belief commitment
- REST API and WebSocket updates
- authentication and persistence
- historical metrics and analysis
- browser dashboard and agent inspection

## Known Beta Limitations

These are intentionally outside the current scope:

- vaccination and advanced public-health policy
- hospitals and medical infrastructure
- disease strains, mutation, and seasonal epidemiology
- advanced military units and tactical warfare
- predictive analytics or machine learning
- production deployment hardening
- large-scale distributed simulation
- scripted victory conditions
- strategy-game balancing

## Validation Policy

Every change during Closed Beta should preserve:

- seeded determinism
- world-state validation
- bounded social effects
- persistence compatibility
- API contract stability
- frontend build success
- complete regression test success

A feature is not considered complete merely because the UI renders. The simulation and persistence layers must remain testable independently.

## Bug-Fix Priority

1. Invalid simulation state
2. Determinism/replay regression
3. Persistence/data corruption
4. API correctness
5. Frontend runtime/build failures
6. Emergent behavior balance
7. UX improvements
8. New features

## Next Phase

After Closed Beta stabilization, the project can move toward production preparation. Production work should focus first on deployment, observability, database operations, security hardening, backups, performance/load testing, and operational recovery.

New simulation features should be added only after beta findings are understood.
