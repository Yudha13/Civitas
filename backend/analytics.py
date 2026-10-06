"""Historical analysis helpers for CIVITAS metric snapshots."""

from dataclasses import asdict
from typing import Iterable

from simulation.engine import Metrics


def _change(first: float, last: float) -> float:
    return last - first


def _peak(history: list[Metrics], field: str) -> dict:
    item = max(history, key=lambda snapshot: getattr(snapshot, field))
    return {"day": item.day, "value": getattr(item, field)}


def _trough(history: list[Metrics], field: str) -> dict:
    item = min(history, key=lambda snapshot: getattr(snapshot, field))
    return {"day": item.day, "value": getattr(item, field)}


def analyze_metrics(history: Iterable[Metrics]) -> dict:
    """Return a compact deterministic summary of a historical metric window."""
    snapshots = list(history)
    if not snapshots:
        return {
            "start_day": None,
            "end_day": None,
            "days": 0,
            "population": {"start": 0, "end": 0, "change": 0},
            "wealth": {"start": 0.0, "end": 0.0, "change": 0.0},
            "food": {"start": 0.0, "end": 0.0, "change": 0.0},
            "trust": {"start": 0.0, "end": 0.0, "change": 0.0},
            "wealth_gini": {"start": 0.0, "end": 0.0, "change": 0.0},
            "events": {
                "births": 0,
                "deaths": 0,
                "migrations": 0,
                "conflicts": 0,
                "disasters": 0,
                "wars": 0,
                "war_casualties": 0,
                "epidemics": 0,
                "epidemic_infections": 0,
                "epidemic_deaths": 0,
                "ideology_shifts": 0,
            },
            "peaks": {},
            "troughs": {},
        }

    first = snapshots[0]
    last = snapshots[-1]
    return {
        "start_day": first.day,
        "end_day": last.day,
        "days": max(0, last.day - first.day),
        "population": {
            "start": first.living_population,
            "end": last.living_population,
            "change": last.living_population - first.living_population,
        },
        "wealth": {
            "start": first.total_wealth,
            "end": last.total_wealth,
            "change": _change(first.total_wealth, last.total_wealth),
        },
        "food": {
            "start": first.total_food,
            "end": last.total_food,
            "change": _change(first.total_food, last.total_food),
        },
        "trust": {
            "start": first.average_trust,
            "end": last.average_trust,
            "change": _change(first.average_trust, last.average_trust),
        },
        "wealth_gini": {
            "start": first.wealth_gini,
            "end": last.wealth_gini,
            "change": _change(first.wealth_gini, last.wealth_gini),
        },
        "events": {
            "births": sum(item.births for item in snapshots),
            "deaths": sum(item.deaths for item in snapshots),
            "migrations": sum(item.migrations for item in snapshots),
            "conflicts": sum(item.conflicts for item in snapshots),
            "disasters": sum(item.environmental_disasters for item in snapshots),
            "wars": sum(item.wars for item in snapshots),
            "war_casualties": sum(item.war_casualties for item in snapshots),
            "epidemics": sum(item.epidemics for item in snapshots),
            "epidemic_infections": sum(item.epidemic_infections for item in snapshots),
            "epidemic_deaths": sum(item.epidemic_deaths for item in snapshots),
            "ideology_shifts": sum(item.ideology_shifts for item in snapshots),
        },
        "peaks": {
            "population": _peak(snapshots, "living_population"),
            "food": _peak(snapshots, "total_food"),
            "wealth": _peak(snapshots, "total_wealth"),
            "trust": _peak(snapshots, "average_trust"),
        },
        "troughs": {
            "population": _trough(snapshots, "living_population"),
            "food": _trough(snapshots, "total_food"),
            "wealth": _trough(snapshots, "total_wealth"),
            "trust": _trough(snapshots, "average_trust"),
        },
    }
