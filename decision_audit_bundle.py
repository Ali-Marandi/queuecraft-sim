"""Build a portable, minimized audit bundle for governed decisions."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from governance_hardening import canonical_json, fingerprint, redact_sensitive


def build_audit_bundle(*, envelope: Mapping[str, Any], decision: Mapping[str, Any], evidence: Mapping[str, Any], policy_result: Mapping[str, Any], approval: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(envelope, Mapping) or not isinstance(decision, Mapping) or not isinstance(evidence, Mapping) or not isinstance(policy_result, Mapping):
        raise ValueError("envelope, decision, evidence, and policy_result must be mappings")
    safe_evidence = redact_sensitive(evidence)
    bundle = {
        "bundle_schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "envelope": dict(envelope),
        "decision": redact_sensitive(decision),
        "evidence": safe_evidence,
        "policy": redact_sensitive(policy_result),
        "approval": redact_sensitive(dict(approval)) if approval is not None else None,
    }
    bundle["audit_fingerprint"] = fingerprint(bundle)
    return bundle


def verify_audit_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, Mapping):
        raise ValueError("bundle must be a mapping")
    supplied = bundle.get("audit_fingerprint")
    if not isinstance(supplied, str) or len(supplied) != 64:
        return {"valid": False, "reason": "missing_or_invalid_fingerprint"}
    payload = {key: value for key, value in bundle.items() if key != "audit_fingerprint"}
    calculated = fingerprint(payload)
    return {"valid": supplied == calculated, "supplied": supplied, "calculated": calculated}


def export_audit_bundle_json(bundle: Mapping[str, Any]) -> str:
    """Canonical JSON export suitable for deterministic archival."""
    return canonical_json(bundle)
