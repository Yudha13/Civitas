"""FastAPI application for the CIVITAS simulation."""
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
import os
from simulation.engine import Simulation
from backend.auth import require_user, verify_google_credential

app = FastAPI(title="CIVITAS API", version="0.2.0")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("CIVITAS_SESSION_SECRET", "civitas-development-session-secret"),
    same_site="lax",
    https_only=os.getenv("CIVITAS_COOKIE_SECURE", "0") == "1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SimulationConfig(BaseModel):
    seed: int = 1
    population: int = Field(default=100, ge=0)

class RunRequest(BaseModel):
    days: int = Field(ge=0)

class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1)

simulation = Simulation()

def _world_state() -> dict:
    world = simulation.world
    return {
        "day": world.day,
        "population": world.population,
        "villages": [
            {"id": v.id, "name": v.name, "agents": len([i for i in v.agents if world.agents[i].alive]),
             "food": v.resources.food, "wood": v.resources.wood, "stone": v.resources.stone}
            for v in world.villages.values()
        ],
        "factions": [
            {"id": f.id, "name": f.name, "leader_id": f.leader_id, "members": list(f.members), "cohesion": f.cohesion}
            for f in world.factions.values()
        ],
    }

def _agent_state(agent_id: int) -> dict:
    world = simulation.world
    agent = world.agents[agent_id]
    village = world.villages[agent.village_id]
    faction = world.factions.get(agent.faction_id) if agent.faction_id is not None else None
    return {"id": agent.id, "age": agent.age, "health": agent.health, "hunger": agent.hunger,
            "wealth": agent.wealth, "trust": agent.trust, "occupation": agent.occupation.value,
            "village_id": agent.village_id, "village_name": village.name, "alive": agent.alive,
            "fertility": agent.fertility, "faction_id": agent.faction_id,
            "faction_name": faction.name if faction else None}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/auth/google")
def google_login(payload: GoogleLoginRequest, request: Request) -> dict:
    user = verify_google_credential(payload.credential)
    request.session["user"] = {
        "subject": user.subject,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
    return request.session["user"]

@app.get("/auth/me")
def me(request: Request) -> dict:
    return require_user(request)

@app.post("/auth/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"status": "ok"}


@app.post("/simulation/start")
def start(config: SimulationConfig, request: Request) -> dict:
    require_user(request)
    global simulation
    simulation = Simulation(seed=config.seed, population=config.population)
    return _world_state()

@app.post("/simulation/tick")
def tick(request: Request) -> dict:
    require_user(request)
    simulation.tick()
    return _world_state()

@app.post("/simulation/run")
def run(request: RunRequest) -> dict:
    require_user(request)
    simulation.run(request.days)
    return _world_state()

@app.get("/simulation/state")
def state(request: Request) -> dict:
    require_user(request)
    return _world_state()

@app.get("/simulation/metrics")
def metrics(request: Request) -> dict:
    require_user(request)
    return simulation.metrics().__dict__

@app.get("/simulation/metrics/history")
def metrics_history(request: Request, limit: int = 365) -> list[dict]:
    require_user(request)
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 5000")
    return [snapshot.__dict__ for snapshot in simulation.metrics_history[-limit:]]

@app.get("/simulation/agents")
def agents(request: Request, limit: int = 200) -> list[dict]:
    require_user(request)
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    agent_ids = sorted(simulation.world.agents)[:limit]
    return [_agent_state(agent_id) for agent_id in agent_ids]

@app.websocket("/simulation/ws")
async def simulation_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    if websocket.session.get("user") is None:
        await websocket.close(code=4401)
        return
    try:
        while True:
            command = await websocket.receive_json()
            action = command.get("action", "state")
            if action == "tick":
                simulation.tick()
            elif action == "run":
                days = command.get("days", 1)
                if not isinstance(days, int) or days < 0:
                    await websocket.send_json({"error": "days must be a non-negative integer"})
                    continue
                simulation.run(days)
            elif action == "state":
                pass
            else:
                await websocket.send_json({"error": f"unknown action: {action}"})
                continue
            await websocket.send_json({"action": action, "state": _world_state(), "metrics": simulation.metrics().__dict__})
    except WebSocketDisconnect:
        return

@app.get("/simulation/events")
def events(request: Request, limit: int = 100) -> list[dict]:
    require_user(request)
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    return [event.__dict__ for event in simulation.world.events[-limit:]]
