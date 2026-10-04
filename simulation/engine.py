"""Deterministic, dependency-free CIVITAS simulation engine."""

from dataclasses import dataclass
from random import Random

from .models import Agent, Event, EventType, Faction, Occupation, Relationship, Village, World


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
    average_trust: float
    trade_volume: float
    births: int
    deaths: int
    migrations: int
    social_interactions: int
    conflicts: int
    faction_count: int
    average_faction_cohesion: float
    wealth_gini: float
    top_10_wealth_share: float


class Simulation:
    """Advance a CIVITAS world one deterministic day at a time."""

    FOOD_PER_DAY = 1.25
    WORKING_AGE = 16.0
    MIN_REPRODUCTIVE_AGE = 18.0
    MAX_REPRODUCTIVE_AGE = 45.0
    BIRTH_PROBABILITY = 0.015
    MIGRATION_PROBABILITY = 0.05
    MIGRATION_FOOD_GAP = 4.0
    SOCIAL_INTERACTION_PROBABILITY = 0.35
    SOCIAL_TRUST_STEP = 0.5
    DISPUTE_PROBABILITY = 0.08
    DISPUTE_TRUST_THRESHOLD = 25.0
    DISPUTE_SCARCITY_THRESHOLD = 1.0
    SOCIAL_MAX_PARTNERS = 4
    DISPUTE_MAX_RELATIONSHIPS = 256
    FACTION_TRUST_THRESHOLD = 55.0
    FACTION_MIN_INTERACTIONS = 3
    FACTION_MIN_SIZE = 3
    VALIDATION_INTERVAL = 30

    def __init__(self, seed: int = 1, population: int = 100) -> None:
        if population < 0:
            raise ValueError("Population cannot be negative.")

        self.rng = Random(seed)
        self.seed = seed
        self.world = self._create_world(population)
        self._daily_trade_volume = 0.0
        self._daily_births = 0
        self._daily_deaths = 0
        self._daily_migrations = 0
        self._daily_social_interactions = 0
        self._daily_conflicts = 0
        self.world.validate()
        self.metrics_history: list[Metrics] = [self.metrics()]

    def _create_world(self, population: int) -> World:
        world = World()
        for village_id, name in enumerate(("North", "Central", "South"), start=1):
            world.villages[village_id] = Village(village_id, name)

        occupations = list(Occupation)
        for agent_id in range(1, population + 1):
            village_id = ((agent_id - 1) % 3) + 1
            occupation = self.rng.choice(occupations)
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
        self._daily_trade_volume = 0.0
        self._daily_births = 0
        self._daily_deaths = 0
        self._daily_migrations = 0
        self._daily_social_interactions = 0
        self._daily_conflicts = 0
        self._emit(EventType.DAY_STARTED, f"Day {self.world.day} started")

        self._production_phase()
        self._economy_phase()
        self._trade_phase()
        self._consumption_phase()
        self._population_phase()
        self._social_phase()
        self._dispute_phase()
        self._faction_phase()
        self._faction_dynamics_phase()
        self._migration_phase()

        self._emit(
            EventType.DAY_SUMMARY,
            f"Day {self.world.day}: population={self.world.population}",
        )
        self.world.validate(validate_relationships=self.world.day % self.VALIDATION_INTERVAL == 0)
        self.metrics_history.append(self.metrics())
        return self.world

    def run(self, days: int) -> World:
        if days < 0:
            raise ValueError("Days cannot be negative.")

        for _ in range(days):
            self.tick()
        return self.world

    def metrics(self) -> Metrics:
        agents = list(self.world.agents.values())
        living = [agent for agent in agents if agent.alive]
        living_count = len(living)
        trust_values = [agent.trust for agent in living]

        faction_cohesions = [faction.cohesion for faction in self.world.factions.values()]

        return Metrics(
            day=self.world.day,
            population=living_count,
            living_population=living_count,
            average_health=(sum(agent.health for agent in living) / living_count if living_count else 0.0),
            average_hunger=(sum(agent.hunger for agent in living) / living_count if living_count else 0.0),
            total_food=sum(v.resources.food for v in self.world.villages.values()),
            total_wood=sum(v.resources.wood for v in self.world.villages.values()),
            total_stone=sum(v.resources.stone for v in self.world.villages.values()),
            total_wealth=sum(agent.wealth for agent in living),
            average_wealth=(sum(agent.wealth for agent in living) / living_count if living_count else 0.0),
            average_trust=(sum(trust_values) / len(trust_values) if trust_values else 0.0),
            trade_volume=self._daily_trade_volume,
            births=self._daily_births,
            deaths=self._daily_deaths,
            migrations=self._daily_migrations,
            social_interactions=self._daily_social_interactions,
            conflicts=self._daily_conflicts,
            faction_count=len(self.world.factions),
            average_faction_cohesion=(sum(faction_cohesions) / len(faction_cohesions) if faction_cohesions else 0.0),
        )

    def _is_working_age(self, agent: Agent) -> bool:
        return agent.age >= self.WORKING_AGE

    def _production_phase(self) -> None:
        for village in self.world.villages.values():
            self._produce(village)

    def _economy_phase(self) -> None:
        for agent in self.world.agents.values():
            if not agent.alive or not self._is_working_age(agent):
                continue
            income = {Occupation.FARMER: 0.5, Occupation.HUNTER: 0.5, Occupation.BUILDER: 0.75, Occupation.TRADER: 1.0}[agent.occupation]
            agent.wealth += income
            self._emit(EventType.ECONOMY, f"Agent {agent.id}: +{income:g} wealth", agent_id=agent.id, village_id=agent.village_id)

    def _trade_phase(self) -> None:
        target_per_agent = 2.0
        surplus = {}
        deficit = {}
        for village in self.world.villages.values():
            living = sum(1 for agent_id in village.agents if self.world.agents[agent_id].alive)
            balance = village.resources.food - living * target_per_agent
            if balance >= 1.0:
                surplus[village.id] = balance
            elif balance < 0:
                deficit[village.id] = -balance

        if not surplus or not deficit:
            return

        sellers = {village_id: self._find_trader(village_id) for village_id in surplus}
        buyers = {village_id: self._find_trader(village_id) for village_id in deficit}
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
                self._emit(EventType.TRADE, f"{amount:g} food traded from village {seller_id} to village {buyer_id}", village_id=buyer_id, amount=amount)
                if seller_balance < 1.0:
                    break

    def _find_trader(self, village_id: int) -> Agent | None:
        traders = [
            self.world.agents[agent_id]
            for agent_id in self.world.villages[village_id].agents
            if self.world.agents[agent_id].alive
            and self._is_working_age(self.world.agents[agent_id])
            and self.world.agents[agent_id].occupation == Occupation.TRADER
        ]
        return max(traders, key=lambda agent: agent.wealth, default=None)

    def _population_phase(self) -> None:
        living = [agent for agent in self.world.agents.values() if agent.alive]
        next_id = max(self.world.agents, default=0) + 1
        eligible = [agent for agent in living if self.MIN_REPRODUCTIVE_AGE <= agent.age <= self.MAX_REPRODUCTIVE_AGE]
        for parent in eligible:
            if self.rng.random() >= self.BIRTH_PROBABILITY * parent.fertility:
                continue
            village = self.world.villages[parent.village_id]
            child = Agent(id=next_id, age=0.0, health=100.0, hunger=0.0, wealth=parent.wealth * 0.25, trust=parent.trust, occupation=Occupation.FARMER, village_id=parent.village_id, alive=True, fertility=parent.fertility)
            parent.wealth *= 0.75
            self.world.agents[next_id] = child
            village.agents.append(next_id)
            self._emit(EventType.BIRTH, f"Agent {next_id} was born in {village.name}", agent_id=next_id, village_id=village.id)
            next_id += 1

    def _social_phase(self) -> None:
        """Create local pairwise interactions and update relationship trust."""
        for village in self.world.villages.values():
            living = sorted(
                agent_id for agent_id in village.agents
                if self.world.agents[agent_id].alive
            )
            for index, first_id in enumerate(living):
                candidates = living[index + 1:]
                if len(candidates) > self.SOCIAL_MAX_PARTNERS:
                    candidates = self.rng.sample(candidates, self.SOCIAL_MAX_PARTNERS)
                for second_id in candidates:
                    if self.rng.random() >= self.SOCIAL_INTERACTION_PROBABILITY:
                        continue

                    key = (first_id, second_id)
                    relationship = self.world.relationships.get(key)
                    if relationship is None:
                        relationship = Relationship(first_id, second_id)
                        self.world.relationships[key] = relationship

                    first = self.world.agents[first_id]
                    second = self.world.agents[second_id]
                    similarity = 1.0 if first.occupation == second.occupation else 0.0
                    wealth_gap = abs(first.wealth - second.wealth)
                    trust_delta = self.SOCIAL_TRUST_STEP * similarity - min(0.25, wealth_gap / 100.0)
                    relationship.trust = max(0.0, min(100.0, relationship.trust + trust_delta))
                    relationship.interactions += 1

                    first.trust = max(0.0, min(100.0, first.trust + trust_delta * 0.25))
                    second.trust = max(0.0, min(100.0, second.trust + trust_delta * 0.25))
                    self._emit(
                        EventType.SOCIAL,
                        f"Agents {first_id} and {second_id} interacted",
                        agent_id=first_id,
                        village_id=village.id,
                    )

    def _dispute_phase(self) -> None:
        """Create non-violent disputes when trust is low and food is scarce."""
        for village in self.world.villages.values():
            living = [agent_id for agent_id in village.agents if self.world.agents[agent_id].alive]
            scarcity = village.resources.food / max(len(living), 1)
            if scarcity > self.DISPUTE_SCARCITY_THRESHOLD:
                continue

            candidates = [
                relationship
                for relationship in self.world.relationships.values()
                if relationship.trust <= self.DISPUTE_TRUST_THRESHOLD
                and relationship.agent_a in self.world.agents
                and relationship.agent_b in self.world.agents
                and self.world.agents[relationship.agent_a].alive
                and self.world.agents[relationship.agent_b].alive
                and self.world.agents[relationship.agent_a].village_id == village.id
                and self.world.agents[relationship.agent_b].village_id == village.id
            ]
            if len(candidates) > self.DISPUTE_MAX_RELATIONSHIPS:
                candidates = self.rng.sample(candidates, self.DISPUTE_MAX_RELATIONSHIPS)

            for relationship in candidates:
                if self.rng.random() >= self.DISPUTE_PROBABILITY:
                    continue
                relationship.trust = max(0.0, relationship.trust - 1.0)
                self._emit(
                    EventType.CONFLICT,
                    f"Agents {relationship.agent_a} and {relationship.agent_b} entered a dispute in {village.name}",
                    agent_id=relationship.agent_a,
                    village_id=village.id,
                )

    def _faction_phase(self) -> None:
        """Form small factions from repeated, high-trust social relationships."""
        strong = [
            relationship
            for relationship in self.world.relationships.values()
            if relationship.trust >= self.FACTION_TRUST_THRESHOLD
            and relationship.interactions >= self.FACTION_MIN_INTERACTIONS
            and self.world.agents[relationship.agent_a].alive
            and self.world.agents[relationship.agent_b].alive
        ]

        for agent in sorted(self.world.agents.values(), key=lambda item: item.id):
            if not agent.alive or agent.faction_id is not None:
                continue
            scores = []
            for faction_id, faction in self.world.factions.items():
                links = [
                    relationship
                    for relationship in strong
                    if (relationship.agent_a == agent.id and relationship.agent_b in faction.members)
                    or (relationship.agent_b == agent.id and relationship.agent_a in faction.members)
                ]
                if len(links) >= 2:
                    scores.append((faction_id, sum(link.trust for link in links)))
            if scores:
                faction_id, _ = max(scores, key=lambda item: (item[1], -item[0]))
                faction = self.world.factions[faction_id]
                faction.members.append(agent.id)
                agent.faction_id = faction_id
                self._emit(EventType.FACTION_JOINED, f"Agent {agent.id} joined faction {faction_id}", agent_id=agent.id)

        adjacency = {}
        for relationship in strong:
            if self.world.agents[relationship.agent_a].faction_id is not None:
                continue
            if self.world.agents[relationship.agent_b].faction_id is not None:
                continue
            adjacency.setdefault(relationship.agent_a, set()).add(relationship.agent_b)
            adjacency.setdefault(relationship.agent_b, set()).add(relationship.agent_a)

        visited = set()
        next_id = max(self.world.factions, default=0) + 1
        for start in sorted(adjacency):
            if start in visited:
                continue
            component = []
            stack = [start]
            while stack:
                agent_id = stack.pop()
                if agent_id in visited:
                    continue
                visited.add(agent_id)
                component.append(agent_id)
                stack.extend(sorted(adjacency.get(agent_id, ()), reverse=True))
            if len(component) < self.FACTION_MIN_SIZE:
                continue

            members = sorted(component)
            leader_id = max(
                members,
                key=lambda member_id: (
                    sum(
                        relationship.trust
                        for relationship in strong
                        if member_id in (relationship.agent_a, relationship.agent_b)
                        and relationship.agent_a in members
                        and relationship.agent_b in members
                    ),
                    -member_id,
                ),
            )
            faction = Faction(next_id, f"Faction {next_id}", leader_id, members)
            self.world.factions[next_id] = faction
            for member_id in members:
                self.world.agents[member_id].faction_id = next_id
            self._update_faction_cohesion(faction)
            self._emit(EventType.FACTION_FORMED, f"{faction.name} formed with {len(members)} members", agent_id=leader_id)
            next_id += 1

        for faction in self.world.factions.values():
            self._update_faction_cohesion(faction)

    def _faction_dynamics_phase(self) -> None:
        """Maintain faction membership and deterministically replace dead leaders."""
        for faction_id in sorted(list(self.world.factions)):
            faction = self.world.factions[faction_id]
            living_members = sorted(
                member_id
                for member_id in faction.members
                if self.world.agents[member_id].alive
            )

            if living_members != faction.members:
                for member_id in faction.members:
                    if member_id not in living_members:
                        self.world.agents[member_id].faction_id = None
                faction.members = living_members

            if not faction.members:
                del self.world.factions[faction_id]
                continue

            if faction.leader_id not in faction.members:
                previous_leader = faction.leader_id
                faction.leader_id = self._select_faction_leader(faction)
                self._emit(
                    EventType.FACTION_LEADER_CHANGED,
                    f"Faction {faction.id} selected agent {faction.leader_id} as new leader after agent {previous_leader} left",
                    agent_id=faction.leader_id,
                )

            self._update_faction_cohesion(faction)

    def _select_faction_leader(self, faction: Faction) -> int:
        member_set = set(faction.members)
        return max(
            faction.members,
            key=lambda member_id: (
                sum(
                    relationship.trust
                    for relationship in self.world.relationships.values()
                    if member_id in (relationship.agent_a, relationship.agent_b)
                    and relationship.agent_a in member_set
                    and relationship.agent_b in member_set
                ),
                -member_id,
            ),
        )

    def _update_faction_cohesion(self, faction: Faction) -> None:
        if len(faction.members) < 2:
            faction.cohesion = 0.0
            return
        member_set = set(faction.members)
        trusts = [
            relationship.trust
            for relationship in self.world.relationships.values()
            if relationship.agent_a in member_set and relationship.agent_b in member_set
        ]
        faction.cohesion = sum(trusts) / len(trusts) if trusts else 0.0

    def _migration_phase(self) -> None:
        living = [agent for agent in self.world.agents.values() if agent.alive and self._is_working_age(agent)]
        for agent in living:
            source = self.world.villages[agent.village_id]
            source_population = sum(1 for agent_id in source.agents if self.world.agents[agent_id].alive)
            source_food_per_capita = source.resources.food / source_population if source_population else 0.0
            candidates = []
            for village in self.world.villages.values():
                if village.id == source.id:
                    continue
                population = sum(1 for agent_id in village.agents if self.world.agents[agent_id].alive)
                food_per_capita = village.resources.food / population if population else village.resources.food
                if food_per_capita >= source_food_per_capita + self.MIGRATION_FOOD_GAP:
                    candidates.append((food_per_capita, village))
            if not candidates or self.rng.random() >= self.MIGRATION_PROBABILITY:
                continue
            _, destination = max(candidates, key=lambda item: (item[0], -item[1].id))
            source.agents.remove(agent.id)
            destination.agents.append(agent.id)
            old_village_id = agent.village_id
            agent.village_id = destination.id
            self._emit(EventType.MIGRATION, f"Agent {agent.id} moved from village {old_village_id} to village {destination.id}", agent_id=agent.id, village_id=destination.id)

    def _consumption_phase(self) -> None:
        for agent in list(self.world.agents.values()):
            if agent.alive:
                self._consume_and_age(agent)

    def _emit(self, event_type: EventType, message: str, agent_id: int | None = None, village_id: int | None = None, amount: float | None = None) -> None:
        self.world.events.append(Event(day=self.world.day, type=event_type, message=message, agent_id=agent_id, village_id=village_id, amount=amount))
        if event_type == EventType.TRADE:
            self._daily_trade_volume += amount or 0.0
        elif event_type == EventType.BIRTH:
            self._daily_births += 1
        elif event_type == EventType.DEATH:
            self._daily_deaths += 1
        elif event_type == EventType.MIGRATION:
            self._daily_migrations += 1
        elif event_type == EventType.SOCIAL:
            self._daily_social_interactions += 1
        elif event_type == EventType.CONFLICT:
            self._daily_conflicts += 1

    def _produce(self, village: Village) -> None:
        counts = {occupation: 0 for occupation in Occupation}
        for agent_id in village.agents:
            agent = self.world.agents[agent_id]
            if agent.alive and self._is_working_age(agent):
                counts[agent.occupation] += 1
        food_produced = counts[Occupation.FARMER] * 3.0 + counts[Occupation.HUNTER] * 2.0
        wood_produced = counts[Occupation.BUILDER] * 1.0
        stone_produced = counts[Occupation.BUILDER] * 0.5
        village.resources.food += food_produced
        village.resources.wood += wood_produced
        village.resources.stone += stone_produced
        self._emit(EventType.PRODUCTION, f"{village.name}: +{food_produced:g} food, +{wood_produced:g} wood, +{stone_produced:g} stone", village_id=village.id)

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
            self._emit(EventType.CONSUMPTION, f"Agent {agent.id} was not fed", agent_id=agent.id, village_id=agent.village_id)
        if agent.health <= 0:
            agent.alive = False
            self._emit(EventType.DEATH, f"Agent {agent.id} died", agent_id=agent.id, village_id=agent.village_id)
