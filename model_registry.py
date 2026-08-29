"""Governed model registry for QueueCraft.

The registry is intentionally local and deterministic. It tracks model identity,
validation evidence, current lifecycle stage, and promotion decisions without
performing deployment or modifying an active production endpoint.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


STAGES = ("development", "candidate", "champion", "retired")


@dataclass
class RegistryRecord:
    model_id: str
    family: str
    version: str
    stage: str = "development"
    validation_status: str = "unvalidated"
    primary_metric: str = "rmse"
    metric_value: float | None = None
    evidence_fingerprint: str | None = None
    limitations: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_at: str | None = None
    review_note: str | None = None


def validate_record(record: RegistryRecord) -> None:
    if record.stage not in STAGES:
        raise ValueError(f"unsupported stage: {record.stage}")
    if not record.model_id or not record.family or not record.version:
        raise ValueError("model_id, family and version are required")
    if record.metric_value is not None and record.metric_value < 0:
        raise ValueError("metric_value must be non-negative")


def register_model(record: RegistryRecord) -> dict[str, Any]:
    validate_record(record)
    return {"record": asdict(record), "registered": True}


def review_candidate(record: RegistryRecord, *, validation_status: str, evidence_fingerprint: str, reviewer_note: str = "") -> dict[str, Any]:
    """Move a development model to candidate after explicit validation review."""
    validate_record(record)
    if record.stage not in ("development", "candidate"):
        raise ValueError("only development/candidate models can enter candidate review")
    if not evidence_fingerprint:
        raise ValueError("evidence_fingerprint is required for candidate review")
    record.stage = "candidate"
    record.validation_status = validation_status
    record.evidence_fingerprint = evidence_fingerprint
    record.reviewed_at = datetime.now(timezone.utc).isoformat()
    record.review_note = reviewer_note or None
    return asdict(record)


def promote_to_champion(record: RegistryRecord, *, approval_id: str, reviewer_note: str = "") -> dict[str, Any]:
    """Record a human-approved champion promotion without deploying anything."""
    validate_record(record)
    if record.stage != "candidate":
        raise ValueError("only candidate models can be promoted to champion")
    if record.validation_status not in ("validated", "validated_with_limits"):
        raise ValueError("model must have an accepted validation status")
    if not approval_id:
        raise ValueError("approval_id is required")
    record.stage = "champion"
    record.reviewed_at = datetime.now(timezone.utc).isoformat()
    record.review_note = reviewer_note or f"Approved by governance record {approval_id}"
    return asdict(record)


def retire_model(record: RegistryRecord, *, approval_id: str) -> dict[str, Any]:
    """Retire a model through an explicit human governance action."""
    validate_record(record)
    if record.stage == "retired":
        return asdict(record)
    if not approval_id:
        raise ValueError("approval_id is required")
    record.stage = "retired"
    record.reviewed_at = datetime.now(timezone.utc).isoformat()
    record.review_note = f"Retired by governance record {approval_id}"
    return asdict(record)


def registry_snapshot(records: list[RegistryRecord]) -> dict[str, Any]:
    """Return a stable summary grouped by lifecycle stage."""
    for record in records:
        validate_record(record)
    grouped = {stage: [] for stage in STAGES}
    for record in records:
        grouped[record.stage].append(record.model_id)
    champions = [record.model_id for record in records if record.stage == "champion"]
    return {
        "total_models": len(records),
        "stages": grouped,
        "champions": champions,
        "governance": {"automatic_promotion": False, "deployment_side_effects": False},
    }
