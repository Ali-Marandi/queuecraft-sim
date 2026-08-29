"""QueueCraft challenger orchestration.

Connects streaming-drift signals to governed challenger evaluation without
performing deployment or external mutations. The orchestrator chooses a
registered challenger candidate, runs a supplied evaluation callback, and
returns an auditable evaluation request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


@dataclass(frozen=True)
class ChallengerTrigger:
    evaluation_requested: bool
    reason: str
    source: str
    deployment: str = "blocked"


def build_challenger_trigger(drift_result: Mapping[str, Any]) -> ChallengerTrigger:
    """Translate a drift monitor result into an advisory evaluation trigger."""
    if drift_result.get("status") != "drift_detected":
        return ChallengerTrigger(False, "no_material_drift", "streaming_drift")
    return ChallengerTrigger(
        True,
        "material_input_drift_detected",
        "streaming_drift",
    )


def select_challenger(
    candidates: list[Mapping[str, Any]],
    *,
    family: str | None = None,
    exclude_model_id: str | None = None,
) -> Mapping[str, Any] | None:
    """Select the highest-ranked candidate that is eligible for evaluation."""
    eligible = []
    for candidate in candidates:
        if candidate.get("status") not in {"candidate", "development"}:
            continue
        if family and candidate.get("family") != family:
            continue
        if exclude_model_id and candidate.get("model_id") == exclude_model_id:
            continue
        if candidate.get("validation_status") not in {"passed", "pending"}:
            continue
        eligible.append(candidate)
    if not eligible:
        return None
    return sorted(eligible, key=lambda x: (-float(x.get("priority", 0.0)), str(x.get("model_id", ""))))[0]


def orchestrate_challenger_evaluation(
    drift_result: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
    *,
    current_model_id: str | None = None,
    family: str | None = None,
    evaluator: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a challenger evaluation request and optionally execute a local evaluator."""
    trigger = build_challenger_trigger(drift_result)
    if not trigger.evaluation_requested:
        return {
            "status": "not_triggered",
            "trigger": trigger.__dict__,
            "candidate": None,
            "evaluation": None,
            "deployment": "blocked",
        }

    candidate = select_challenger(candidates, family=family, exclude_model_id=current_model_id)
    if candidate is None:
        return {
            "status": "triggered_no_candidate",
            "trigger": trigger.__dict__,
            "candidate": None,
            "evaluation": None,
            "deployment": "blocked",
        }

    evaluation = evaluator(candidate) if evaluator else None
    return {
        "status": "evaluation_completed" if evaluation is not None else "evaluation_requested",
        "trigger": trigger.__dict__,
        "candidate": dict(candidate),
        "evaluation": dict(evaluation) if evaluation is not None else None,
        "deployment": "blocked",
        "human_approval_required": True,
    }
