from simulation.engine import Simulation
from simulation.models import EventType, Faction, Ideology, Occupation, Relationship


def test_initial_population_is_distributed_across_three_villages():
    simulation = Simulation(seed=42, population=99)
    assert simulation.world.population == 99
    assert [len(v.agents) for v in simulation.world.villages.values()] == [33, 33, 33]
    assert set(agent.occupation for agent in simulation.world.agents.values()) == set(Occupation)


def test_tick_advances_one_day_and_records_an_event():
    simulation = Simulation(seed=42, population=100)
    simulation.tick()
    assert simulation.world.day == 1
    assert simulation.world.population >= 100
    assert simulation.world.events[-1].type == EventType.DAY_SUMMARY
    assert simulation.world.events[-1].message == f"Day 1: population={simulation.world.population}"


def test_seeded_simulations_are_reproducible():
    first = Simulation(seed=123, population=100)
    second = Simulation(seed=123, population=100)
    first.run(30)
    second.run(30)
    assert first.world.day == second.world.day == 30
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_wealth_inequality_metrics_are_deterministic_and_bounded():
    simulation = Simulation(seed=42, population=10)
    wealth = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0]
    for agent, value in zip(simulation.world.agents.values(), wealth):
        agent.wealth = value

    metrics = simulation.metrics()
    assert abs(metrics.wealth_gini - 0.08181818181818179) < 1e-12
    assert abs(metrics.top_10_wealth_share - 2.0 / 11.0) < 1e-12


def test_metrics_track_population_and_resources():
    simulation = Simulation(seed=42, population=100)
    initial = simulation.metrics()
    simulation.tick()
    current = simulation.metrics()
    assert initial.day == 0
    assert initial.population == 100
    assert initial.living_population == 100
    assert current.day == 1
    assert current.living_population >= 100
    assert current.population == current.living_population
    assert current.total_food > initial.total_food
    assert current.total_wood > initial.total_wood
    assert current.total_stone > initial.total_stone
    assert current.total_wealth > initial.total_wealth
    assert current.average_wealth > initial.average_wealth
    assert 0 <= current.average_trust <= 100
    assert current.trade_volume >= 0
    assert current.births >= 0
    assert current.deaths >= 0
    assert current.migrations >= 0
    assert current.social_interactions >= 0
    assert current.conflicts >= 0
    assert 0 <= current.wealth_gini <= 1
    assert 0 <= current.top_10_wealth_share <= 1
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


def test_world_validation_rejects_negative_wealth():
    simulation = Simulation(seed=42, population=1)
    simulation.world.agents[1].wealth = -0.1
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
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.05
    simulation.run(365)
    assert simulation.world.day == 365
    assert simulation.world.population > 0
    assert all(agent.health >= 0 for agent in simulation.world.agents.values())


def test_occupation_assignment_is_seeded_and_not_fixed_by_agent_id():
    first = Simulation(seed=42, population=30)
    second = Simulation(seed=42, population=30)
    assert [agent.occupation for agent in first.world.agents.values()] == [agent.occupation for agent in second.world.agents.values()]
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


def test_trade_can_emerge_without_manually_forcing_village_food():
    simulation = Simulation(seed=7, population=90)
    simulation.run(365)
    trade_events = [event for event in simulation.world.events if event.type == EventType.TRADE]
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


def test_births_create_new_agents_and_are_seeded():
    first = Simulation(seed=123, population=100)
    second = Simulation(seed=123, population=100)
    first.run(365)
    second.run(365)
    births = [event for event in first.world.events if event.type == EventType.BIRTH]
    assert births
    assert first.world.events == second.world.events
    assert len(first.world.agents) > 100
    assert first.world.population > 0
    assert all(first.world.agents[event.agent_id].age > 0.0 for event in births)


def test_births_preserve_world_validity():
    simulation = Simulation(seed=321, population=100)
    simulation.run(365)
    simulation.world.validate()


def test_children_do_not_produce_or_earn_before_working_age():
    simulation = Simulation(seed=1, population=1)
    child = simulation.world.agents[1]
    child.age = 5.0
    child.occupation = Occupation.FARMER
    initial_food = simulation.world.villages[1].resources.food
    initial_wealth = child.wealth
    simulation.tick()
    assert simulation.world.villages[1].resources.food == initial_food - simulation.FOOD_PER_DAY
    assert child.wealth == initial_wealth


def test_migration_moves_agents_toward_food_rich_villages():
    simulation = Simulation(seed=17, population=3)
    source = simulation.world.villages[1]
    destination = simulation.world.villages[2]
    source.resources.food = 0.0
    destination.resources.food = 1000.0
    simulation.MIGRATION_PROBABILITY = 1.0
    simulation.tick()
    moved = [event for event in simulation.world.events if event.type == EventType.MIGRATION]
    assert moved
    assert any(agent.village_id == 2 for agent in simulation.world.agents.values())
    simulation.world.validate()


def test_migration_is_seeded_and_reproducible():
    first = Simulation(seed=77, population=30)
    second = Simulation(seed=77, population=30)
    first.run(60)
    second.run(60)
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_social_interactions_create_relationships():
    simulation = Simulation(seed=5, population=9)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 1.0
    simulation.tick()
    assert simulation.world.relationships
    relationship = next(iter(simulation.world.relationships.values()))
    assert relationship.agent_a < relationship.agent_b
    assert relationship.interactions == 1
    assert 0 <= relationship.trust <= 100
    assert any(event.type == EventType.SOCIAL for event in simulation.world.events)


def test_inequality_reduces_social_trust_deterministically():
    simulation = Simulation(seed=42, population=6)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 1.0
    simulation.SOCIAL_TRUST_STEP = 0.0
    simulation.INEQUALITY_TRUST_PENALTY = 1.0

    village = simulation.world.villages[1]
    ids = sorted(village.agents)
    wealth = [1.0, 1.0, 1.0, 1.0, 1.0, 10.0]
    for agent in simulation.world.agents.values():
        agent.age = 0.0
    for agent_id, value in zip(ids, wealth):
        simulation.world.agents[agent_id].wealth = value

    initial_inequality = simulation.metrics().wealth_gini
    simulation.tick()

    inequality = initial_inequality
    relationships = [
        relationship
        for relationship in simulation.world.relationships.values()
        if relationship.agent_a in ids and relationship.agent_b in ids
    ]
    assert relationships
    for relationship in relationships:
        first = simulation.world.agents[relationship.agent_a]
        second = simulation.world.agents[relationship.agent_b]
        wealth_gap_penalty = min(0.25, abs(first.wealth - second.wealth) / 100.0)
        expected_trust = max(0.0, 50.0 - wealth_gap_penalty - inequality)
        assert abs(relationship.trust - expected_trust) < 1e-12


def test_social_system_is_seeded_and_reproducible():
    first = Simulation(seed=88, population=30)
    second = Simulation(seed=88, population=30)
    first.run(30)
    second.run(30)
    assert first.world.events == second.world.events
    assert first.world.relationships == second.world.relationships
    assert first.metrics_history == second.metrics_history


def test_conflict_emerges_from_low_trust_and_scarcity():
    simulation = Simulation(seed=5, population=6)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 1.0
    simulation.DISPUTE_PROBABILITY = 1.0
    village = simulation.world.villages[1]
    village.resources.food = 0.0
    ids = sorted(village.agents[:2])
    before = Relationship(ids[0], ids[1], trust=0.0)
    simulation.world.relationships[(ids[0], ids[1])] = before
    simulation.tick()
    conflicts = [event for event in simulation.world.events if event.type == EventType.CONFLICT]
    assert conflicts
    assert simulation.world.relationships[(ids[0], ids[1])].trust == 0.0

def test_conflict_is_seeded_and_reproducible():
    first = Simulation(seed=12, population=30)
    second = Simulation(seed=12, population=30)
    first.run(30)
    second.run(30)
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_relationship_validation_rejects_invalid_pair():
    simulation = Simulation(seed=1, population=2)
    simulation.world.relationships[(2, 1)] = Relationship(2, 1)
    try:
        simulation.world.validate()
        assert False
    except ValueError:
        pass




def test_faction_forms_from_repeated_high_trust_relationships():
    simulation = Simulation(seed=10, population=9)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    for agent in simulation.world.agents.values():
        agent.age = 0.0
    village = simulation.world.villages[1]
    ids = sorted(village.agents[:3])
    for index, first_id in enumerate(ids):
        for second_id in ids[index + 1:]:
            simulation.world.relationships[(first_id, second_id)] = Relationship(
                first_id, second_id, trust=70.0, interactions=3
            )

    simulation.tick()

    assert len(simulation.world.factions) == 1
    faction = next(iter(simulation.world.factions.values()))
    assert faction.members == ids
    assert faction.leader_id in ids
    assert faction.cohesion == 70.0
    assert all(simulation.world.agents[agent_id].faction_id == faction.id for agent_id in ids)
    assert any(event.type == EventType.FACTION_FORMED for event in simulation.world.events)
    simulation.world.validate()


def test_faction_formation_is_seeded_and_reproducible():
    first = Simulation(seed=42, population=30)
    second = Simulation(seed=42, population=30)
    first.SOCIAL_INTERACTION_PROBABILITY = 1.0
    second.SOCIAL_INTERACTION_PROBABILITY = 1.0

    first.run(10)
    second.run(10)

    assert first.world.factions == second.world.factions
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_faction_metrics_track_count_and_average_cohesion():
    simulation = Simulation(seed=3, population=9)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    for agent in simulation.world.agents.values():
        agent.age = 0.0
    village = simulation.world.villages[1]
    ids = sorted(village.agents[:3])
    for index, first_id in enumerate(ids):
        for second_id in ids[index + 1:]:
            simulation.world.relationships[(first_id, second_id)] = Relationship(
                first_id, second_id, trust=70.0, interactions=3
            )

    simulation.tick()

    metrics = simulation.metrics()
    assert metrics.faction_count == 1
    assert metrics.average_faction_cohesion == 70.0


def test_faction_replaces_dead_leader_deterministically():
    simulation = Simulation(seed=4, population=9)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    village = simulation.world.villages[1]
    ids = sorted(village.agents[:3])
    relationships = [
        Relationship(ids[0], ids[1], trust=80.0, interactions=4),
        Relationship(ids[0], ids[2], trust=80.0, interactions=4),
        Relationship(ids[1], ids[2], trust=60.0, interactions=3),
    ]
    for relationship in relationships:
        simulation.world.relationships[(relationship.agent_a, relationship.agent_b)] = relationship

    faction = Faction(1, "Faction 1", ids[0], ids.copy())
    simulation.world.factions[1] = faction
    for agent_id in ids:
        simulation.world.agents[agent_id].faction_id = 1

    simulation.world.agents[ids[0]].alive = False
    simulation.tick()

    assert simulation.world.factions[1].members == ids[1:]
    assert simulation.world.factions[1].leader_id == ids[1]
    assert simulation.world.agents[ids[0]].faction_id is None
    assert any(event.type == EventType.FACTION_LEADER_CHANGED for event in simulation.world.events)
    simulation.world.validate()


def test_political_pressure_tracks_inequality_and_reduces_faction_cohesion():
    simulation = Simulation(seed=21, population=6)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    for agent in simulation.world.agents.values():
        agent.age = 0.0

    village = simulation.world.villages[1]
    ids = sorted(village.agents)
    for agent_id, value in zip(ids, [1.0, 1.0, 1.0, 1.0, 1.0, 10.0]):
        simulation.world.agents[agent_id].wealth = value

    relationship = Relationship(ids[0], ids[1], trust=80.0, interactions=4)
    simulation.world.relationships[(ids[0], ids[1])] = relationship
    faction = Faction(1, "Faction 1", ids[0], ids[:2])
    simulation.world.factions[1] = faction
    simulation.world.agents[ids[0]].faction_id = 1
    simulation.world.agents[ids[1]].faction_id = 1

    simulation.tick()

    metrics = simulation.metrics()
    assert metrics.political_pressure == metrics.wealth_gini
    assert metrics.political_pressure > 0.0
    assert faction.cohesion == max(
        0.0,
        80.0 - metrics.political_pressure * simulation.FACTION_POLITICAL_PRESSURE_PENALTY,
    )


def test_faction_dynamics_are_seeded_and_reproducible():
    first = Simulation(seed=55, population=30)
    second = Simulation(seed=55, population=30)
    first.SOCIAL_INTERACTION_PROBABILITY = 0.2
    second.SOCIAL_INTERACTION_PROBABILITY = 0.2

    first.run(60)
    second.run(60)

    assert first.world.factions == second.world.factions
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_environmental_disaster_is_bounded_and_recorded():
    simulation = Simulation(seed=31, population=6)
    simulation.ENVIRONMENTAL_DISASTER_PROBABILITY = 1.0
    simulation.ENVIRONMENTAL_RESOURCE_LOSS_MIN = 0.2
    simulation.ENVIRONMENTAL_RESOURCE_LOSS_MAX = 0.2
    simulation.ENVIRONMENTAL_HEALTH_DAMAGE_MIN = 5.0
    simulation.ENVIRONMENTAL_HEALTH_DAMAGE_MAX = 5.0

    village = simulation.world.villages[1]
    initial_food = village.resources.food
    initial_wood = village.resources.wood
    initial_health = [simulation.world.agents[agent_id].health for agent_id in village.agents]

    simulation._environmental_disaster_phase()

    disasters = [event for event in simulation.world.events if event.type == EventType.ENVIRONMENTAL_DISASTER]
    assert len(disasters) == 1
    assert simulation.metrics().environmental_disasters == 1
    assert village.resources.food < initial_food or village.resources.wood < initial_wood
    for agent_id, health in zip(village.agents, initial_health):
        assert simulation.world.agents[agent_id].health == max(0.0, health - 5.0)
    simulation.world.validate()


def test_environmental_disasters_are_seeded_and_reproducible():
    first = Simulation(seed=77, population=30)
    second = Simulation(seed=77, population=30)
    first.ENVIRONMENTAL_DISASTER_PROBABILITY = 0.2
    second.ENVIRONMENTAL_DISASTER_PROBABILITY = 0.2

    first.run(60)
    second.run(60)

    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_war_hostility_increases_with_scarcity_and_low_trust():
    simulation = Simulation(seed=41, population=12)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    first_ids = sorted(simulation.world.villages[1].agents)
    second_ids = sorted(simulation.world.villages[2].agents)
    first = Faction(1, "Faction 1", first_ids[0], first_ids[:4], cohesion=80.0)
    second = Faction(2, "Faction 2", second_ids[0], second_ids[:4], cohesion=80.0)
    simulation.world.factions[1] = first
    simulation.world.factions[2] = second
    for agent_id in first.members:
        simulation.world.agents[agent_id].faction_id = 1
    for agent_id in second.members:
        simulation.world.agents[agent_id].faction_id = 2

    for village in simulation.world.villages.values():
        village.resources.food = 100.0

    calm = simulation._faction_war_hostility(first, second)

    for village in (simulation.world.villages[1], simulation.world.villages[2]):
        village.resources.food = 0.0
    simulation.world.relationships[(first.members[0], second.members[0])] = Relationship(
        first.members[0], second.members[0], trust=0.0, interactions=3
    )

    hostile = simulation._faction_war_hostility(first, second)
    assert 0.0 <= calm <= 1.0
    assert 0.0 <= hostile <= 1.0
    assert hostile > calm


def test_war_is_bounded_recorded_and_seeded():
    first = Simulation(seed=41, population=12)
    second = Simulation(seed=41, population=12)
    for simulation in (first, second):
        simulation.WAR_PROBABILITY = 1.0
        simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
        first_ids = sorted(simulation.world.villages[1].agents)
        second_ids = sorted(simulation.world.villages[2].agents)
        simulation.world.factions[1] = Faction(1, "Faction 1", first_ids[0], first_ids[:4], cohesion=70.0)
        simulation.world.factions[2] = Faction(2, "Faction 2", second_ids[0], second_ids[:4], cohesion=60.0)
        for agent_id in first_ids[:4]:
            simulation.world.agents[agent_id].faction_id = 1
        for agent_id in second_ids[:4]:
            simulation.world.agents[agent_id].faction_id = 2

    first._war_phase()
    second._war_phase()

    assert first.world.events == second.world.events
    assert first.metrics() == second.metrics()
    assert first.metrics().wars == 1
    assert first.metrics().war_casualties >= 1
    assert first.metrics().war_casualties <= 4
    assert any(event.type == EventType.WAR_STARTED for event in first.world.events)
    assert any(event.type == EventType.WAR_RESOLVED for event in first.world.events)
    assert all(agent.health >= 0 for agent in first.world.agents.values())
    first.world.validate()


def test_epidemic_is_bounded_recorded_and_recoverable():
    simulation = Simulation(seed=101, population=9)
    simulation.EPIDEMIC_INTRODUCTION_PROBABILITY = 1.0
    simulation.EPIDEMIC_HEALTH_DAMAGE = 1.0
    simulation.SOCIAL_INTERACTION_PROBABILITY = 1.0
    simulation.tick()

    cases = [event for event in simulation.world.events if event.type == EventType.EPIDEMIC_STARTED]
    assert cases
    assert simulation.metrics().epidemics == 1
    infected = [agent for agent in simulation.world.agents.values() if agent.disease_days > 0 or agent.immune]
    assert infected
    assert all(0 <= agent.health <= 100 for agent in simulation.world.agents.values())
    simulation.world.validate()

    simulation.EPIDEMIC_INTRODUCTION_PROBABILITY = 0.0
    simulation.run(simulation.EPIDEMIC_DURATION_DAYS + 1)
    assert any(event.type == EventType.EPIDEMIC_RECOVERED for event in simulation.world.events)
    assert any(agent.immune for agent in simulation.world.agents.values())
    simulation.world.validate()


def test_epidemic_transmission_increases_with_local_contacts():
    simulation = Simulation(seed=202, population=6)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    simulation.EPIDEMIC_INTRODUCTION_PROBABILITY = 0.0
    simulation.EPIDEMIC_TRANSMISSION_PROBABILITY = 1.0
    village = simulation.world.villages[1]
    ids = sorted(village.agents)
    for index, first_id in enumerate(ids):
        for second_id in ids[index + 1:]:
            simulation.world.relationships[(first_id, second_id)] = Relationship(
                first_id, second_id, trust=70.0, interactions=3
            )
    simulation.world.agents[ids[0]].disease_days = simulation.EPIDEMIC_DURATION_DAYS
    simulation._epidemic_phase()
    assert sum(agent.disease_days > 0 for agent in simulation.world.agents.values()) >= 2
    assert simulation.metrics().epidemic_infections >= 1
    simulation.world.validate()


def test_epidemics_are_seeded_and_reproducible():
    first = Simulation(seed=303, population=30)
    second = Simulation(seed=303, population=30)
    first.EPIDEMIC_INTRODUCTION_PROBABILITY = 0.2
    second.EPIDEMIC_INTRODUCTION_PROBABILITY = 0.2
    first.SOCIAL_INTERACTION_PROBABILITY = 0.8
    second.SOCIAL_INTERACTION_PROBABILITY = 0.8
    first.run(60)
    second.run(60)
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history
    assert all(agent.disease_days >= 0 for agent in first.world.agents.values())


def test_ideology_is_bounded_emergent_and_recorded():
    simulation = Simulation(seed=909, population=30)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 1.0
    for village in simulation.world.villages.values():
        village.resources.food = 0.0
    simulation._ideology_phase()

    assert all(agent.ideology in list(Ideology) for agent in simulation.world.agents.values())
    assert all(0.0 <= agent.ideology_commitment <= 1.0 for agent in simulation.world.agents.values())
    assert 0.0 <= simulation.metrics().ideology_diversity <= 1.0
    assert 0.0 <= simulation.metrics().dominant_ideology_share <= 1.0
    assert simulation.metrics().ideology_shifts >= 0
    assert all(event.type == EventType.IDEOLOGY_SHIFTED for event in simulation.world.events if event.type == EventType.IDEOLOGY_SHIFTED)
    simulation.world.validate()


def test_ideology_is_seeded_and_reproducible():
    first = Simulation(seed=910, population=30)
    second = Simulation(seed=910, population=30)
    first.SOCIAL_INTERACTION_PROBABILITY = 0.8
    second.SOCIAL_INTERACTION_PROBABILITY = 0.8
    first.run(60)
    second.run(60)
    assert first.world.agents == second.world.agents
    assert first.world.events == second.world.events
    assert first.metrics_history == second.metrics_history


def test_ideology_changes_war_hostility_with_cross_faction_difference():
    simulation = Simulation(seed=911, population=12)
    simulation.SOCIAL_INTERACTION_PROBABILITY = 0.0
    first_ids = sorted(simulation.world.villages[1].agents)
    second_ids = sorted(simulation.world.villages[2].agents)
    first = Faction(1, "Faction 1", first_ids[0], first_ids[:4], cohesion=70.0)
    second = Faction(2, "Faction 2", second_ids[0], second_ids[:4], cohesion=70.0)
    simulation.world.factions[1] = first
    simulation.world.factions[2] = second
    for agent_id in first.members:
        simulation.world.agents[agent_id].faction_id = 1
    for agent_id in second.members:
        simulation.world.agents[agent_id].faction_id = 2
    for agent in simulation.world.agents.values():
        agent.ideology = Ideology.COMMUNAL
    calm = simulation._faction_war_hostility(first, second)
    for agent_id in second.members:
        simulation.world.agents[agent_id].ideology = Ideology.EXPANSIONIST
    hostile = simulation._faction_war_hostility(first, second)
    assert hostile > calm
    assert 0.0 <= hostile <= 1.0
