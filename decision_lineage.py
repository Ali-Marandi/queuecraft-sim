"""QueueCraft decision lineage graph.

Builds a deterministic provenance graph connecting data, models, scenarios,
experiments, decisions, approvals, evidence, and replays. This is provenance
metadata, not causal inference and not a deployment mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

NODE_TYPES = ("data", "model", "scenario", "experiment", "decision", "approval", "replay", "evidence")
EDGE_TYPES = ("uses", "derived_from", "evaluated_by", "approved_by", "replayed_from", "contains", "supports")


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LineageNode:
    node_id: str
    node_type: str
    label: str
    fingerprint: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class LineageEdge:
    edge_id: str
    from_id: str
    to_id: str
    edge_type: str
    metadata: dict[str, Any] | None = None


def _validate_node(node: Mapping[str, Any]) -> None:
    if not node.get("id") or node.get("type") not in NODE_TYPES:
        raise ValueError("each node requires an id and supported type")


def _validate_edge(edge: Mapping[str, Any], node_ids: set[str]) -> None:
    if not edge.get("from") or not edge.get("to"):
        raise ValueError("each edge requires from and to")
    if edge["from"] not in node_ids or edge["to"] not in node_ids:
        raise ValueError(f"unknown lineage endpoint: {edge.get('from')}->{edge.get('to')}")
    if edge.get("type") not in EDGE_TYPES:
        raise ValueError("unsupported lineage edge type")


def _assert_acyclic(edges: Sequence[LineageEdge], node_ids: set[str]) -> None:
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    indegree: dict[str, int] = {node_id: 0 for node_id in node_ids}
    for edge in edges:
        adjacency[edge.from_id].append(edge.to_id)
        indegree[edge.to_id] += 1
    queue = [node_id for node_id, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        current = queue.pop(0)
        visited += 1
        for child in adjacency[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if visited != len(node_ids):
        raise ValueError("lineage graph must be acyclic")


def build_lineage_graph(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_nodes: list[LineageNode] = []
    node_ids: set[str] = set()
    for raw in nodes:
        _validate_node(raw)
        node_id = str(raw["id"])
        if node_id in node_ids:
            raise ValueError(f"duplicate lineage node: {node_id}")
        node_ids.add(node_id)
        normalized_nodes.append(LineageNode(node_id, str(raw["type"]), str(raw.get("label", node_id)), raw.get("fingerprint"), dict(raw.get("metadata", {}))))

    normalized_edges: list[LineageEdge] = []
    for index, raw in enumerate(edges):
        _validate_edge(raw, node_ids)
        edge_id = str(raw.get("id", fingerprint({"from": raw["from"], "to": raw["to"], "type": raw["type"], "i": index})[:16]))
        normalized_edges.append(LineageEdge(edge_id, str(raw["from"]), str(raw["to"]), str(raw["type"]), dict(raw.get("metadata", {}))))
    _assert_acyclic(normalized_edges, node_ids)

    adjacency: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    reverse: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in normalized_edges:
        adjacency[edge.from_id].append(edge.to_id)
        reverse[edge.to_id].append(edge.from_id)

    payload = {"nodes": [asdict(n) for n in normalized_nodes], "edges": [asdict(e) for e in normalized_edges]}
    return {
        **payload,
        "node_count": len(normalized_nodes),
        "edge_count": len(normalized_edges),
        "roots": sorted(node_id for node_id, parents in reverse.items() if not parents),
        "leaves": sorted(node_id for node_id, children in adjacency.items() if not children),
        "graph_fingerprint": fingerprint(payload),
        "governance": {"causal_inference": False, "deployment_side_effects": False},
    }


def _walk(graph: Mapping[str, Any], start_id: str, direction: str, max_depth: int) -> list[str]:
    nodes = {str(n["node_id"]) for n in graph.get("nodes", [])}
    if start_id not in nodes:
        raise ValueError(f"unknown lineage node: {start_id}")
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in nodes}
    for edge in graph.get("edges", []):
        if direction == "ancestors":
            adjacency[str(edge["to_id"])].append(str(edge["from_id"]))
        else:
            adjacency[str(edge["from_id"])].append(str(edge["to_id"]))
    visited: set[str] = set()
    frontier = [(start_id, 0)]
    while frontier:
        current, depth = frontier.pop(0)
        if depth >= max_depth:
            continue
        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append((neighbor, depth + 1))
    return sorted(visited)


def lineage_subgraph(graph: Mapping[str, Any], node_id: str, *, direction: str = "ancestors", max_depth: int = 10) -> dict[str, Any]:
    if direction not in ("ancestors", "descendants"):
        raise ValueError("direction must be ancestors or descendants")
    if max_depth < 1:
        raise ValueError("max_depth must be positive")
    selected = {node_id, *_walk(graph, node_id, direction, max_depth)}
    nodes = [node for node in graph.get("nodes", []) if node.get("node_id") in selected]
    edges = [edge for edge in graph.get("edges", []) if edge.get("from_id") in selected and edge.get("to_id") in selected]
    return {"root": node_id, "direction": direction, "nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


def build_lineage_from_evidence(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Infer provenance links from common evidence-pack fields without inventing missing entities."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    decision = evidence.get("decision")
    decision_id = str(evidence.get("decision_id", "decision")) if decision is not None else None
    if decision is not None:
        nodes.append({"id": decision_id, "type": "decision", "label": "Decision", "fingerprint": fingerprint(decision)})
    scenario_id = evidence.get("scenario_id")
    if scenario_id:
        scenario_id = str(scenario_id)
        nodes.append({"id": scenario_id, "type": "scenario", "label": scenario_id, "fingerprint": evidence.get("scenario_fingerprint")})
        if decision_id:
            edges.append({"from": scenario_id, "to": decision_id, "type": "supports"})
    experiment = evidence.get("experiment")
    exp_id = None
    if isinstance(experiment, Mapping) and experiment:
        exp_id = str(evidence.get("experiment_id", "experiment"))
        nodes.append({"id": exp_id, "type": "experiment", "label": exp_id, "fingerprint": fingerprint(experiment)})
        if decision_id:
            edges.append({"from": exp_id, "to": decision_id, "type": "supports"})
    approval = evidence.get("approval")
    if isinstance(approval, Mapping) and approval.get("id"):
        approval_id = str(approval["id"])
        nodes.append({"id": approval_id, "type": "approval", "label": approval_id, "metadata": dict(approval)})
        if decision_id:
            edges.append({"from": approval_id, "to": decision_id, "type": "approved_by"})
    models = evidence.get("models", evidence.get("model_versions", []))
    for index, model in enumerate(models if isinstance(models, list) else []):
        if isinstance(model, Mapping):
            model_id = str(model.get("model_id", model.get("id", f"model-{index}")))
            nodes.append({"id": model_id, "type": "model", "label": model_id, "fingerprint": model.get("evidence_fingerprint"), "metadata": dict(model)})
            if decision_id:
                edges.append({"from": model_id, "to": decision_id, "type": "uses"})
            if exp_id:
                edges.append({"from": model_id, "to": exp_id, "type": "evaluated_by"})
    source_data = evidence.get("source_data", evidence.get("data_assets", []))
    for index, data in enumerate(source_data if isinstance(source_data, list) else []):
        if isinstance(data, Mapping):
            data_id = str(data.get("asset_id", data.get("id", f"data-{index}")))
            nodes.append({"id": data_id, "type": "data", "label": data_id, "fingerprint": data.get("fingerprint"), "metadata": dict(data)})
            if decision_id:
                edges.append({"from": data_id, "to": decision_id, "type": "derived_from"})
    replay = evidence.get("replay")
    if isinstance(replay, Mapping) and replay:
        replay_id = str(evidence.get("replay_id", "replay"))
        nodes.append({"id": replay_id, "type": "replay", "label": replay_id, "fingerprint": replay.get("replay_fingerprint"), "metadata": dict(replay)})
        if decision_id:
            edges.append({"from": replay_id, "to": decision_id, "type": "replayed_from"})
    return build_lineage_graph(nodes, edges)
