from simulation.engine import Simulation


def test_initial_population_is_distributed_across_three_villages():
    simulation = Simulation(seed=42, population=99)

    assert simulation.world.population == 99
    assert [len(v.agents) for v in simulation.world.villages.values()] == [33, 33, 33]


def test_tick_advances_one_day_and_records_an_event():
    simulation = Simulation(seed=42, population=100)

    simulation.tick()

    assert simulation.world.day == 1
    assert simulation.world.population == 100
    assert simulation.world.events[-1] == "Day 1: population=100"


def test_seeded_simulations_are_reproducible():
    first = Simulation(seed=123, population=100)
    second = Simulation(seed=123, population=100)

    first.run(30)
    second.run(30)

    assert first.world.day == second.world.day == 30
    assert first.world.events == second.world.events
    assert first.world.population == second.world.population


def test_five_hundred_agents_survive_one_year_in_mvp_conditions():
    simulation = Simulation(seed=2026, population=500)

    simulation.run(365)

    assert simulation.world.day == 365
    assert simulation.world.population > 0
    assert all(agent.health >= 0 for agent in simulation.world.agents.values())
