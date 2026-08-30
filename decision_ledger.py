"""Append-only local decision ledger for QueueCraft observability and audit trails."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    event_type: str
    created_at: float
    payload: dict[str, Any]
    previous_hash: str | None
    event_hash: str


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class DecisionLedger:
    """Small append-only JSONL ledger with tamper-evident hash chaining."""

    def __init__(self, path: str | Path = "artifacts/decision-ledger.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str | None:
        if not self.path.exists():
            return None
        last: str | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = json.loads(line)["event_hash"]
        return last

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous_hash = self._last_hash()
        created_at = time.time()
        event_id = hashlib.sha256(f"{created_at}:{event_type}:{previous_hash}".encode()).hexdigest()[:16]
        core = {
            "event_id": event_id,
            "event_type": event_type,
            "created_at": created_at,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        event_hash = hashlib.sha256(_canonical(core).encode()).hexdigest()
        event = LedgerEvent(event_hash=event_hash, **core)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(_canonical(asdict(event)) + "\n")
        return asdict(event)

    def read(self, limit: int = 200) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("limit must be positive")
        if not self.path.exists():
            return []
        events = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return events[-limit:]

    def verify(self) -> dict[str, Any]:
        events = self.read(limit=10_000_000)
        previous_hash: str | None = None
        for index, event in enumerate(events):
            expected_core = {key: event[key] for key in ("event_id", "event_type", "created_at", "payload", "previous_hash")}
            expected_hash = hashlib.sha256(_canonical(expected_core).encode()).hexdigest()
            if event["previous_hash"] != previous_hash or event["event_hash"] != expected_hash:
                return {"valid": False, "checked": index + 1, "failed_event_id": event.get("event_id")}
            previous_hash = event["event_hash"]
        return {"valid": True, "checked": len(events), "last_hash": previous_hash}
