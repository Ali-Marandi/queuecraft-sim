"""Human-readable diff reporting for QueueCraft replay results."""
from __future__ import annotations

from typing import Any

from decision_replay import compare_records


def build_replay_diff_report(original: dict[str, Any], replayed: dict[str, Any]) -> dict[str, Any]:
    identical, changed = compare_records(original, replayed)
    return {
        "status": "identical" if identical else "diverged",
        "changed_field_count": len(changed),
        "changed_fields": list(changed),
        "recommendation": "reusable" if identical else "investigate",
        "scope": "decision_record",
    }
