"""QueueCraft Scenario Intelligence 2.0.

Bridges market-intelligence inputs to QueueCraft operational scenarios without
pretending that the relationship is causal unless the operator supplies an
explicit scenario linkage. All outputs are deterministic and auditable.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from decision_engine import build_decision_package
from market_intelligence import analyze_market_snapshot


def _fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def build_scenario_graph(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Evaluate a bounded directed scenario graph using operator-supplied weights."""
    node_map = {str(n["id"]): dict(n) for n in nodes}
    scores = {node_id: float(node.get("shock", 0.0)) for node_id, node in node_map.items()}
    normalized_edges = []
    for edge in edges:
        src = str(edge["from"])
        dst = str(edge["to"])
        if src not in node_map or dst not in node_map:
            raise ValueError(f"unknown scenario graph node: {src}->{dst}")
        weight = float(edge.get("weight", 0.0))
        normalized_edges.append({"from": src, "to": dst, "weight": weight})
    for _ in range(max(1, len(node_map))):
        updates = dict(scores)
        for edge in normalized_edges:
            updates[edge["to"]] += scores[edge["from"]] * edge["weight"]
        scores = {k: float(max(-10.0, min(10.0, v))) for k, v in updates.items()}
    ranked = sorted(scores.items(), key=lambda item: abs(item[1]), reverse=True)
    return {
        "nodes": list(node_map.values()),
        "edges": normalized_edges,
        "scores": scores,
        "ranking": [{"node": k, "score": round(v, 6)} for k, v in ranked],
        "disclaimer": "Graph propagation is scenario logic, not an empirically identified causal model.",
    }


def counterfactual_scale(history: Sequence[float], demand_multiplier: float = 1.0, service_time_multiplier: float = 1.0) -> list[float]:
    """Create a transparent counterfactual demand path from supplied history."""
    if demand_multiplier <= 0 or service_time_multiplier <= 0:
        raise ValueError("counterfactual multipliers must be positive")
    # Service time affects operational load rather than arrivals; expose an
    # equivalent-load path so the comparison remains deterministic and clear.
    return [float(x) * demand_multiplier * service_time_multiplier for x in history]


def governance_manifest(*, inputs: Mapping[str, Any], models: Sequence[str], assumptions: Sequence[str], ai_enabled: bool = False) -> dict[str, Any]:
    """Return an auditable governance manifest for a scenario run."""
    manifest = {
        "schema_version": "2.0",
        "models": list(models),
        "assumptions": list(assumptions),
        "input_keys": sorted(inputs),
        "ai_enabled": bool(ai_enabled),
        "controls": {
            "human_approval_required": True,
            "external_operations_performed": False,
            "default_outbound_telemetry": False,
            "decision_source_restricted_to_evaluated_candidates": True,
        },
    }
    manifest["manifest_fingerprint"] = _fingerprint(manifest)
    return manifest


def run_integrated_scenario(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Run market + operational analysis, graph propagation and counterfactuals."""
    market = analyze_market_snapshot(payload["market"])
    queue = build_decision_package(
        payload["operational"]["historical_counts"],
        payload["operational"]["tiers"],
        sla_mean_wait=payload["operational"].get("sla_mean_wait", 5.0),
        cost_per_server=float(payload["operational"].get("cost_per_server", 1.0)),
        server_range=tuple(payload["operational"].get("server_range", [1, 6])),
        replications=int(payload["operational"].get("replications", 100)),
        seed=payload["operational"].get("seed", 42),
        arrival_multipliers=payload["operational"].get("arrival_multipliers", [0.8, 1.0, 1.2]),
        service_time_multipliers=payload["operational"].get("service_time_multipliers", [0.8, 1.0, 1.2]),
        enable_llm=bool(payload.get("enable_llm", False)),
    )
    graph = build_scenario_graph(payload.get("graph", {}).get("nodes", []), payload.get("graph", {}).get("edges", []))
    cf = payload.get("counterfactual", {})
    base_history = payload["operational"]["historical_counts"]
    cf_history = counterfactual_scale(
        base_history,
        float(cf.get("demand_multiplier", 1.0)),
        float(cf.get("service_time_multiplier", 1.0)),
    )
    governance = governance_manifest(
        inputs=payload,
        models=["market_intelligence", "decision_engine", "scenario_graph", "counterfactual_scale"],
        assumptions=[
            "Market-to-operations edges are operator-specified scenario links.",
            "Counterfactual scaling is a stress transformation, not a causal estimate.",
            "LLM output cannot create an operational action outside the evaluated candidate catalog.",
        ],
        ai_enabled=bool(payload.get("enable_llm", False)),
    )
    result = {
        "engine_version": "2.0.0",
        "market": market,
        "operations": queue,
        "scenario_graph": graph,
        "counterfactual": {
            "transformed_history": cf_history,
            "demand_multiplier": float(cf.get("demand_multiplier", 1.0)),
            "service_time_multiplier": float(cf.get("service_time_multiplier", 1.0)),
        },
        "governance": governance,
        "disclaimer": "Integrated scenario analysis for decision support only; not investment advice or a trading system.",
    }
    result["scenario_fingerprint"] = _fingerprint(result)
    return result
