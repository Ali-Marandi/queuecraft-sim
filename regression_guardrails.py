"""Continuous evaluation guardrails for QueueCraft challengers.

Compares champion and challenger metrics and blocks promotion when a protected
metric regresses beyond its configured tolerance. The module is deterministic,
offline-first, and advisory: it never deploys or changes external systems.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any


@dataclass(frozen=True)
class Guardrail:
    name: str
    direction: str = "lower_is_better"
    max_relative_regression: float = 0.05


def _relative_change(champion: float, challenger: float) -> float:
    denominator = max(abs(champion), 1e-12)
    return (challenger - champion) / denominator


def evaluate_guardrails(champion: Mapping[str, float], challenger: Mapping[str, float], guards: list[Guardrail]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    blocked = False
    for guard in guards:
        if guard.name not in champion or guard.name not in challenger:
            results.append({"metric": guard.name, "status": "missing_data"})
            blocked = True
            continue
        old = float(champion[guard.name])
        new = float(challenger[guard.name])
        change = _relative_change(old, new)
        if guard.direction == "lower_is_better":
            regression = change > guard.max_relative_regression
        elif guard.direction == "higher_is_better":
            regression = (-change) > guard.max_relative_regression
        else:
            raise ValueError("direction must be lower_is_better or higher_is_better")
        status = "blocked" if regression else "pass"
        if regression:
            blocked = True
        results.append({"metric": guard.name, "champion": old, "challenger": new, "relative_change": change, "status": status})
    return {
        "status": "blocked" if blocked else "pass",
        "promotion_blocked": blocked,
        "checks": results,
        "deployment": "blocked",
        "note": "Guardrails are decision controls, not evidence of model validity by themselves.",
    }
