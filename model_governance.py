"""Integrated model-governance contract for QueueCraft Enterprise.

This module composes walk-forward validation, drift screening, continuous
evaluation, promotion gates, and registry state into one deterministic report.
It never trains, deploys, or mutates an external system.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Sequence

from continuous_evaluation import EvaluationPolicy, continuous_evaluation
from model_lifecycle import ModelCandidate, compare_challengers
from model_registry import RegistryRecord, registry_snapshot
from promotion_gate import evaluate_promotion_gate
from walk_forward_backtest import BacktestSummary, select_champion, walk_forward


def evaluate_model_governance(
    *,
    observations: Sequence[float],
    models: Mapping[str, Any],
    candidates: Sequence[ModelCandidate],
    champion_metric: float,
    challenger_metric: float,
    metric_direction: str = "lower_better",
    data_quality_score: float = 1.0,
    drift_status: str = "not_configured",
    evidence_fingerprint: str | None = None,
    validation_status: str = "unvalidated",
    evaluation_policy: EvaluationPolicy | None = None,
    min_train_size: int = 6,
) -> dict[str, Any]:
    """Produce one cross-layer model governance decision record."""
    folds, summaries = walk_forward(observations, dict(models), min_train_size=min_train_size)
    champion: BacktestSummary = select_champion(summaries)
    comparison = compare_challengers(candidates)
    evaluation = continuous_evaluation(
        {"primary_loss": champion_metric},
        {"primary_loss": challenger_metric},
        data_quality_score,
        0.0 if drift_status in {"stable", "not_configured"} else 1.0,
        evaluation_policy,
    )
    promotion = evaluate_promotion_gate(
        validation_status=validation_status,
        data_quality_score=data_quality_score,
        drift_status="stable" if drift_status == "stable" else ("drift" if drift_status == "drift" else "not_configured"),
        champion_metric=champion_metric,
        challenger_metric=challenger_metric,
        metric_direction=metric_direction,
        evidence_fingerprint=evidence_fingerprint,
        minimum_improvement=0.0,
    )
    return {
        "schema_version": 1,
        "validation": {
            "folds": len(folds),
            "summaries": [asdict(item) for item in summaries],
            "selected_backtest_model": champion.model_id,
        },
        "candidate_comparison": comparison,
        "continuous_evaluation": evaluation,
        "promotion_gate": promotion,
        "governance": {
            "automatic_promotion": False,
            "deployment_performed": False,
            "human_approval_required": True,
            "overall_status": "blocked" if promotion["eligible"] is False or evaluation["promotion_blocked"] else "review_required",
        },
    }


def governance_snapshot(records: Sequence[RegistryRecord]) -> dict[str, Any]:
    """Return a compact registry posture suitable for an enterprise dashboard."""
    snapshot = registry_snapshot(list(records))
    return {
        "registry": snapshot,
        "posture": {
            "champion_count": len(snapshot["champions"]),
            "automatic_promotion": False,
            "external_deployment": False,
        },
    }
