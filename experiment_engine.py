"""QueueCraft experiment and comparison statistics.

The engine is intentionally model-agnostic: it compares repeated outcomes from
already-defined scenario runs. It reports uncertainty and effect size without
claiming causal identification.
"""
from __future__ import annotations

from math import sqrt
from typing import Any, Sequence

import numpy as np


def bootstrap_mean_ci(values: Sequence[float], confidence: float = 0.95, resamples: int = 5000, seed: int | None = 42) -> dict[str, Any]:
    """Return a percentile bootstrap CI for a sample mean."""
    x = np.asarray(values, dtype=float)
    if x.size < 2:
        raise ValueError("at least 2 observations are required")
    if not 0.5 < confidence < 1.0:
        raise ValueError("confidence must be between 0.5 and 1.0")
    if resamples < 100:
        raise ValueError("resamples must be at least 100")
    rng = np.random.default_rng(seed)
    means = np.empty(resamples, dtype=float)
    for i in range(resamples):
        means[i] = np.mean(rng.choice(x, size=x.size, replace=True))
    alpha = (1.0 - confidence) / 2.0
    return {
        "mean": float(np.mean(x)),
        "lower": float(np.quantile(means, alpha)),
        "upper": float(np.quantile(means, 1.0 - alpha)),
        "confidence": confidence,
        "resamples": resamples,
        "seed": seed,
    }


def paired_effect(baseline: Sequence[float], counterfactual: Sequence[float], confidence: float = 0.95, resamples: int = 5000, seed: int | None = 42) -> dict[str, Any]:
    """Compare paired observations using bootstrap CI on the paired difference."""
    a = np.asarray(baseline, dtype=float)
    b = np.asarray(counterfactual, dtype=float)
    if a.size != b.size or a.size < 2:
        raise ValueError("paired samples must have equal size and at least 2 observations")
    diff = b - a
    ci = bootstrap_mean_ci(diff, confidence=confidence, resamples=resamples, seed=seed)
    pooled = sqrt(max((float(np.var(a, ddof=1)) + float(np.var(b, ddof=1))) / 2.0, 1e-12))
    effect_size = float(np.mean(diff) / pooled)
    direction = "improves" if np.mean(diff) < 0 else "worsens" if np.mean(diff) > 0 else "neutral"
    return {
        "baseline_mean": float(np.mean(a)),
        "counterfactual_mean": float(np.mean(b)),
        "mean_difference": float(np.mean(diff)),
        "ci": ci,
        "standardized_effect": effect_size,
        "direction_for_lower_is_better": direction,
        "paired_observations": int(a.size),
        "interpretation": "Statistical comparison only; not causal evidence without an identification strategy.",
    }


def scenario_experiment(baseline: Sequence[float], candidate: Sequence[float], *, metric: str = "mean_wait", confidence: float = 0.95, resamples: int = 5000, seed: int | None = 42) -> dict[str, Any]:
    """Build a reproducible comparison record suitable for governance/audit exports."""
    result = paired_effect(baseline, candidate, confidence=confidence, resamples=resamples, seed=seed)
    result["metric"] = metric
    result["engine_version"] = "1.0.0"
    return result
