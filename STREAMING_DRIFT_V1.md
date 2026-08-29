# QueueCraft Streaming Drift v1

QueueCraft now includes a bounded, offline-first streaming drift monitor for explicit local observations.

## Signals

The monitor compares a reference window with the current window using:

- relative mean shift
- relative standard-deviation shift
- an empirical CDF distance proxy

Insufficient windows return `insufficient_data` and never trigger a challenger.

## Challenger trigger

A detected drift produces:

```json
{
  "evaluation_requested": true,
  "action": "create_challenger_evaluation",
  "deployment": "blocked"
}
```

The trigger is intentionally advisory. It requests evaluation only; it never deploys, scales, trades, or mutates an external system.

## Desktop API

`API.monitor_streaming_drift(payload_json)` accepts explicit local `reference`, `current`, and optional threshold values. `reset_streaming_drift()` clears the current window while retaining the reference.

## Limits

This is a lightweight screening detector, not a calibrated statistical test. For production monitoring, thresholds should be validated against the operating domain and paired with a documented response policy.
