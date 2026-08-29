"""Stable service contract for the QueueCraft model-lifecycle layer."""
from __future__ import annotations

import json
from typing import Any

from model_lifecycle import ModelCandidate, compare_challengers, model_lifecycle_snapshot


def evaluate_model_lifecycle(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate model candidates and an optional calibration/drift snapshot."""
    models = [
        ModelCandidate(
            item["model_id"],
            item["family"],
            item["version"],
            item["metrics"],
            tuple(item.get("limitations", [])),
        )
        for item in payload["models"]
    ]
    comparison = compare_challengers(
        models,
        primary_metric=payload.get("primary_metric", "rmse"),
        tolerance=float(payload.get("tolerance", 0.0)),
    )
    result: dict[str, Any] = {"comparison": comparison}
    if "actual" in payload and "predicted" in payload:
        model_id = payload.get("snapshot_model_id", models[0].model_id)
        selected = next(model for model in models if model.model_id == model_id)
        result["snapshot"] = model_lifecycle_snapshot(
            model=selected,
            actual=payload["actual"],
            predicted=payload["predicted"],
            reference_load=payload.get("reference_load"),
            current_load=payload.get("current_load"),
        )
    return result


def evaluate_model_lifecycle_json(payload_json: str) -> str:
    """JSON adapter suitable for the desktop bridge or another local caller."""
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return json.dumps(evaluate_model_lifecycle(payload), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)})
