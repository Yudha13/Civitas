# Roadmap

## Phase 0 — Foundation
- [x] Repository created
- [x] Architecture defined
- [x] Simulation model defined
- [ ] Initial project structure
- [ ] Development tooling

## Phase 1 — Simulation Core
- [x] World
- [x] Agent
- [x] Resource
- [x] Occupation
- [x] Simulation tick
- [x] Seeded random generator
- [x] Basic metrics
- [x] Unit tests
- [x] Population births
- [x] Working-age production rules
- [x] Population and migration validation

## Phase 2 — Society
- [x] Villages
- [x] Relationships
- [x] Trust attribute
- [x] Migration
- [x] Trade
- [x] Basic conflict

## Phase 3 — Web API
- [x] FastAPI application
- [x] Simulation lifecycle endpoints
- [x] World state endpoint
- [x] Agent inspection endpoint
- [x] Historical metrics endpoint
- [x] Event endpoint
- [x] WebSocket stream

## Phase 4 — Web Interface
- [x] Dashboard
- [x] World view foundation
- [x] Interactive village map
- [x] Village selection and linked agent filtering
- [x] Faction visual identity
- [x] Simulation controls
- [x] Agent inspector
- [x] Event log
- [x] Historical charts
- [x] React + TypeScript frontend foundation
- [x] WebSocket live updates
- [x] Frontend CI build verification

## Phase 5 — Authentication & Persistence
- [x] Google Identity Services sign-in
- [x] Backend ID token verification
- [x] Secure application session
- [x] Protected simulation API
- [x] User persistence
- [x] PostgreSQL schema and Alembic migration
- [x] User-owned simulations
- [x] Simulation metadata
- [x] Historical metrics
- [x] Simulation load/resume\n- [x] RNG state persistence for deterministic continuation\n- [x] Replay/load API

## Phase 6 — Advanced Systems

Phase 6 begins with measurement-first social stratification. Inequality metrics are deterministic, persisted with metric history, and exposed in the dashboard before inequality is allowed to influence agent behavior. The first behavior effect is now bounded and deterministic: higher wealth inequality reduces trust during social interactions. Political pressure is also derived deterministically from wealth inequality and applies a bounded penalty to faction cohesion.
- [x] Politics: bounded political pressure metric and faction cohesion response
- [x] Factions: emergent formation
- [x] Faction dynamics: membership cleanup and leader succession
- [x] Inequality measurement: wealth Gini and top-10% wealth share
- [x] Inequality social effect: bounded trust pressure during social interactions
- [ ] Environmental disasters
- [ ] War
- [ ] Epidemics
- [ ] Ideologies and belief systems

## Long-Term

CIVITAS should remain a sandbox rather than becoming a scripted strategy game. Emergent behavior is the primary feature.
