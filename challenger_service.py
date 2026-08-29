"""Closed-loop challenger evaluation service.

This local service combines a drift signal, registry candidates, and optional
model-evaluation metrics into a single governed response. It never deploys,
scales, trades, or mutates an external system.
"""
from __future__ import annotations

import json
from typing import Any, Mapping

from challenger_orchestrator import orchestrate_challenger_evaluation


def build_evaluation_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Build an auditable challenger evaluation response from JSON-like input."""
    return orchestrate_challenger_evaluation(
        payload.get("drift", {}),
        list(payload.get("registry_candidates", [])),
        current_model_id=payload.get("current_model_id"),
        family=payload.get("family"),
    )


def build_evaluation_request_json(payload_json: str) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        return json.dumps(build_evaluation_request(payload), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)})
