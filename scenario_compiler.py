"""Compile validated QueueCraft scenarios into immutable execution plans."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from governance_hardening import fingerprint
from scenario_manager import validate_scenario


@dataclass(frozen=True)
class CompiledScenario:
    scenario_fingerprint: str
    schema_version: str
    horizon: int
    replications: int
    seed: int | None
    tier_count: int
    total_servers: int
    estimated_work_units: int
    execution_class: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_scenario(scenario: Mapping[str, Any]) -> dict[str, Any]:
    """Validate, normalize and compile a scenario without executing it."""
    if not isinstance(scenario, Mapping):
        raise ValueError("scenario must be a mapping")
    normalized = validate_scenario(dict(scenario))
    simulation = normalized["simulation"]
    replications = int(simulation["replications"])
    horizon = int(simulation["horizon"])
    tiers = normalized["tiers"]
    total_servers = sum(int(tier["servers"]) for tier in tiers)
    estimated_work_units = replications * horizon * max(len(tiers), 1)
    if estimated_work_units <= 10_000:
        execution_class = "interactive"
    elif estimated_work_units <= 500_000:
        execution_class = "batch"
    else:
        execution_class = "distributed"
    plan = CompiledScenario(
        scenario_fingerprint=fingerprint(normalized),
        schema_version=normalized["schema_version"],
        horizon=horizon,
        replications=replications,
        seed=simulation.get("seed"),
        tier_count=len(tiers),
        total_servers=total_servers,
        estimated_work_units=estimated_work_units,
        execution_class=execution_class,
    )
    return {"compiled": True, "scenario": normalized, "plan": plan.to_dict()}


def verify_compiled_scenario(compiled: Mapping[str, Any]) -> dict[str, Any]:
    """Verify that the compiled plan still matches its normalized scenario."""
    if not isinstance(compiled, Mapping) or not isinstance(compiled.get("scenario"), Mapping):
        raise ValueError("compiled artifact must contain a scenario mapping")
    scenario = dict(compiled["scenario"])
    expected = fingerprint(scenario)
    supplied = str(compiled.get("plan", {}).get("scenario_fingerprint", ""))
    return {"valid": supplied == expected, "expected": expected, "supplied": supplied}
