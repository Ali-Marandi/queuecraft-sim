"""Query and summarize QueueCraft decision-ledger events."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from decision_ledger import DecisionLedger


def timeline_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(event.get("event_type", "unknown")) for event in events)
    return {
        "event_count": len(events),
        "event_types": dict(sorted(counts.items())),
        "integrity_ready": all("event_hash" in event and "created_at" in event for event in events),
    }


def query_ledger(
    path: str | Path = "artifacts/decision-ledger.jsonl",
    *,
    event_type: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    ledger = DecisionLedger(path)
    events = ledger.read(limit=limit)
    if event_type:
        events = [event for event in events if event.get("event_type") == event_type]
    return {"events": events, "summary": timeline_summary(events), "integrity": ledger.verify()}
