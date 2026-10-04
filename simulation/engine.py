"""Deterministic, dependency-free CIVITAS simulation engine."""

from dataclasses import dataclass
from random import Random

from .models import Agent, Event, EventType, Occupation, Village, World


@dataclass(frozen=True)
class Metrics:
    """Snapshot of the most important world-level indicators."""

    day: int
    population: int
    living_population: int
    average_health: float
    average_hunger: float
    total_food: float
    total_wood: float
    total_stone: float
    total_wealth: float
    average_wealth: float
    trade_volume: float


class Simulation:
    """Advance a CIVITAS world one deterministic day at a time."""

    FOOD_PER_DAY = 1.0

    def __init__(self, seed: int = 1, population: int = 100) -> None:
        if population < 0:
            raise ValueError("Population cannot be negative.")

        self.rng = Random(seed)
        self.seed = seed
        self.world = self._create_world(population)
        self.metrics_history: list[Metrics] = [self.metrics()]
        self.world.validate()

    def _create_world(self, population: int) -> World:
        world = World()
        for village_id, name in enumerate(("North", "Central", "South"), start=1):
            world.villages[village_id] = Village(village_id, name)

        occupations = list(Occupation)
        for agent_id in range(1, population + 1):
            village_id = ((agent_id - 1) % 3) + 1
            occupation = occupations[(agent_id - 1) % len(occupations)]
            agent = Agent(
                id=agent_id,
                age=self.rng.randint(18, 55),
                occupation=occupation,
                village_id=village_id,
            )
            world.agents[agent_id] = agent
            world.villages[village_id].agents.append(agent_id)
        return world

    def tick(self) -> World:
        """Advance the simulation by one deterministic day."""
        self.world.day += 1
        self._emit(EventType.DAY_STARTED, f"Day {self.world.day} started")

        self._production_phase()
        self._economy_phase()
        self._trade_phase()
        self._consumption_phase()

        self._emit(
            EventType.DAY_SUMMARY,
            f"Day {self.world.day}: population={self.world.population}",
        )
        self.world.validate()
        self.metrics_history.append(self.metrics())
        return self.world

    def run(self, days: int) -> World:
        if days < 0:
            raise ValueError("Days cannot be negative.")

        for _ in range(days):
            self.tick()
        return self.world

    def metrics(self) -> Metrics:
        """Return a point-in-time snapshot without mutating the simulation."""
        agents = list(self.world.agents.values())
        living = [agent for agent in agents if agent.alive]
        living_count = len(living)

        average_health = (
            sum(agent.health for agent in living) / living_count
            if living_count
            else 0.0
        )
        average_hunger = (
            sum(agent.hunger for agent in living) / living_count
            if living_count
            else 0.0
        )

        return Metrics(
            day=self.world.day,
            population=len(agents),
            living_population=living_count,
            average_health=average_health,
            average_hunger=average_hunger,
            total_food=sum(v.resources.food for v in self.world.villages.values()),
            total_wood=sum(v.resources.wood for v in self.world.villages.values()),
            total_stone=sum(v.resources.stone for v in self.world.villages.values()),
            total_wealth=sum(agent.wealth for agent in living),
            average_wealth=(sum(agent.wealth for agent in living) / living_count if living_count else 0.0),
            trade_volume=sum(
                event.amount or 0.0
                for event in self.world.events
                if event.type == EventType.TRADE and event.day == self.world.day
            ),
        )

    def _production_phase(self) -> None:
        for village in self.world.villages.values():
            self._produce(village)

    def _economy_phase(self) -> None:
        for agent in self.world.agents.values():
            if not agent.alive:
                continue

            income = {
                Occupation.FARMER: 0.5,
                Occupation.HUNTER: 0.5,
                Occupation.BUILDER: 0.75,
                Occupation.TRADER: 1.0,
            }[agent.occupation]
            agent.wealth += income
            self._emit(
                EventType.ECONOMY,
                f"Agent {agent.id}: +{income:g} wealth",
                agent_id=agent.id,
                village_id=agent.village_id,
            )

    def _trade_phase(self) -> None:
        """Move surplus food between villages through local traders."""
        target_per_agent = 2.0
        surplus = {}
        deficit = {}

        for village in self.world.villages.values():
            living = sum(
                1 for agent_id in village.agents if self.world.agents[agent_id].alive
            )
            target = living * target_per_agent
            balance = village.resources.food - target
            if balance >= 1.0:
                surplus[village.id] = balance
            elif balance < 0:
                deficit[village.id] = -balance

        if not surplus or not deficit:
            return

        sellers = {
            village_id: self._find_trader(village_id)
            for village_id in surplus
        }
        buyers = {
            village_id: self._find_trader(village_id)
            for village_id in deficit
        }

        for seller_id, seller_balance in surplus.items():
            seller = sellers[seller_id]
            if seller is None:
                continue

            for buyer_id in deficit:
                buyer = buyers[buyer_id]
                if buyer is None:
                    continue

                amount = min(seller_balance, deficit[buyer_id], 5.0, buyer.wealth)
                if amount <= 0:
                    continue

                self.world.villages[seller_id].resources.food -= amount
                self.world.villages[buyer_id].resources.food += amount
                buyer.wealth -= amount
                seller.wealth += amount
                seller_balance -= amount
                deficit[buyer_id] -= amount

                self._emit(
                    EventType.TRADE,
                    f"{amount:g} food traded from village {seller_id} to village {buyer_id}",
                    village_id=buyer_id,
                    amount=amount,
                )

                if seller_balance < 1.0:
                    break

    def _find_trader(self, village_id: int) -> Agent | None:
        traders = [
            self.world.agents[agent_id]
            for agent_id in self.world.villages[village_id].agents
            if self.world.agents[agent_id].alive
            and self.world.agents[agent_id].occupation == Occupation.TRADER
        ]
        return max(traders, key=lambda agent: agent.wealth, default=None)

    def _consumption_phase(self) -> None:
        for agent in list(self.world.agents.values()):
            if agent.alive:
                self._consume_and_age(agent)

    def _emit(
        self,
        event_type: EventType,
        message: str,
        agent_id: int | None = None,
        village_id: int | None = None,
        amount: float | None = None,
    ) -> None:
        self.world.events.append(
            Event(
                day=self.world.day,
                type=event_type,
                message=message,
                agent_id=agent_id,
                village_id=village_id,
                amount=amount,
            )
        )

    def _produce(self, village: Village) -> None:
        counts = {occupation: 0 for occupation in Occupation}
        for agent_id in village.agents:
            agent = self.world.agents[agent_id]
            if agent.alive:
                counts[agent.occupation] += 1

        food_produced = (
            counts[Occupation.FARMER] * 3.0
            + counts[Occupation.HUNTER] * 2.0
        )
        wood_produced = counts[Occupation.BUILDER] * 1.0
        stone_produced = counts[Occupation.BUILDER] * 0.5

        village.resources.food += food_produced
        village.resources.wood += wood_produced
        village.resources.stone += stone_produced

        self._emit(
            EventType.PRODUCTION,
            f"{village.name}: +{food_produced:g} food, +{wood_produced:g} wood, +{stone_produced:g} stone",
            village_id=village.id,
        )

    def _consume_and_age(self, agent: Agent) -> None:
        village = self.world.villages[agent.village_id]
        fed = village.resources.consume_food(self.FOOD_PER_DAY)
        agent.age += 1 / 365

        if fed:
            agent.hunger = max(0.0, agent.hunger - 20.0)
            agent.health = min(100.0, agent.health + 0.5)
        else:
            agent.hunger = min(100.0, agent.hunger + 25.0)
            agent.health = max(0.0, agent.health - 5.0)
            self._emit(
                EventType.CONSUMPTION,
                f"Agent {agent.id} was not fed",
                agent_id=agent.id,
                village_id=agent.village_id,
            )

        if agent.health <= 0:
            agent.alive = False
            self._emit(
                EventType.DEATH,
                f"Agent {agent.id} died",
                agent_id=agent.id,
                village_id=agent.village_id,
            )
