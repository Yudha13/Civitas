"""Persistence repository for CIVITAS domain state."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.db_models import (
    AgentRecord,
    EventRecord,
    FactionRecord,
    MetricRecord,
    RelationshipRecord,
    SimulationRecord,
    User,
    VillageRecord,
)
from simulation.engine import Metrics, Simulation
from simulation.models import Agent, Event, EventType, Faction, Occupation, Relationship, Resources, Village, World


def _encode_rng_state(simulation: Simulation) -> str:
    return json.dumps(simulation.rng.getstate())


def _decode_rng_state(value: str):
    def restore(item):
        if isinstance(item, list):
            return tuple(restore(child) for child in item)
        return item

    return restore(json.loads(value))


class SimulationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_user(self, subject, email=None, name=None, picture=None):
        user = self.session.scalar(select(User).where(User.google_sub == subject))
        now = datetime.now(timezone.utc)
        if user is None:
            user = User(
                google_sub=subject,
                email=email,
                name=name,
                avatar_url=picture,
                created_at=now,
                last_login_at=now,
            )
            self.session.add(user)
        else:
            user.email, user.name, user.avatar_url, user.last_login_at = email, name, picture, now
        self.session.commit()
        return user

    def create_simulation(self, user_id: int, simulation: Simulation, name="Untitled Simulation"):
        record = SimulationRecord(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            seed=simulation.seed,
            population=simulation.world.population,
            initial_population=simulation.world.population,
            rng_state=_encode_rng_state(simulation),
            engine_version="0.1.0",
            status="active",
            current_day=simulation.world.day,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(record)
        self.session.flush()
        self.save_state(record.id, simulation, commit=False)
        self.session.commit()
        return record

    def save_state(self, simulation_id: str, simulation: Simulation, commit=True):
        record = self.session.get(SimulationRecord, simulation_id)
        if record is None:
            raise ValueError("Simulation record not found")
        record.current_day = simulation.world.day
        record.population = simulation.world.population
        record.rng_state = _encode_rng_state(simulation)
        record.updated_at = datetime.now(timezone.utc)
        self._replace_villages(record.id, simulation)
        self._replace_agents(record.id, simulation)
        self._replace_factions(record.id, simulation)
        self._replace_relationships(record.id, simulation)
        self._upsert_metrics(record.id, simulation)
        self._upsert_events(record.id, simulation)
        if commit:
            self.session.commit()
        return record

    def list_simulations(self, user_id):
        return list(
            self.session.scalars(
                select(SimulationRecord)
                .where(SimulationRecord.user_id == user_id)
                .order_by(SimulationRecord.created_at.desc())
            )
        )

    def get_simulation(self, user_id, simulation_id):
        return self.session.scalar(
            select(SimulationRecord).where(
                SimulationRecord.id == simulation_id,
                SimulationRecord.user_id == user_id,
            )
        )

    def load_simulation(self, user_id: int, simulation_id: str) -> Simulation:
        record = self.get_simulation(user_id, simulation_id)
        if record is None:
            raise ValueError("Simulation not found")

        simulation = Simulation(seed=record.seed, population=record.initial_population)
        world = World(day=record.current_day)

        village_records = list(
            self.session.scalars(
                select(VillageRecord)
                .where(VillageRecord.simulation_id == simulation_id)
                .order_by(VillageRecord.village_id)
            )
        )
        for row in village_records:
            world.villages[row.village_id] = Village(
                id=row.village_id,
                name=row.name,
                resources=Resources(food=row.food, wood=row.wood, stone=row.stone),
            )

        agent_records = list(
            self.session.scalars(
                select(AgentRecord)
                .where(AgentRecord.simulation_id == simulation_id)
                .order_by(AgentRecord.agent_id)
            )
        )
        for row in agent_records:
            world.agents[row.agent_id] = Agent(
                id=row.agent_id,
                age=row.age,
                health=row.health,
                hunger=row.hunger,
                wealth=row.wealth,
                trust=row.trust,
                occupation=Occupation(row.occupation),
                village_id=row.village_id,
                alive=row.alive,
                fertility=row.fertility,
                faction_id=row.faction_id,
                disease_days=row.disease_days,
                immune=row.immune,
            )

        village_orders = {row.village_id: row.agent_order for row in village_records}
        for village in world.villages.values():
            stored_order = village_orders.get(village.id)
            if stored_order:
                village.agents = [agent_id for agent_id in json.loads(stored_order) if agent_id in world.agents]
            else:
                village.agents = sorted(
                    agent_id for agent_id, agent in world.agents.items() if agent.village_id == village.id
                )

        faction_records = list(
            self.session.scalars(
                select(FactionRecord)
                .where(FactionRecord.simulation_id == simulation_id)
                .order_by(FactionRecord.faction_id)
            )
        )
        for row in faction_records:
            world.factions[row.faction_id] = Faction(
                id=row.faction_id,
                name=row.name,
                leader_id=row.leader_id,
                members=json.loads(row.members),
                cohesion=row.cohesion,
            )

        relationship_records = list(
            self.session.scalars(
                select(RelationshipRecord)
                .where(RelationshipRecord.simulation_id == simulation_id)
                .order_by(RelationshipRecord.agent_a, RelationshipRecord.agent_b)
            )
        )
        for row in relationship_records:
            relationship = Relationship(
                agent_a=row.agent_a,
                agent_b=row.agent_b,
                trust=row.trust,
                interactions=row.interactions,
            )
            world.relationships[(row.agent_a, row.agent_b)] = relationship

        event_records = list(
            self.session.scalars(
                select(EventRecord)
                .where(EventRecord.simulation_id == simulation_id)
                .order_by(EventRecord.id)
            )
        )
        world.events = [
            Event(
                day=row.day,
                type=EventType(row.event_type),
                message=row.message,
                agent_id=row.agent_id,
                village_id=row.village_id,
                amount=row.amount,
            )
            for row in event_records
        ]

        metric_records = list(
            self.session.scalars(
                select(MetricRecord)
                .where(MetricRecord.simulation_id == simulation_id)
                .order_by(MetricRecord.day)
            )
        )
        simulation.world = world
        simulation.metrics_history = [
            Metrics(
                day=row.day,
                population=row.population,
                living_population=row.living_population,
                average_health=row.average_health,
                average_hunger=row.average_hunger,
                total_food=row.total_food,
                total_wood=row.total_wood,
                total_stone=row.total_stone,
                total_wealth=row.total_wealth,
                average_wealth=row.average_wealth,
                average_trust=row.average_trust,
                trade_volume=row.trade_volume,
                births=row.births,
                deaths=row.deaths,
                migrations=row.migrations,
                social_interactions=row.social_interactions,
                conflicts=row.conflicts,
                faction_count=row.faction_count,
                average_faction_cohesion=row.average_faction_cohesion,
                wealth_gini=row.wealth_gini,
                top_10_wealth_share=row.top_10_wealth_share,
                political_pressure=row.political_pressure,
                environmental_disasters=row.environmental_disasters,
                wars=row.wars,
                war_casualties=row.war_casualties,
                epidemics=row.epidemics,
                epidemic_infections=row.epidemic_infections,
                epidemic_deaths=row.epidemic_deaths,
            )
            for row in metric_records
        ]
        if not simulation.metrics_history:
            simulation.metrics_history = [simulation.metrics()]

        if record.rng_state:
            simulation.rng.setstate(_decode_rng_state(record.rng_state))
        else:
            simulation.run(record.current_day)

        world.validate()
        return simulation

    def _replace_villages(self, sid, sim):
        self.session.query(VillageRecord).filter(VillageRecord.simulation_id == sid).delete()
        for v in sim.world.villages.values():
            self.session.add(
                VillageRecord(
                    simulation_id=sid,
                    village_id=v.id,
                    name=v.name,
                    food=v.resources.food,
                    wood=v.resources.wood,
                    stone=v.resources.stone,
                    agent_order=json.dumps(v.agents),
                )
            )

    def _replace_agents(self, sid, sim):
        self.session.query(AgentRecord).filter(AgentRecord.simulation_id == sid).delete()
        for a in sim.world.agents.values():
            self.session.add(
                AgentRecord(
                    simulation_id=sid,
                    agent_id=a.id,
                    village_id=a.village_id,
                    age=a.age,
                    health=a.health,
                    hunger=a.hunger,
                    wealth=a.wealth,
                    trust=a.trust,
                    occupation=a.occupation.value,
                    alive=a.alive,
                    fertility=a.fertility,
                    faction_id=a.faction_id,
                    disease_days=a.disease_days,
                    immune=a.immune,
                )
            )

    def _replace_factions(self, sid, sim):
        self.session.query(FactionRecord).filter(FactionRecord.simulation_id == sid).delete()
        for f in sim.world.factions.values():
            self.session.add(
                FactionRecord(
                    simulation_id=sid,
                    faction_id=f.id,
                    name=f.name,
                    leader_id=f.leader_id,
                    cohesion=f.cohesion,
                    members=json.dumps(f.members),
                )
            )

    def _replace_relationships(self, sid, sim):
        self.session.query(RelationshipRecord).filter(RelationshipRecord.simulation_id == sid).delete()
        for r in sim.world.relationships.values():
            self.session.add(
                RelationshipRecord(
                    simulation_id=sid,
                    agent_a=r.agent_a,
                    agent_b=r.agent_b,
                    trust=r.trust,
                    interactions=r.interactions,
                )
            )

    def _upsert_metrics(self, sid, sim):
        for metric in sim.metrics_history:
            values = metric.__dict__
            existing = self.session.scalar(
                select(MetricRecord).where(
                    MetricRecord.simulation_id == sid,
                    MetricRecord.day == metric.day,
                )
            )
            if existing is None:
                self.session.add(MetricRecord(simulation_id=sid, **values))
            else:
                for key, value in values.items():
                    setattr(existing, key, value)

    def _upsert_events(self, sid, sim):
        existing_count = self.session.scalar(
            select(func.count()).select_from(EventRecord).where(EventRecord.simulation_id == sid)
        ) or 0
        for event in sim.world.events[existing_count:]:
            self.session.add(
                EventRecord(
                    simulation_id=sid,
                    day=event.day,
                    event_type=event.type.value,
                    message=event.message,
                    agent_id=event.agent_id,
                    village_id=event.village_id,
                    amount=event.amount,
                )
            )
