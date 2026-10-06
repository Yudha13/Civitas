"""FastAPI application for the CIVITAS simulation."""
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel, Field
import os
from simulation.engine import Simulation
from backend.database import SessionLocal, get_session
from backend.repository import SimulationRepository
from sqlalchemy.orm import Session
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

class SimulationCreateRequest(SimulationConfig):
    name: str = "Untitled Simulation"

simulation = Simulation()
active_simulations: dict[int, Simulation] = {}

def _world_state(sim: Simulation | None = None) -> dict:
    sim = sim or simulation
    world = sim.world
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

def _agent_state(agent_id: int, sim: Simulation | None = None) -> dict:
    sim = sim or simulation
    world = sim.world
    agent = world.agents[agent_id]
    village = world.villages[agent.village_id]
    faction = world.factions.get(agent.faction_id) if agent.faction_id is not None else None
    return {"id": agent.id, "age": agent.age, "health": agent.health, "hunger": agent.hunger,
            "wealth": agent.wealth, "trust": agent.trust, "occupation": agent.occupation.value,
            "village_id": agent.village_id, "village_name": village.name, "alive": agent.alive,
            "fertility": agent.fertility, "faction_id": agent.faction_id,
            "faction_name": faction.name if faction else None, "ideology": agent.ideology.value, "ideology_commitment": agent.ideology_commitment}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/auth/google")
def google_login(payload: GoogleLoginRequest, request: Request, db: Session = Depends(get_session)) -> dict:
    user = verify_google_credential(payload.credential)
    record = SimulationRepository(db).upsert_user(user.subject, user.email, user.name, user.picture)
    request.session["user"] = {
        "subject": user.subject,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
        "user_id": record.id,
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
def start(config: SimulationCreateRequest, request: Request, db: Session = Depends(get_session)) -> dict:
    user = require_user(request)
    global simulation
    simulation = Simulation(seed=config.seed, population=config.population)
    user_id = int(user["user_id"])
    active_simulations[user_id] = simulation
    record = SimulationRepository(db).create_simulation(user_id, simulation, config.name)
    request.session["simulation_id"] = record.id
    return _world_state(simulation)

@app.post("/simulation/tick")
def tick(request: Request, db: Session = Depends(get_session)) -> dict:
    user = require_user(request)
    sim = active_simulations.get(int(user["user_id"]))
    if sim is None:
        raise HTTPException(status_code=404, detail="No active simulation")
    sim.tick()
    SimulationRepository(db).save_state(request.session["simulation_id"], sim)
    return _world_state(sim)

@app.post("/simulation/run")
def run(payload: RunRequest, request: Request, db: Session = Depends(get_session)) -> dict:
    user = require_user(request)
    sim = active_simulations.get(int(user["user_id"]))
    if sim is None:
        raise HTTPException(status_code=404, detail="No active simulation")
    sim.run(payload.days)
    SimulationRepository(db).save_state(request.session["simulation_id"], sim)
    return _world_state(sim)

@app.get("/simulation/state")
def state(request: Request) -> dict:
    user = require_user(request)
    return _world_state(active_simulations.get(int(user["user_id"])))

@app.get("/simulation/metrics")
def metrics(request: Request) -> dict:
    user = require_user(request)
    sim = active_simulations.get(int(user["user_id"])) or simulation
    return sim.metrics().__dict__

@app.get("/simulation/metrics/history")
def metrics_history(request: Request, limit: int = 365) -> list[dict]:
    user = require_user(request)
    sim = active_simulations.get(int(user["user_id"])) or simulation
    if limit < 1 or limit > 5000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 5000")
    return [snapshot.__dict__ for snapshot in sim.metrics_history[-limit:]]

@app.get("/simulation/agents")
def agents(request: Request, limit: int = 200) -> list[dict]:
    user = require_user(request)
    sim = active_simulations.get(int(user["user_id"])) or simulation
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    agent_ids = sorted(sim.world.agents)[:limit]
    return [_agent_state(agent_id, sim) for agent_id in agent_ids]

@app.get("/simulations")
def list_simulations(request: Request, db: Session = Depends(get_session)) -> list[dict]:
    user = require_user(request)
    records = SimulationRepository(db).list_simulations(int(user["user_id"]))
    return [{"id": r.id, "name": r.name, "seed": r.seed, "population": r.population, "initial_population": r.initial_population, "current_day": r.current_day, "status": r.status, "created_at": r.created_at.isoformat()} for r in records]

@app.get("/simulations/{simulation_id}")
def get_simulation(simulation_id: str, request: Request, db: Session = Depends(get_session)) -> dict:
    user = require_user(request)
    record = SimulationRepository(db).get_simulation(int(user["user_id"]), simulation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"id": record.id, "name": record.name, "seed": record.seed, "population": record.population, "initial_population": record.initial_population, "current_day": record.current_day, "status": record.status, "engine_version": record.engine_version, "created_at": record.created_at.isoformat(), "updated_at": record.updated_at.isoformat()}


@app.post("/simulations/{simulation_id}/load")
def load_simulation(simulation_id: str, request: Request, db: Session = Depends(get_session)) -> dict:
    user = require_user(request)
    repo = SimulationRepository(db)
    try:
        loaded = repo.load_simulation(int(user["user_id"]), simulation_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    active_simulations[int(user["user_id"])] = loaded
    request.session["simulation_id"] = simulation_id
    return _world_state(loaded)

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
            user_id = int(websocket.session["user"]["user_id"])
            sim = active_simulations.get(user_id) or simulation
            if action == "tick":
                sim.tick()
            elif action == "run":
                days = command.get("days", 1)
                if not isinstance(days, int) or days < 0:
                    await websocket.send_json({"error": "days must be a non-negative integer"})
                    continue
                sim.run(days)
            elif action == "state":
                pass
            else:
                await websocket.send_json({"error": f"unknown action: {action}"})
                continue
            if action in {"tick", "run"} and websocket.session.get("simulation_id"):
                with SessionLocal() as db:
                    SimulationRepository(db).save_state(websocket.session["simulation_id"], sim)
            await websocket.send_json({"action": action, "state": _world_state(sim), "metrics": sim.metrics().__dict__})
    except WebSocketDisconnect:
        return

@app.get("/simulation/events")
def events(request: Request, limit: int = 100) -> list[dict]:
    user = require_user(request)
    sim = active_simulations.get(int(user["user_id"])) or simulation
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    return [event.__dict__ for event in sim.world.events[-limit:]]
