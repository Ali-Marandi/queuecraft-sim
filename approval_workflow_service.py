"""JSON adapter for QueueCraft policy evaluation and approval workflow."""
from __future__ import annotations

import json
from typing import Any

from approval_workflow import create_request, transition, workflow_snapshot
from policy_engine import evaluate_policy, policy_from_mapping


def evaluate_with_policy(payload: dict[str, Any]) -> dict[str, Any]:
    policy = policy_from_mapping(payload["policy"])
    return evaluate_policy(policy, payload["decision"])


def create_approval(payload: dict[str, Any]) -> dict[str, Any]:
    return create_request(
        request_id=str(payload["request_id"]),
        decision_id=str(payload["decision_id"]),
        required_role=str(payload.get("required_role", "reviewer")),
        policy_id=payload.get("policy_id"),
        reason=str(payload.get("reason", "")),
        expires_at=payload.get("expires_at"),
    )


def transition_approval(payload: dict[str, Any]) -> dict[str, Any]:
    return transition(
        payload["request"],
        new_state=str(payload["new_state"]),
        reviewer_id=payload.get("reviewer_id"),
        review_note=payload.get("review_note"),
        role=payload.get("role"),
    )


def workflow_summary(payload: dict[str, Any]) -> dict[str, Any]:
    return workflow_snapshot(payload.get("requests", []))


def json_call(payload_json: str, operation: str) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        functions = {
            "evaluate_policy": evaluate_with_policy,
            "create_approval": create_approval,
            "transition_approval": transition_approval,
            "workflow_summary": workflow_summary,
        }
        if operation not in functions:
            raise ValueError(f"unsupported operation: {operation}")
        return json.dumps(functions[operation](payload), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)
