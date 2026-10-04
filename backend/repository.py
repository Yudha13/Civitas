"""Persistence repository for CIVITAS domain state."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.db_models import AgentRecord, EventRecord, FactionRecord, MetricRecord, RelationshipRecord, SimulationRecord, User, VillageRecord
from simulation.engine import Simulation

class SimulationRepository:
    def __init__(self, session: Session) -> None: self.session = session
    def upsert_user(self, subject, email=None, name=None, picture=None):
        user = self.session.scalar(select(User).where(User.google_sub == subject)); now = datetime.now(timezone.utc)
        if user is None:
            user = User(google_sub=subject,email=email,name=name,avatar_url=picture,created_at=now,last_login_at=now); self.session.add(user)
        else: user.email, user.name, user.avatar_url, user.last_login_at = email,name,picture,now
        self.session.commit(); return user
    def create_simulation(self, user_id: int, simulation: Simulation, name="Untitled Simulation"):
        record = SimulationRecord(id=str(uuid4()),user_id=user_id,name=name,seed=simulation.seed,population=simulation.world.population,engine_version="0.1.0",status="active",current_day=simulation.world.day,started_at=datetime.now(timezone.utc))
        self.session.add(record); self.session.flush(); self.save_state(record.id,simulation,commit=False); self.session.commit(); return record
    def save_state(self, simulation_id: str, simulation: Simulation, commit=True):
        record = self.session.get(SimulationRecord,simulation_id)
        if record is None: raise ValueError("Simulation record not found")
        record.current_day=simulation.world.day; record.population=simulation.world.population; record.updated_at=datetime.now(timezone.utc)
        self._replace_villages(record.id,simulation); self._replace_agents(record.id,simulation); self._replace_factions(record.id,simulation); self._replace_relationships(record.id,simulation); self._upsert_metrics(record.id,simulation); self._upsert_events(record.id,simulation)
        if commit: self.session.commit()
        return record
    def list_simulations(self,user_id): return list(self.session.scalars(select(SimulationRecord).where(SimulationRecord.user_id==user_id).order_by(SimulationRecord.created_at.desc())))
    def get_simulation(self,user_id,simulation_id): return self.session.scalar(select(SimulationRecord).where(SimulationRecord.id==simulation_id,SimulationRecord.user_id==user_id))
    def _replace_villages(self,sid,sim):
        self.session.query(VillageRecord).filter(VillageRecord.simulation_id==sid).delete()
        for v in sim.world.villages.values(): self.session.add(VillageRecord(simulation_id=sid,village_id=v.id,name=v.name,food=v.resources.food,wood=v.resources.wood,stone=v.resources.stone))
    def _replace_agents(self,sid,sim):
        self.session.query(AgentRecord).filter(AgentRecord.simulation_id==sid).delete()
        for a in sim.world.agents.values(): self.session.add(AgentRecord(simulation_id=sid,agent_id=a.id,village_id=a.village_id,age=a.age,health=a.health,hunger=a.hunger,wealth=a.wealth,trust=a.trust,occupation=a.occupation.value,alive=a.alive,fertility=a.fertility,faction_id=a.faction_id))
    def _replace_factions(self,sid,sim):
        self.session.query(FactionRecord).filter(FactionRecord.simulation_id==sid).delete()
        for f in sim.world.factions.values(): self.session.add(FactionRecord(simulation_id=sid,faction_id=f.id,name=f.name,leader_id=f.leader_id,cohesion=f.cohesion,members=json.dumps(f.members)))
    def _replace_relationships(self,sid,sim):
        self.session.query(RelationshipRecord).filter(RelationshipRecord.simulation_id==sid).delete()
        for r in sim.world.relationships.values(): self.session.add(RelationshipRecord(simulation_id=sid,agent_a=r.agent_a,agent_b=r.agent_b,trust=r.trust,interactions=r.interactions))
    def _upsert_metrics(self,sid,sim):
        for metric in sim.metrics_history:
            values=metric.__dict__; existing=self.session.scalar(select(MetricRecord).where(MetricRecord.simulation_id==sid,MetricRecord.day==metric.day))
            if existing is None: self.session.add(MetricRecord(simulation_id=sid,**values))
            else:
                for key,value in values.items(): setattr(existing,key,value)
    def _upsert_events(self,sid,sim):
        existing_count=self.session.scalar(select(func.count()).select_from(EventRecord).where(EventRecord.simulation_id==sid)) or 0
        for event in sim.world.events[existing_count:]:
            self.session.add(EventRecord(simulation_id=sid,day=event.day,event_type=event.type.value,message=event.message,agent_id=event.agent_id,village_id=event.village_id,amount=event.amount))
