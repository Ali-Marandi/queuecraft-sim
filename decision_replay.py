"""Deterministic decision replay and comparison helpers for QueueCraft."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ReplayResult:
    status: str
    original_fingerprint: str
    replay_fingerprint: str
    identical: bool
    changed_fields: tuple[str, ...]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "original_fingerprint": self.original_fingerprint,
            "replay_fingerprint": self.replay_fingerprint,
            "identical": self.identical,
            "changed_fields": list(self.changed_fields),
            "notes": list(self.notes),
        }


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.update(_flatten(item, path))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            result.update(_flatten(item, f"{prefix}[{index}]") )
        return result
    return {prefix: value}


def compare_records(original: Any, replayed: Any) -> tuple[bool, tuple[str, ...]]:
    left = _flatten(original)
    right = _flatten(replayed)
    changed = sorted(set(left) | set(right))
    changed = tuple(path for path in changed if left.get(path) != right.get(path))
    return not changed, changed


def replay_decision(
    evidence: dict[str, Any],
    executor: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    expected_fingerprint: str | None = None,
) -> ReplayResult:
    """Replay a local decision package and compare the resulting record.

    The executor must be deterministic for an identical evidence package.
    No external side effects are performed by this helper itself.
    """
    if not isinstance(evidence, dict):
        raise ValueError("evidence must be an object")
    original = evidence.get("decision", evidence.get("result", evidence))
    original_fp = expected_fingerprint or fingerprint(original)
    replayed = executor(evidence)
    if not isinstance(replayed, dict):
        raise ValueError("executor must return an object")
    replay_fp = fingerprint(replayed)
    identical, changed = compare_records(original, replayed)
    notes: list[str] = []
    stored = evidence.get("decision_fingerprint")
    if stored and stored != original_fp:
        notes.append("stored decision fingerprint differs from the evidence-derived fingerprint")
    if identical and stored and stored != replay_fp:
        notes.append("replay matches the supplied decision record, but not its stored fingerprint")
    return ReplayResult(
        status="identical" if identical else "diverged",
        original_fingerprint=original_fp,
        replay_fingerprint=replay_fp,
        identical=identical,
        changed_fields=changed,
        notes=tuple(notes),
    )


def replay_snapshot(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, side-effect-free summary suitable for a replay UI."""
    decision = evidence.get("decision", evidence.get("result", evidence))
    return {
        "evidence_fingerprint": fingerprint(evidence),
        "decision_fingerprint": fingerprint(decision),
        "model_versions": evidence.get("model_versions", evidence.get("models", [])),
        "assumptions": evidence.get("assumptions", {}),
        "seed": evidence.get("seed"),
        "scenario_id": evidence.get("scenario_id"),
        "replay_supported": True,
    }
