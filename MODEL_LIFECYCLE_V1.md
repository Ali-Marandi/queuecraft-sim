# QueueCraft Model Lifecycle v1

QueueCraft now has an offline model-lifecycle layer for evaluating forecasts before any promotion decision.

## Performance

`forecast_metrics()` returns MAE, RMSE, sMAPE, bias, and observation count.

## Calibration

`calibration_by_bins()` groups paired predictions and actuals into deterministic predicted-value bins and reports the gap between average prediction and average actual.

## Drift

`distribution_drift()` compares reference and current numeric samples using mean and median shifts. The result is explicitly a screening indicator, not a statistical hypothesis test.

## Champion / Challenger

`compare_challengers()` ranks candidate models by a primary metric such as RMSE. It records the comparison and recommended candidate but never promotes a model automatically. Human approval is required.

## Lifecycle snapshot

`model_lifecycle_snapshot()` combines model identity, performance, calibration, input drift, and governance state into one portable JSON object.

## CLI

```bash
python model_lifecycle_cli.py examples/model_lifecycle.json --output artifacts/model-lifecycle.json
```

The lifecycle layer is offline-first and does not fetch telemetry, train models, transmit data, or change active production configuration.
