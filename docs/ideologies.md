# Stage 9 — Ideologies and Belief Systems

## Goal
Introduce belief systems as an emergent social layer. Ideology describes tendencies that arise from world conditions and social influence, not scripted factions or predetermined historical outcomes.

## Design principles
- **Agent-level state:** each living agent has a current ideology and bounded commitment.
- **Emergence:** ideology changes from scarcity, inequality, trust, faction cohesion, and local social influence.
- **Seeded:** all stochastic decisions use the simulation RNG.
- **Bounded:** ideology can influence trust, faction cohesion, and conflict only through small clamped modifiers.
- **Observable:** shifts are represented as events and exposed through metrics/history.
- **Persistent:** ideology state and historical metrics survive save/load through an Alembic migration.
- **Backward-compatible:** existing simulations load with a neutral/default ideology.

## Initial ideology set
| Ideology | Core tendency |
| --- | --- |
| Communal | cooperation and shared resources |
| Traditional | stability, continuity, and existing social bonds |
| Individualist | autonomy and personal wealth |
| Expansionist | growth, competition, and external opportunity |

These labels are simulation abstractions, not claims about real-world political ideologies.

## Emergence model
Each agent evaluates bounded pressures rather than receiving a hard-coded assignment.
- Scarcity increases the relative appeal of communal responses.
- Wealth inequality increases pressure toward individualist or expansionist responses depending on local opportunity.
- High trust and faction cohesion reinforce traditional or communal tendencies.
- Low trust and repeated conflict increase individualist or expansionist tendencies.
- Existing ideology receives inertia through commitment, preventing daily random switching.
- Social neighbors provide bounded influence based on repeated interactions.

The exact scoring remains deterministic and is normalized before selection.

## Effects
Ideology will not directly decide war, migration, or production. Instead it provides small modifiers to relationship trust changes, faction cohesion, and conflict/war hostility. All effects are clamped and remain secondary to existing systems.

## Events
Expected event: `IDEOLOGY_SHIFTED`. Events include the agent, previous ideology, new ideology, and bounded commitment value.

## Metrics
Stage 9 should expose ideological diversity, dominant ideology distribution, and ideology shifts per day. Historical metrics remain deterministic and persisted.

## Validation
Regression coverage should verify valid ideology state, bounded commitment, seeded reproducibility, deterministic save/load continuation, social influence, bounded effects on trust/cohesion/hostility, and no invalid world state after ideology shifts.

## Deliberate non-goals
Stage 9 does not attempt to model real-world political parties, modern political labels, propaganda systems, elections, religion, or historical civilizations. CIVITAS remains an emergent sandbox.