from simulation.engine import Simulation
from simulation.models import EventType, Occupation


def test_initial_population_is_distributed_across_three_villages():
    simulation = Simulation(seed=42, population=99)

    assert simulation.world.population == 99
    assert [len(v.agents) for v in simulation.world.villages.values()] == [33, 33, 33]
    assert set(agent.occupation for agent in simulation.world.agents.values()) == set(Occupation)


def test_tick_advances_one_day_and_records_an_event():
    simulation = Simulation(seed=42, population=100)

    simulation.tick()

    assert simulation.world.day == 1
    assert simulation.world.population == 100
    assert simulation.world.events[-1].type == EventType.DAY_SUMMARY
    assert simulation.world.events[-1].message == "Day 1: population=100"


def test_seeded_simulations_are_reproducible():
    first = Simulation(seed=123, population=100)
    second = Simulation(seed=123, population=100)

    first.run(30)
    second.run(30)

    assert first.world.day == second.world.day == 30
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_metrics_track_population_and_resources():
    simulation = Simulation(seed=42, population=100)

    initial = simulation.metrics()
    simulation.tick()
    current = simulation.metrics()

    assert initial.day == 0
    assert initial.population == 100
    assert initial.living_population == 100
    assert current.day == 1
    assert current.living_population == 100
    assert current.total_food > initial.total_food
    assert current.total_wood > initial.total_wood
    assert current.total_stone > initial.total_stone
    assert current.total_wealth > initial.total_wealth
    assert current.average_wealth > initial.average_wealth
    assert current.trade_volume >= 0
    assert all(agent.wealth >= 0 for agent in simulation.world.agents.values())


def test_invalid_population_and_run_values_are_rejected():
    try:
        Simulation(population=-1)
        assert False
    except ValueError:
        pass

    simulation = Simulation()
    try:
        simulation.run(-1)
        assert False
    except ValueError:
        pass


def test_world_validation_catches_invalid_agent_state():
    simulation = Simulation(seed=42, population=1)
    simulation.world.agents[1].health = 101

    try:
        simulation.world.validate()
        assert False
    except ValueError:
        pass


def test_structured_events_include_day_and_type():
    simulation = Simulation(seed=42, population=10)

    simulation.tick()

    assert simulation.world.events[0].type == EventType.DAY_STARTED
    assert simulation.world.events[-1].type == EventType.DAY_SUMMARY
    assert all(event.day == 1 for event in simulation.world.events)
    assert any(event.type == EventType.ECONOMY for event in simulation.world.events)


def test_five_hundred_agents_survive_one_year_in_mvp_conditions():
    simulation = Simulation(seed=2026, population=500)

    simulation.run(365)

    assert simulation.world.day == 365
    assert simulation.world.population > 0
    assert all(agent.health >= 0 for agent in simulation.world.agents.values())


def test_occupation_assignment_is_seeded_and_not_fixed_by_agent_id():
    first = Simulation(seed=42, population=30)
    second = Simulation(seed=42, population=30)

    assert [agent.occupation for agent in first.world.agents.values()] == [
        agent.occupation for agent in second.world.agents.values()
    ]
    assert len({agent.occupation for agent in first.world.agents.values()}) > 1


def test_trade_moves_food_between_villages_when_a_deficit_exists():
    simulation = Simulation(seed=42, population=12)
    north = simulation.world.villages[1]
    south = simulation.world.villages[3]
    north.resources.food = 1000.0
    south.resources.food = 0.0

    simulation.tick()

    assert south.resources.food > 0.0
    trade_events = [event for event in simulation.world.events if event.type == EventType.TRADE]
    assert trade_events
    assert all(event.amount is not None and event.amount > 0 for event in trade_events)
    assert simulation.metrics().trade_volume == sum(event.amount for event in trade_events)


def test_world_validation_rejects_negative_wealth():
    simulation = Simulation(seed=42, population=1)
    simulation.world.agents[1].wealth = -0.1

    try:
        simulation.world.validate()
        assert False
    except ValueError:
        pass


def test_trade_can_emerge_without_manually_forcing_village_food():
    simulation = Simulation(seed=7, population=90)
    simulation.run(365)

    trade_events = [
        event for event in simulation.world.events
        if event.type == EventType.TRADE
    ]

    assert trade_events
    assert simulation.world.population > 0
    assert all(v.resources.food >= 0 for v in simulation.world.villages.values())


def test_same_seed_produces_same_trade_history():
    first = Simulation(seed=99, population=30)
    second = Simulation(seed=99, population=30)

    first.run(20)
    second.run(20)

    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history
