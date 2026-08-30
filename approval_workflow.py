"""Human approval workflow for governed QueueCraft actions."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Mapping

STATES = ("pending", "approved", "rejected", "expired", "cancelled")


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    decision_id: str
    required_role: str = "reviewer"
    policy_id: str | None = None
    reason: str = ""
    created_at: str = ""
    expires_at: str | None = None
    state: str = "pending"
    reviewer_id: str | None = None
    review_note: str | None = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_request(*, request_id: str, decision_id: str, required_role: str = "reviewer", policy_id: str | None = None, reason: str = "", expires_at: str | None = None) -> dict[str, Any]:
    if not request_id or not decision_id:
        raise ValueError("request_id and decision_id are required")
    return asdict(ApprovalRequest(request_id, decision_id, required_role, policy_id, reason, _now(), expires_at))


def transition(request: Mapping[str, Any], *, new_state: str, reviewer_id: str | None = None, review_note: str | None = None, role: str | None = None) -> dict[str, Any]:
    if new_state not in STATES:
        raise ValueError(f"unsupported state: {new_state}")
    current = str(request.get("state", "pending"))
    if current != "pending":
        raise ValueError(f"only pending requests can transition; current={current}")
    if new_state in ("approved", "rejected"):
        if not reviewer_id or not role:
            raise ValueError("reviewer_id and role are required for a decision")
        required_role = str(request.get("required_role", "reviewer"))
        if role != required_role:
            raise ValueError("reviewer role does not satisfy the approval requirement")
    result = dict(request)
    result["state"] = new_state
    result["reviewer_id"] = reviewer_id
    result["review_note"] = review_note
    result["reviewed_at"] = _now()
    result["deployment_performed"] = False
    return result


def workflow_snapshot(requests: list[Mapping[str, Any]]) -> dict[str, Any]:
    counts = {state: 0 for state in STATES}
    for request in requests:
        state = str(request.get("state", "pending"))
        if state not in counts:
            raise ValueError(f"unsupported request state: {state}")
        counts[state] += 1
    return {
        "request_count": len(requests),
        "states": counts,
        "open_requests": counts["pending"],
        "governance": {"human_approval_required": True, "automatic_approval": False, "deployment_side_effects": False},
    }
