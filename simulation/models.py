"""Core data models for the CIVITAS simulation."""

from dataclasses import dataclass, field
from enum import Enum


class Occupation(str, Enum):
    FARMER = "farmer"
    HUNTER = "hunter"
    BUILDER = "builder"
    TRADER = "trader"


@dataclass
class Resources:
    food: float = 100.0
    wood: float = 100.0
    stone: float = 50.0

    def consume_food(self, amount: float) -> bool:
        if amount <= self.food:
            self.food -= amount
            return True
        return False


@dataclass
class Agent:
    id: int
    age: int
    health: float = 100.0
    hunger: float = 0.0
    wealth: float = 10.0
    trust: float = 50.0
    occupation: Occupation = Occupation.FARMER
    village_id: int = 1
    alive: bool = True


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
    events: list[str] = field(default_factory=list)

    @property
    def population(self) -> int:
        return sum(agent.alive for agent in self.agents.values())
