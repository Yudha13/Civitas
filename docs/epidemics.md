# CIVITAS Epidemics

## Purpose

The epidemic system models disease as an emergent population process rather than a scripted historical event.

A disease can appear in a sufficiently populated village, spread through existing social relationships, reduce agent health, kill vulnerable agents, and produce temporary immunity in survivors.

## Simulation rules

- Disease state is stored per agent with `disease_days` and `immune`.
- Epidemic introduction is probabilistic and seeded by the simulation RNG.
- Transmission requires an existing social relationship with at least one recorded interaction.
- Local population density scales transmission probability within bounded limits.
- Infection lasts for a bounded number of simulation days.
- Each infected day applies bounded health damage.
- Agents with critically low health have a small bounded mortality chance.
- Survivors recover and become immune.
- Immune agents cannot be infected again by the current disease model.
- Epidemic deaths also contribute to the global death metric.
- World validation rejects negative disease duration.

## Metrics

Historical metric snapshots expose:

- `epidemics`: newly started outbreaks for the day.
- `epidemic_infections`: new infections for the day, including the initial case.
- `epidemic_deaths`: deaths caused by the epidemic for the day.

The dashboard exposes all three metrics and their historical charts.

## Persistence

Agent disease state is persisted with the simulation:

- `disease_days`
- `immune`

Historical epidemic metrics are persisted through Alembic migration `0008`.

RNG state remains persisted by the existing simulation repository, so epidemic continuation follows the same deterministic load/resume model as the other simulation systems.

## Events

The engine emits:

- `epidemic_started`
- `epidemic_case`
- `epidemic_recovered`
- `death` when an epidemic causes mortality

## Validation and tests

The Stage 8 test suite covers:

- bounded disease state and health values
- outbreak introduction
- transmission through social contacts
- recovery and immunity
- epidemic deaths contributing to deaths
- seeded reproducibility
- world-state validation

## Deliberate limitations

This is intentionally a bounded sandbox model, not a clinical epidemiology simulator. It does not currently model pathogen strains, vaccination, medical capacity, incubation curves, seasonality, mutation, or public-health interventions.

Those features belong to later experimentation only if they improve emergent behavior without turning CIVITAS into a scripted strategy system.
