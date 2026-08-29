"""Regime-aware model selection built on chronological backtests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from walk_forward_backtest import FoldResult, regime_label


@dataclass(frozen=True)
class RegimeWinner:
    regime: str
    model_id: str
    mean_absolute_error: float
    folds: int


def select_by_regime(observations: Sequence[float], folds: Sequence[FoldResult]) -> list[RegimeWinner]:
    values = [float(x) for x in observations]
    grouped: dict[str, dict[str, list[float]]] = {}
    for fold in folds:
        regime = regime_label(values[:fold.test_index])
        grouped.setdefault(regime, {}).setdefault(fold.model_id, []).append(fold.absolute_error)
    winners: list[RegimeWinner] = []
    for regime, models in grouped.items():
        winner_model, errors = min(models.items(), key=lambda item: (sum(item[1]) / len(item[1]), item[0]))
        winners.append(RegimeWinner(regime, winner_model, sum(errors) / len(errors), len(errors)))
    return sorted(winners, key=lambda item: item.regime)


def current_regime_recommendation(observations: Sequence[float], winners: Sequence[RegimeWinner]) -> dict[str, object]:
    regime = regime_label(observations)
    matching = [winner for winner in winners if winner.regime == regime]
    if not matching:
        return {"regime": regime, "model_id": None, "status": "no_validated_regime_winner"}
    winner = min(matching, key=lambda item: (item.mean_absolute_error, item.model_id))
    return {
        "regime": regime,
        "model_id": winner.model_id,
        "status": "validated_regime_match",
        "backtest_mae": winner.mean_absolute_error,
        "folds": winner.folds,
    }
