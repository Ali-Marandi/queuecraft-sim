"""Classify likely sources of divergence between a stored and replayed decision."""
from __future__ import annotations

from typing import Iterable


def classify_changed_fields(changed_fields: Iterable[str]) -> dict[str, object]:
    fields = sorted(set(changed_fields))
    categories = {
        "data": [],
        "model": [],
        "assumption": [],
        "execution": [],
        "other": [],
    }
    for field in fields:
        lower = field.lower()
        if any(token in lower for token in ("data", "input", "actual", "history")):
            categories["data"].append(field)
        elif any(token in lower for token in ("model", "version", "algorithm")):
            categories["model"].append(field)
        elif any(token in lower for token in ("assumption", "threshold", "constraint", "sla")):
            categories["assumption"].append(field)
        elif any(token in lower for token in ("seed", "random", "simulation", "replication")):
            categories["execution"].append(field)
        else:
            categories["other"].append(field)
    ranked = sorted(
        ((name, len(values)) for name, values in categories.items() if values),
        key=lambda item: (-item[1], item[0]),
    )
    return {
        "changed_field_count": len(fields),
        "categories": categories,
        "primary_category": ranked[0][0] if ranked else None,
        "diagnosis_confidence": "heuristic",
    }
