"""Release/deployment readiness gate for governed QueueCraft decisions.

The gate is deliberately conservative: a policy block, stale evidence, broken
fingerprints, missing required evidence, or an unresolved human approval can
never produce a READY result. It is dependency-free and side-effect free.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from governance_hardening import fingerprint


OUTCOMES = ("READY", "REVIEW", "BLOCK")


@dataclass(frozen=True)
class ReadinessControl:
    control_id: str
    status: str
    detail: str


def _parse_time(value: str) -> datetime:
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _check_fingerprint(name: str, artifact: Mapping[str, Any], expected: Any) -> ReadinessControl:
    if not isinstance(artifact, Mapping):
        return ReadinessControl(name, "fail", "artifact is not a mapping")
    actual = fingerprint(artifact)
    if actual != expected:
        return ReadinessControl(name, "fail", "fingerprint mismatch")
    return ReadinessControl(name, "pass", "fingerprint verified")


def evaluate_readiness(
    *,
    envelope: Mapping[str, Any],
    decision: Mapping[str, Any],
    evidence: Mapping[str, Any],
    policy_result: Mapping[str, Any],
    approval: Mapping[str, Any] | None = None,
    required_evidence_fields: Sequence[str] = (),
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return a conservative readiness decision and an auditable control set."""
    controls: list[ReadinessControl] = []
    current = now.astimezone(timezone.utc) if now else datetime.now(timezone.utc)

    controls.append(_check_fingerprint("decision_identity", decision, envelope.get("decision_fingerprint")))
    controls.append(_check_fingerprint("evidence_identity", evidence, envelope.get("evidence_fingerprint")))

    action = str(policy_result.get("action", "review")).lower()
    if action == "block":
        controls.append(ReadinessControl("policy", "fail", "policy result is block"))
    elif action == "allow":
        controls.append(ReadinessControl("policy", "pass", "policy result is allow"))
    else:
        controls.append(ReadinessControl("policy", "review", "policy review is required"))

    missing = [field for field in required_evidence_fields if field not in evidence or evidence[field] is None]
    controls.append(
        ReadinessControl("evidence_completeness", "fail" if missing else "pass",
                         "missing: " + ", ".join(missing) if missing else "required evidence present")
    )

    expires_at = envelope.get("expires_at") or evidence.get("expires_at")
    if expires_at:
        try:
            expired = current >= _parse_time(str(expires_at))
            controls.append(ReadinessControl("freshness", "fail" if expired else "pass", "evidence expired" if expired else "evidence within validity window"))
        except (TypeError, ValueError):
            controls.append(ReadinessControl("freshness", "fail", "invalid expiry timestamp"))
    else:
        controls.append(ReadinessControl("freshness", "review", "no expiry timestamp supplied"))

    approval_required = bool(envelope.get("approval_required", True))
    if approval_required:
        if approval is None:
            controls.append(ReadinessControl("human_approval", "fail", "approval record is required"))
        else:
            approval_state = str(approval.get("state", "pending"))
            if approval_state == "approved":
                controls.append(ReadinessControl("human_approval", "pass", "human approval recorded"))
            elif approval_state == "rejected":
                controls.append(ReadinessControl("human_approval", "fail", "approval was rejected"))
            elif approval_state == "expired":
                controls.append(ReadinessControl("human_approval", "fail", "approval request expired"))
            else:
                controls.append(ReadinessControl("human_approval", "fail", f"approval state is {approval_state}"))
    else:
        controls.append(ReadinessControl("human_approval", "pass", "approval not required by envelope"))

    if not str(envelope.get("decision_id", "")).strip():
        controls.append(ReadinessControl("decision_id", "fail", "decision_id is missing"))
    else:
        controls.append(ReadinessControl("decision_id", "pass", "decision_id is present"))

    statuses = {control.status for control in controls}
    if "fail" in statuses:
        outcome = "BLOCK"
    elif "review" in statuses:
        outcome = "REVIEW"
    else:
        outcome = "READY"

    return {
        "outcome": outcome,
        "ready": outcome == "READY",
        "review_required": outcome == "REVIEW",
        "blocked": outcome == "BLOCK",
        "controls": [asdict(control) for control in controls],
        "control_summary": {
            "pass": sum(control.status == "pass" for control in controls),
            "review": sum(control.status == "review" for control in controls),
            "fail": sum(control.status == "fail" for control in controls),
        },
    }
