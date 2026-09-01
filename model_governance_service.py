"""JSON service contract for the integrated QueueCraft model-governance layer."""
from __future__ import annotations

import json
from typing import Any

from model_governance import evaluate_model_governance
from model_lifecycle import ModelCandidate


def evaluate_model_governance_json(payload_json: str) -> str:
    """Validate a local request and return a deterministic governance report."""
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        raw_models = payload.get("models", {})
        if not isinstance(raw_models, dict) or not raw_models:
            raise ValueError("models must be a non-empty mapping of model_id to callable name")

        # This service intentionally accepts only built-in deterministic model families.
        builtin = {
            "last_value": lambda values: float(values[-1]),
            "mean": lambda values: sum(values) / len(values),
            "median": lambda values: sorted(values)[len(values) // 2],
        }
        models = {}
        for name in raw_models:
            if name not in builtin:
                raise ValueError(f"unsupported built-in model: {name}")
            models[name] = builtin[name]

        candidates = [
            ModelCandidate(
                str(item["model_id"]),
                str(item["family"]),
                str(item["version"]),
                {str(k): float(v) for k, v in item["metrics"].items()},
                tuple(item.get("limitations", [])),
            )
            for item in payload.get("candidates", [])
        ]
        result = evaluate_model_governance(
            observations=payload["observations"],
            models=models,
            candidates=candidates,
            champion_metric=float(payload["champion_metric"]),
            challenger_metric=float(payload["challenger_metric"]),
            metric_direction=str(payload.get("metric_direction", "lower_better")),
            data_quality_score=float(payload.get("data_quality_score", 1.0)),
            drift_status=str(payload.get("drift_status", "not_configured")),
            evidence_fingerprint=payload.get("evidence_fingerprint"),
            validation_status=str(payload.get("validation_status", "unvalidated")),
            min_train_size=int(payload.get("min_train_size", 6)),
        )
        return json.dumps(result, ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError, ZeroDivisionError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)
