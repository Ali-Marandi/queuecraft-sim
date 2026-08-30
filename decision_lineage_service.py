"""JSON service contract for QueueCraft decision lineage."""
from __future__ import annotations

import json
from typing import Any

from decision_lineage import build_lineage_from_evidence, lineage_subgraph


def build_lineage(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if "nodes" in payload:
        graph = __import__("decision_lineage").build_lineage_graph(payload.get("nodes", []), payload.get("edges", []))
    else:
        graph = build_lineage_from_evidence(payload)
    if "node_id" in payload:
        graph["focus"] = lineage_subgraph(
            graph,
            str(payload["node_id"]),
            direction=str(payload.get("direction", "ancestors")),
            max_depth=int(payload.get("max_depth", 10)),
        )
    return graph


def lineage_json(payload_json: str) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        return json.dumps(build_lineage(payload), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)


if __name__ == "__main__":
    import sys
    payload = sys.stdin.read() if len(sys.argv) == 1 else open(sys.argv[1], encoding="utf-8").read()
    print(lineage_json(payload))
