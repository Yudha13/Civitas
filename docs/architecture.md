# Architecture

## System Layers

CIVITAS is divided into independent layers.

### 1. Simulation Engine

Responsible for the rules of the simulated world.

Core responsibilities:

- world state
- agents
- resources
- occupations
- time progression
- interactions
- events

The engine must not depend on React, HTTP, WebSocket, or database implementation details.

### 2. Backend

FastAPI exposes the simulation to clients.

Responsibilities:

- simulation lifecycle
- read-only world state
- commands and events
- WebSocket updates
- persistence boundary

### 3. Frontend

React + TypeScript provides:

- world visualization
- simulation controls
- agent inspection
- charts
- event log

### 4. Persistence

PostgreSQL will store durable simulation metadata and selected historical state.

The first engine prototype may run entirely in memory.

## Data Flow

```
Simulation Tick
      ↓
World State Update
      ↓
Event Generation
      ↓
Backend
      ↓
WebSocket
      ↓
Browser
```

## Core Rule

The frontend observes the simulation. It does not own the simulation.

This separation keeps the model testable and allows future clients, such as a CLI or replay tool, to use the same engine.
