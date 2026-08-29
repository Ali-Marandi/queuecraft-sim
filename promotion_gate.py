"""Deterministic governance gate for QueueCraft model promotion."""
from __future__ import annotations

from typing import Any, Mapping


def evaluate_promotion_gate(
    *,
    validation_status: str,
    data_quality_score: float,
    drift_status: str,
    champion_metric: float,
    challenger_metric: float,
    metric_direction: str = "lower_better",
    minimum_improvement: float = 0.0,
    evidence_fingerprint: str | None,
) -> dict[str, Any]:
    """Return an auditable eligibility decision; never promotes a model."""
    reasons: list[str] = []
    if validation_status not in ("validated", "validated_with_limits"):
        reasons.append("validation_not_accepted")
    if not 0.0 <= data_quality_score <= 1.0:
        raise ValueError("data_quality_score must be between 0 and 1")
    if data_quality_score < 0.80:
        reasons.append("data_quality_below_0.80")
    if drift_status == "drift":
        reasons.append("input_drift_detected")
    elif drift_status not in ("stable", "not_configured", "unknown"):
        reasons.append("unrecognized_drift_state")
    if not evidence_fingerprint:
        reasons.append("missing_evidence_fingerprint")
    if metric_direction == "lower_better":
        improvement = (champion_metric - challenger_metric) / max(abs(champion_metric), 1e-12)
    elif metric_direction == "higher_better":
        improvement = (challenger_metric - champion_metric) / max(abs(champion_metric), 1e-12)
    else:
        raise ValueError("metric_direction must be lower_better or higher_better")
    if improvement < minimum_improvement:
        reasons.append("insufficient_metric_improvement")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "metric": {
            "direction": metric_direction,
            "champion": champion_metric,
            "challenger": challenger_metric,
            "relative_improvement": improvement,
            "minimum_required": minimum_improvement,
        },
        "governance": {
            "automatic_promotion": False,
            "human_approval_required": True,
            "deployment_performed": False,
        },
    }
