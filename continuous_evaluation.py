"""Continuous evaluation orchestration for governed QueueCraft models."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from regression_guardrails import Guardrail, evaluate_guardrails


@dataclass(frozen=True)
class EvaluationPolicy:
    required_improvement: float = 0.0
    min_data_quality: float = 0.75
    max_drift: float = 0.20
    protected_metrics: tuple[str, ...] = ("sla_failure_rate", "latency_p95", "bias")


def continuous_evaluation(
    champion: Mapping[str, float],
    challenger: Mapping[str, float],
    data_quality: float,
    drift_score: float,
    policy: EvaluationPolicy | None = None,
) -> dict[str, Any]:
    p = policy or EvaluationPolicy()
    gates: list[dict[str, Any]] = []
    improvement = float(champion.get("primary_loss", 0.0)) - float(challenger.get("primary_loss", 0.0))
    gates.append({"gate": "primary_improvement", "value": improvement, "required": p.required_improvement, "status": "pass" if improvement >= p.required_improvement else "blocked"})
    gates.append({"gate": "data_quality", "value": data_quality, "required": p.min_data_quality, "status": "pass" if data_quality >= p.min_data_quality else "blocked"})
    gates.append({"gate": "drift", "value": drift_score, "maximum": p.max_drift, "status": "pass" if drift_score <= p.max_drift else "blocked"})
    guardrails = evaluate_guardrails(
        champion,
        challenger,
        [Guardrail(metric, "lower_is_better", 0.05) for metric in p.protected_metrics],
    )
    gates.append({"gate": "protected_metrics", "status": guardrails["status"]})
    blocked = any(g["status"] == "blocked" for g in gates) or guardrails["promotion_blocked"]
    return {
        "status": "blocked" if blocked else "eligible_for_promotion_review",
        "promotion_blocked": blocked,
        "deployment": "blocked",
        "gates": gates,
        "guardrails": guardrails,
        "human_approval_required": True,
    }
