"""Core data models for the CIVITAS simulation."""

from dataclasses import dataclass, field
from enum import Enum


class Occupation(str, Enum):
    FARMER = "farmer"
    HUNTER = "hunter"
    BUILDER = "builder"
    TRADER = "trader"


class EventType(str, Enum):
    DAY_STARTED = "day_started"
    PRODUCTION = "production"
    CONSUMPTION = "consumption"
    DEATH = "death"
    DAY_SUMMARY = "day_summary"
    ECONOMY = "economy"
    TRADE = "trade"
    BIRTH = "birth"
    MIGRATION = "migration"
    SOCIAL = "social"
    CONFLICT = "conflict"
    FACTION_FORMED = "faction_formed"
    FACTION_JOINED = "faction_joined"
    FACTION_LEADER_CHANGED = "faction_leader_changed"
    ENVIRONMENTAL_DISASTER = "environmental_disaster"
    WAR_STARTED = "war_started"
    WAR_RESOLVED = "war_resolved"


@dataclass(frozen=True)
class Event:
    day: int
    type: EventType
    message: str
    agent_id: int | None = None
    village_id: int | None = None
    amount: float | None = None


@dataclass
class Relationship:
    agent_a: int
    agent_b: int
    trust: float = 50.0
    interactions: int = 0


@dataclass
class Resources:
    food: float = 100.0
    wood: float = 100.0
    stone: float = 50.0

    def consume_food(self, amount: float) -> bool:
        if amount < 0:
            raise ValueError("Food consumption cannot be negative.")
        if amount <= self.food:
            self.food -= amount
            return True
        return False


@dataclass
class Agent:
    id: int
    age: float
    health: float = 100.0
    hunger: float = 0.0
    wealth: float = 10.0
    trust: float = 50.0
    occupation: Occupation = Occupation.FARMER
    village_id: int = 1
    alive: bool = True
    fertility: float = 1.0
    faction_id: int | None = None


@dataclass
class Faction:
    id: int
    name: str
    leader_id: int
    members: list[int] = field(default_factory=list)
    cohesion: float = 0.0


@dataclass
class Village:
    id: int
    name: str
    resources: Resources = field(default_factory=Resources)
    agents: list[int] = field(default_factory=list)


@dataclass
class World:
    day: int = 0
    agents: dict[int, Agent] = field(default_factory=dict)
    villages: dict[int, Village] = field(default_factory=dict)
    relationships: dict[tuple[int, int], Relationship] = field(default_factory=dict)
    factions: dict[int, Faction] = field(default_factory=dict)
    events: list[Event] = field(default_factory=list)

    @property
    def population(self) -> int:
        return sum(agent.alive for agent in self.agents.values())

    def validate(self, validate_relationships: bool = True) -> None:
        """Raise ValueError when the world contains an invalid simulation state."""
        if self.day < 0:
            raise ValueError("World day cannot be negative.")

        for village in self.villages.values():
            if village.resources.food < 0 or village.resources.wood < 0 or village.resources.stone < 0:
                raise ValueError(f"Village {village.id} has negative resources.")

        for agent in self.agents.values():
            if agent.age < 0:
                raise ValueError(f"Agent {agent.id} has negative age.")
            if agent.health < 0 or agent.health > 100:
                raise ValueError(f"Agent {agent.id} has invalid health.")
            if agent.hunger < 0 or agent.hunger > 100:
                raise ValueError(f"Agent {agent.id} has invalid hunger.")
            if agent.trust < 0 or agent.trust > 100:
                raise ValueError(f"Agent {agent.id} has invalid trust.")
            if agent.wealth < 0:
                raise ValueError(f"Agent {agent.id} has negative wealth.")
            if agent.fertility < 0:
                raise ValueError(f"Agent {agent.id} has negative fertility.")
            if agent.village_id not in self.villages:
                raise ValueError(f"Agent {agent.id} references an unknown village.")
            if agent.id not in self.villages[agent.village_id].agents:
                raise ValueError(f"Agent {agent.id} is missing from its village roster.")


        if validate_relationships:
            for key, relationship in self.relationships.items():
                if key != (relationship.agent_a, relationship.agent_b):
                    raise ValueError("Relationship key does not match its agents.")
                if relationship.agent_a >= relationship.agent_b:
                    raise ValueError("Relationship agent ids must be ordered.")
                if relationship.agent_a not in self.agents or relationship.agent_b not in self.agents:
                    raise ValueError("Relationship references an unknown agent.")
                if relationship.trust < 0 or relationship.trust > 100:
                    raise ValueError("Relationship trust must be between 0 and 100.")
                if relationship.interactions < 0:
                    raise ValueError("Relationship interactions cannot be negative.")
            for faction in self.factions.values():
                if faction.leader_id not in self.agents:
                    raise ValueError("Faction leader references an unknown agent.")
                if faction.leader_id not in faction.members:
                    raise ValueError("Faction leader must be a faction member.")
                if faction.cohesion < 0 or faction.cohesion > 100:
                    raise ValueError("Faction cohesion must be between 0 and 100.")
                if len(faction.members) != len(set(faction.members)):
                    raise ValueError("Faction contains duplicate members.")
                for member_id in faction.members:
                    if member_id not in self.agents:
                        raise ValueError("Faction references an unknown agent.")
                    if self.agents[member_id].faction_id != faction.id:
                        raise ValueError("Agent faction membership is inconsistent.")
