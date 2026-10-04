# Simulation Model

## Time

The simulation advances in discrete ticks.

Initial convention:

```
1 tick = 1 simulated day
```

Each tick processes the world in a deterministic sequence.

## Agent

Core attributes:

- id
- age
- health
- hunger
- wealth
- trust
- occupation
- village_id
- fertility
- alive

Working-age agents are currently defined as age 16+.

Children remain part of the population and consume resources, but do not produce resources or earn occupation income until they reach working age.

## Resources

MVP resources:

- food
- wood
- stone

Resources belong to a village.

## Occupations

MVP occupations:

- Farmer
- Hunter
- Builder
- Trader

Occupation rules currently affect production and daily wealth income. Traders also participate in village food trade.

## Villages

The MVP contains three villages:

- North
- Central
- South

Each village owns resources and maintains an agent roster.

## Daily Tick

Current execution order:

1. resource production
2. economic income
3. village food trade
4. resource consumption and aging
5. births
6. social interactions
7. scarcity disputes
8. migration
9. daily summary
10. world validation
11. metrics snapshot

The exact ordering is part of the simulation model and must be documented whenever changed.

## Population Dynamics

Births are seeded and deterministic. Eligible adults are currently ages 18–45, with a daily probability modified by fertility.

Newborns:

- start at age 0
- inherit a portion of parent wealth
- inherit trust and fertility
- remain in the parent's village
- do not produce or earn income until working age

Population metrics represent living population. Historical agent records remain in the world so events and lineage-related systems can reference them later.

## Migration

Working-age agents may migrate when another village has a substantially higher food-per-capita level.

Migration is intentionally probabilistic and local:

- source and destination are existing villages
- the destination must exceed the source by the migration food-gap threshold
- migration probability is seeded
- the agent is removed from the source roster and added to the destination roster
- migration is recorded as a structured event

This is a first social mobility layer, not yet a family migration or pathfinding system.

## Determinism

Each simulation run supports a seed.

Example:

```
seed = 84917321
```

Given the same initial state, seed, and engine version, the run should produce reproducible results.

## Emergence

The engine should prefer local rules over scripted outcomes.

For example, a village with persistent food scarcity may lose population through migration. The engine should not directly declare that village to have collapsed. Larger outcomes should emerge from interacting local rules.

## MVP Success Condition

A simulation containing approximately 500 agents should run for 365 ticks without invalid state, while producing inspectable population, resource, migration, and event histories.


## Social Relationships

Agents can form pairwise relationships through same-village interactions. Relationship trust starts neutral and changes from occupation similarity and wealth differences. Daily social sampling is bounded so relationship growth remains computationally manageable while preserving seeded determinism.

Low-trust relationships can produce non-violent disputes when village food scarcity is severe. Disputes reduce relationship trust and are recorded as structured conflict events.

Relationship integrity is fully validated periodically during long simulations rather than scanning the entire relationship graph every tick. Agent, roster, and resource invariants remain checked every tick.

## Performance and Validation

The engine targets approximately 500 agents for 365 simulated days. Event-derived daily metrics are maintained incrementally instead of rescanning the full event history each tick.

Full relationship validation runs every 30 days, while lightweight world validation runs every tick. This preserves deterministic behavior while preventing the relationship graph from turning routine validation into an accidental quadratic tax.
