# Historical Analysis

Stage 10 adds a deterministic analysis layer on top of the existing metric history.

## Purpose

The simulation engine remains responsible for simulation rules. Historical analysis only summarizes recorded `Metrics` snapshots and does not alter simulation state.

## Analysis window

The API accepts a bounded `limit` and analyzes the most recent snapshots:

- start and end simulation day
- elapsed days
- start, end, and change for population, wealth, food, trust, and wealth Gini
- total births, deaths, migrations, conflicts, disasters, wars, war casualties, epidemics, epidemic infections, epidemic deaths, and ideology shifts
- peak and trough day/value for population, food, wealth, and trust

## API

`GET /simulation/analysis?limit=365`

The endpoint requires an authenticated session and uses the active simulation for the current user.

## Determinism

Analysis is a pure transformation of the supplied metric snapshots. Given the same history, it returns the same result.

## Frontend integration

The dashboard loads the analysis alongside metric history and displays a compact Historical Summary. Existing charts remain unchanged and continue to show the raw historical series.

## Deliberate non-goals

Stage 10 does not add:

- predictive analytics
- machine learning
- hidden scoring or civilization ranking
- changes to simulation rules
- frontend-owned simulation calculations

The goal is observability first: make long runs easier to inspect before adding production-only concerns.
