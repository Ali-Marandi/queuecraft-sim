"""Hardening primitives for auditable QueueCraft decision artifacts.

This module is intentionally dependency-free and side-effect free. It provides:
- canonical JSON serialization for stable fingerprints;
- SHA-256 fingerprints for tamper-evident artifact identity;
- bounded recursive redaction for export-safe metadata;
- a strict decision envelope tying policy, evidence and approval metadata together.

It does not provide cryptographic signing, authentication, authorization, or
compliance certification. Those remain deployment responsibilities.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Any, Mapping, Sequence


DEFAULT_SENSITIVE_KEYS = frozenset({
    "token", "access_token", "refresh_token", "api_key", "apikey", "secret",
    "password", "credential", "authorization", "cookie", "private_key",
})


def canonical_json(value: Any) -> str:
    """Serialize JSON-compatible data deterministically."""
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"value is not canonical JSON data: {exc}") from exc


def fingerprint(value: Any) -> str:
    """Return a stable SHA-256 fingerprint of canonical JSON data."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def redact_sensitive(value: Any, *, sensitive_keys: Sequence[str] = DEFAULT_SENSITIVE_KEYS, replacement: str = "[REDACTED]") -> Any:
    """Recursively redact sensitive mapping keys without mutating the input."""
    keys = {str(key).casefold() for key in sensitive_keys}
    if isinstance(value, Mapping):
        return {
            str(key): replacement if str(key).casefold() in keys else redact_sensitive(item, sensitive_keys=sensitive_keys, replacement=replacement)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive(item, sensitive_keys=sensitive_keys, replacement=replacement) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive(item, sensitive_keys=sensitive_keys, replacement=replacement) for item in value]
    return value


def _require_nonempty(value: Any, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


@dataclass(frozen=True)
class DecisionEnvelope:
    """Minimal, serializable identity for a governed decision."""

    schema_version: int
    decision_id: str
    created_at: str
    decision_fingerprint: str
    policy_id: str
    policy_version: str
    evidence_fingerprint: str
    approval_required: bool = True

    def validate(self) -> None:
        if self.schema_version != 1:
            raise ValueError("unsupported decision envelope schema_version")
        for field in ("decision_id", "created_at", "decision_fingerprint", "policy_id", "policy_version", "evidence_fingerprint"):
            _require_nonempty(getattr(self, field), field)
        for field in ("decision_fingerprint", "evidence_fingerprint"):
            value = getattr(self, field)
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value.casefold()):
                raise ValueError(f"{field} must be a SHA-256 hex digest")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def build_decision_envelope(*, decision_id: str, created_at: str, decision: Mapping[str, Any], policy_id: str, policy_version: str, evidence: Mapping[str, Any], approval_required: bool = True) -> dict[str, Any]:
    """Build and validate a reproducible decision envelope."""
    if not isinstance(decision, Mapping) or not isinstance(evidence, Mapping):
        raise ValueError("decision and evidence must be mappings")
    envelope = DecisionEnvelope(
        schema_version=1,
        decision_id=_require_nonempty(decision_id, "decision_id"),
        created_at=_require_nonempty(created_at, "created_at"),
        decision_fingerprint=fingerprint(decision),
        policy_id=_require_nonempty(policy_id, "policy_id"),
        policy_version=_require_nonempty(policy_version, "policy_version"),
        evidence_fingerprint=fingerprint(evidence),
        approval_required=bool(approval_required),
    )
    return envelope.to_dict()
