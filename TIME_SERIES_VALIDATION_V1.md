# QueueCraft Time-Series Validation v1

QueueCraft now includes chronological walk-forward validation for forecasting models.

## Walk-forward backtesting

`walk_forward()` uses expanding training windows and one-step-ahead test observations. A forecast never receives observations from the future test window.

Reported metrics:

- MAE
- RMSE
- signed bias
- sMAPE

`select_champion()` ranks models by MAE, then RMSE, then absolute bias. This is a deterministic screening rule, not a substitute for domain review.

## Regime-aware selection

`regime_label()` provides a transparent demand-regime label from recent trend and dispersion: `surge`, `decline`, `volatile`, or `stable` (with `insufficient_history` when history is too short).

`select_by_regime()` identifies the lowest-error validated model within each observed regime. `current_regime_recommendation()` returns a recommendation only when a validated winner exists for the current regime.

## Governance boundary

Backtest results are evidence for model selection. They do not automatically promote, deploy, or replace a model. Promotion remains subject to the existing model registry and promotion gate.

## Example

```python
from ai_forecaster import predict_load
from walk_forward_backtest import walk_forward, select_champion

models = {
    "polynomial": lambda history: predict_load(history)["predictions"][0],
    "last_value": lambda history: history[-1],
}
folds, summaries = walk_forward([10, 12, 14, 15, 18, 21, 19, 24, 26, 29, 27, 31], models, min_train_size=6)
champion = select_champion(summaries)
print(champion)
```

The validation layer is intentionally model-agnostic so future forecasting models can enter as challengers without changing the governance contract.
