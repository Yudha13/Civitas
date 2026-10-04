"""Deterministic, dependency-free CIVITAS simulation engine."""

from random import Random

from .models import Agent, Occupation, Village, World


class Simulation:
    """Advance a CIVITAS world one deterministic day at a time."""

    FOOD_PER_DAY = 1.0

    def __init__(self, seed: int = 1, population: int = 100) -> None:
        self.rng = Random(seed)
        self.seed = seed
        self.world = self._create_world(population)

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
        """Advance the simulation by one day."""
        self.world.day += 1

        for village in self.world.villages.values():
            self._produce(village)

        for agent in list(self.world.agents.values()):
            if agent.alive:
                self._consume_and_age(agent)

        self.world.events.append(
            f"Day {self.world.day}: population={self.world.population}"
        )
        return self.world

    def run(self, days: int) -> World:
        for _ in range(days):
            self.tick()
        return self.world

    def _produce(self, village: Village) -> None:
        counts = {occupation: 0 for occupation in Occupation}
        for agent_id in village.agents:
            agent = self.world.agents[agent_id]
            if agent.alive:
                counts[agent.occupation] += 1

        village.resources.food += counts[Occupation.FARMER] * 3.0
        village.resources.food += counts[Occupation.HUNTER] * 2.0
        village.resources.wood += counts[Occupation.BUILDER] * 1.0
        village.resources.stone += counts[Occupation.BUILDER] * 0.5

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

        if agent.health <= 0:
            agent.alive = False
            self.world.events.append(
                f"Day {self.world.day}: agent {agent.id} died"
            )
