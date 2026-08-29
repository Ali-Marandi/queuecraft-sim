"""Walk-forward validation for QueueCraft forecasting models.

The module is deliberately model-agnostic: callers provide named forecasting
functions that consume a training window and return one-step predictions.
All splits are chronological; no future observations are used in a training
window. Metrics are simple, deterministic, and suitable for model governance.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean
from typing import Callable, Sequence


ForecastFn = Callable[[Sequence[float]], float]


@dataclass(frozen=True)
class FoldResult:
    model_id: str
    train_end: int
    test_index: int
    actual: float
    prediction: float
    absolute_error: float
    squared_error: float


@dataclass(frozen=True)
class BacktestSummary:
    model_id: str
    folds: int
    mae: float
    rmse: float
    bias: float
    smape: float


def _smape(actual: float, prediction: float) -> float:
    denom = abs(actual) + abs(prediction)
    return 0.0 if denom == 0 else 2.0 * abs(prediction - actual) / denom


def walk_forward(
    observations: Sequence[float],
    models: dict[str, ForecastFn],
    *,
    min_train_size: int = 6,
    step: int = 1,
) -> tuple[list[FoldResult], list[BacktestSummary]]:
    """Evaluate one-step forecasts on expanding chronological windows."""
    values = [float(x) for x in observations]
    if len(values) <= min_train_size:
        raise ValueError("observations must exceed min_train_size")
    if min_train_size < 2 or step < 1:
        raise ValueError("min_train_size must be >= 2 and step >= 1")
    folds: list[FoldResult] = []
    summaries: list[BacktestSummary] = []
    for model_id, model in models.items():
        model_folds: list[FoldResult] = []
        for test_index in range(min_train_size, len(values), step):
            train = values[:test_index]
            actual = values[test_index]
            prediction = float(model(train))
            if not isfinite(prediction):
                raise ValueError(f"model {model_id} returned a non-finite prediction")
            error = prediction - actual
            model_folds.append(FoldResult(model_id, test_index, test_index, actual, prediction, abs(error), error * error))
        folds.extend(model_folds)
        errors = [f.prediction - f.actual for f in model_folds]
        actuals = [f.actual for f in model_folds]
        predictions = [f.prediction for f in model_folds]
        summaries.append(
            BacktestSummary(
                model_id=model_id,
                folds=len(model_folds),
                mae=mean(f.absolute_error for f in model_folds),
                rmse=mean(f.squared_error for f in model_folds) ** 0.5,
                bias=mean(errors),
                smape=mean(_smape(a, p) for a, p in zip(actuals, predictions)),
            )
        )
    return folds, summaries


def select_champion(summaries: Sequence[BacktestSummary]) -> BacktestSummary:
    """Select a champion by MAE, then RMSE, then absolute bias."""
    if not summaries:
        raise ValueError("at least one summary is required")
    return min(summaries, key=lambda item: (item.mae, item.rmse, abs(item.bias), item.model_id))


def regime_label(history: Sequence[float], *, trend_window: int = 5, volatility_window: int = 5) -> str:
    """Label a simple demand regime using recent trend and relative volatility."""
    values = [float(x) for x in history]
    if len(values) < max(trend_window, volatility_window) + 1:
        return "insufficient_history"
    recent = values[-trend_window:]
    prior = values[-(trend_window + 1):-1]
    trend = mean(recent) - mean(prior)
    vol = (max(recent) - min(recent)) / max(mean(recent), 1e-9)
    if trend > 0.15 * max(mean(recent), 1e-9) and vol > 0.30:
        return "surge"
    if trend < -0.15 * max(mean(recent), 1e-9):
        return "decline"
    if vol > 0.60:
        return "volatile"
    return "stable"


def regime_aware_scores(observations: Sequence[float], folds: Sequence[FoldResult]) -> dict[str, dict[str, float]]:
    """Aggregate absolute error by regime at each test point."""
    values = [float(x) for x in observations]
    buckets: dict[str, dict[str, list[float]]] = {}
    for fold in folds:
        regime = regime_label(values[: fold.test_index])
        buckets.setdefault(regime, {}).setdefault(fold.model_id, []).append(fold.absolute_error)
    return {regime: {model: mean(errors) for model, errors in models.items()} for regime, models in buckets.items()}
