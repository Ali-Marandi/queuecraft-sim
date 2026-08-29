"""QueueCraft model lifecycle utilities.

Deterministic, offline-first helpers for measuring forecast calibration/drift and
for comparing a champion model with challenger candidates. These utilities do
not fetch data, train models, or promote a model automatically.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import sqrt
from statistics import mean, median
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class DriftResult:
    metric: str
    baseline_mean: float
    current_mean: float
    absolute_delta: float
    relative_delta: float
    threshold: float
    status: str


def _finite(values: Sequence[float]) -> list[float]:
    out = [float(v) for v in values]
    if not out or any(v != v or v in (float("inf"), float("-inf")) for v in out):
        raise ValueError("values must be non-empty and finite")
    return out


def distribution_drift(reference: Sequence[float], current: Sequence[float], *, relative_threshold: float = 0.20) -> dict[str, Any]:
    """Compare two numeric samples using mean/median shifts as a screening signal."""
    ref = _finite(reference)
    cur = _finite(current)
    ref_mean, cur_mean = mean(ref), mean(cur)
    ref_median, cur_median = median(ref), median(cur)
    mean_delta = abs(cur_mean - ref_mean)
    relative = mean_delta / max(abs(ref_mean), 1e-12)
    status = "drift" if relative >= relative_threshold else "stable"
    return {
        "status": status,
        "relative_threshold": float(relative_threshold),
        "mean": asdict(DriftResult("mean", ref_mean, cur_mean, cur_mean - ref_mean, relative, relative_threshold, status)),
        "median": {"reference": ref_median, "current": cur_median, "absolute_delta": cur_median - ref_median},
        "sample_sizes": {"reference": len(ref), "current": len(cur)},
        "note": "Drift is a screening indicator; it is not a hypothesis test or proof of distribution shift.",
    }


def forecast_metrics(actual: Sequence[float], predicted: Sequence[float]) -> dict[str, float]:
    """Return deterministic MAE/RMSE/SMAPE and bias metrics."""
    a = _finite(actual)
    p = _finite(predicted)
    n = min(len(a), len(p))
    if n < 2:
        raise ValueError("at least two paired observations are required")
    errors = [p[i] - a[i] for i in range(n)]
    mae = mean(abs(e) for e in errors)
    rmse = sqrt(mean(e * e for e in errors))
    smape = mean(2.0 * abs(errors[i]) / max(abs(a[i]) + abs(p[i]), 1e-12) for i in range(n))
    return {"mae": mae, "rmse": rmse, "smape": smape, "bias": mean(errors), "observations": n}


def calibration_by_bins(actual: Sequence[float], predicted: Sequence[float], *, bins: int = 5) -> dict[str, Any]:
    """Measure forecast calibration by quantile-like equal-width predicted bins."""
    a = _finite(actual)
    p = _finite(predicted)
    n = min(len(a), len(p))
    if n < bins:
        raise ValueError("observations must be at least the number of bins")
    low, high = min(p[:n]), max(p[:n])
    width = max((high - low) / bins, 1e-12)
    buckets: list[dict[str, Any]] = []
    for b in range(bins):
        lo = low + b * width
        hi = high if b == bins - 1 else lo + width
        idx = [i for i in range(n) if lo <= p[i] <= hi and (b == bins - 1 or p[i] < hi)]
        if not idx:
            buckets.append({"bin": b, "count": 0})
            continue
        avg_pred = mean(p[i] for i in idx)
        avg_actual = mean(a[i] for i in idx)
        buckets.append({"bin": b, "count": len(idx), "mean_predicted": avg_pred, "mean_actual": avg_actual, "calibration_gap": avg_pred - avg_actual})
    occupied = [x for x in buckets if x["count"]]
    return {
        "bins": buckets,
        "mean_absolute_calibration_gap": mean(abs(x["calibration_gap"]) for x in occupied) if occupied else None,
    }


@dataclass(frozen=True)
class ModelCandidate:
    model_id: str
    family: str
    version: str
    metrics: Mapping[str, float]
    limitations: tuple[str, ...] = ()


def compare_challengers(candidates: Sequence[ModelCandidate], *, primary_metric: str = "rmse", tolerance: float = 0.0) -> dict[str, Any]:
    """Rank candidates without automatically promoting the winner."""
    if not candidates:
        raise ValueError("at least one model candidate is required")
    if any(primary_metric not in c.metrics for c in candidates):
        raise ValueError(f"all candidates must provide primary metric: {primary_metric}")
    ordered = sorted(candidates, key=lambda c: float(c.metrics[primary_metric]))
    champion = ordered[0]
    challenger_results = []
    for candidate in ordered[1:]:
        delta = float(candidate.metrics[primary_metric]) - float(champion.metrics[primary_metric])
        improvement = -delta
        challenger_results.append({
            "model_id": candidate.model_id,
            "primary_metric": primary_metric,
            "delta_vs_best": delta,
            "improvement_vs_best": improvement,
            "beats_current_best": delta < -tolerance,
        })
    return {
        "ranking": [c.model_id for c in ordered],
        "recommended_candidate": champion.model_id,
        "promotion": {"automatic": False, "requires_human_approval": True},
        "primary_metric": primary_metric,
        "tolerance": tolerance,
        "candidates": [
            {"model_id": c.model_id, "family": c.family, "version": c.version, "metrics": dict(c.metrics), "limitations": list(c.limitations)}
            for c in ordered
        ],
        "challenger_comparisons": challenger_results,
    }


def model_lifecycle_snapshot(
    *,
    model: ModelCandidate,
    actual: Sequence[float],
    predicted: Sequence[float],
    reference_load: Sequence[float] | None = None,
    current_load: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Build one auditable calibration and drift snapshot for a model."""
    metrics = forecast_metrics(actual, predicted)
    calibration = calibration_by_bins(actual, predicted)
    drift = distribution_drift(reference_load, current_load) if reference_load is not None and current_load is not None else None
    return {
        "model": {"model_id": model.model_id, "family": model.family, "version": model.version, "limitations": list(model.limitations)},
        "performance": metrics,
        "calibration": calibration,
        "input_drift": drift,
        "governance": {"status": "observed", "promotion_allowed": False, "human_review_required": True},
    }
