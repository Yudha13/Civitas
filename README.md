# CIVITAS

> An agent-based civilization simulation running in the browser.

CIVITAS is a web-based sandbox for observing how a small society changes over time under interacting rules for population, resources, economy, social trust, migration, conflict, and environmental pressure.

The simulation does not prescribe a fixed story. It defines rules and initial conditions, then observes the consequences.

## Vision

CIVITAS aims to become a laboratory for emergent social behavior:

- agents make local decisions
- resources are produced and consumed
- communities form and change
- cooperation and conflict emerge
- shocks can destabilize a society
- civilizations may adapt, stagnate, fragment, or collapse

## MVP

The first playable version targets:

- 3 villages
- 100–500 agents
- Food, Wood, and Stone
- Farmer, Hunter, Builder, and Trader occupations
- production and consumption
- birth and death
- migration and trade
- basic social trust
- simulation controls
- event log
- basic charts
- browser-based visualization

## Architecture

```
Browser
  │
  ├── React + TypeScript
  │
  └── REST / WebSocket
          │
       FastAPI
          │
   Simulation Engine
          │
      PostgreSQL
```

The simulation engine remains independent from the frontend so it can be tested and executed without the browser.

## Development Order

1. World model
2. Agent model
3. Resources
4. Occupations
5. Daily simulation tick
6. Economy
7. Social interaction
8. Villages
9. Events
10. API
11. Web interface
12. Persistence and analytics

## Design Principle

Start small. A stable simulation of 500 agents is more valuable than a grand design containing 50 systems that cannot survive their first tick.

## Status

Early development — architecture and simulation model are being established.
