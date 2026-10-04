# Simulation Model

## Time

The simulation advances in discrete ticks.

Initial convention:

```
1 tick = 1 simulated day
```

Each tick processes the world in a deterministic sequence.

## Agent

Initial attributes:

- id
- age
- health
- hunger
- wealth
- trust
- occupation
- village_id

Later versions may add personality, beliefs, relationships, skills, and political affiliation.

## Resources

MVP resources:

- food
- wood
- stone

Resources belong to a village or world location.

## Occupations

MVP occupations:

- Farmer
- Hunter
- Builder
- Trader

Each occupation has production and consumption effects.

## Daily Tick

Conceptual order:

1. environmental update
2. resource production
3. resource consumption
4. health update
5. economic interactions
6. social interactions
7. migration
8. births
9. deaths
10. event generation
11. metrics update

The exact ordering is part of the simulation model and must be documented when changed.

## Determinism

Each simulation run should support a seed.

Example:

```
seed = 84917321
```

Given the same initial state, seed, and engine version, the run should produce reproducible results.

## Emergence

The engine should prefer local rules over scripted outcomes.

For example, a drought should reduce food production. It should not directly trigger a civil war. Conflict may emerge later through scarcity, migration, trust changes, and competing interests.

## MVP Success Condition

A simulation containing approximately 500 agents should run for 365 ticks without invalid state, while producing inspectable population, resource, and event histories.
