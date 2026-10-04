"""FastAPI application for the CIVITAS simulation."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from simulation.engine import Simulation

app = FastAPI(title="CIVITAS API", version="0.1.0")


class SimulationConfig(BaseModel):
    seed: int = 1
    population: int = Field(default=100, ge=0)


class RunRequest(BaseModel):
    days: int = Field(ge=0)


simulation = Simulation()


def _world_state() -> dict:
    world = simulation.world
    return {
        "day": world.day,
        "population": world.population,
        "villages": [
            {
                "id": village.id,
                "name": village.name,
                "agents": len(
                    [agent_id for agent_id in village.agents if world.agents[agent_id].alive]
                ),
                "food": village.resources.food,
                "wood": village.resources.wood,
                "stone": village.resources.stone,
            }
            for village in world.villages.values()
        ],
        "factions": [
            {
                "id": faction.id,
                "name": faction.name,
                "leader_id": faction.leader_id,
                "members": list(faction.members),
                "cohesion": faction.cohesion,
            }
            for faction in world.factions.values()
        ],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/simulation/start")
def start(config: SimulationConfig) -> dict:
    global simulation
    simulation = Simulation(seed=config.seed, population=config.population)
    return _world_state()


@app.post("/simulation/tick")
def tick() -> dict:
    simulation.tick()
    return _world_state()


@app.post("/simulation/run")
def run(request: RunRequest) -> dict:
    simulation.run(request.days)
    return _world_state()


@app.get("/simulation/state")
def state() -> dict:
    return _world_state()


@app.get("/simulation/metrics")
def metrics() -> dict:
    return simulation.metrics().__dict__


@app.get("/simulation/events")
def events(limit: int = 100) -> list[dict]:
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    return [event.__dict__ for event in simulation.world.events[-limit:]]
