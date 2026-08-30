# QueueCraft Decision Lineage v1

QueueCraft now exposes a deterministic provenance graph that connects the artifacts participating in a decision.

## Node types

- `data`: source data assets or normalized observations
- `model`: model identity/version records
- `scenario`: saved or executed scenario definitions
- `experiment`: statistical comparison or validation result
- `decision`: operational recommendation or decision record
- `approval`: human governance record
- `replay`: replay artifact
- `evidence`: packaged evidence bundle

## Edge types

`uses`, `derived_from`, `evaluated_by`, `approved_by`, `replayed_from`, `contains`, and `supports` describe provenance relationships. They do not assert causal identification.

## Query

Use `lineage_subgraph(graph, node_id, direction="ancestors")` to inspect the evidence feeding a decision, or `direction="descendants"` to see downstream artifacts.

The graph has its own SHA-256 fingerprint and can be embedded into an evidence package. The graph is local/offline-first and performs no deployment or external mutation.

## Service

`decision_lineage_service.lineage_json()` accepts either explicit nodes/edges or an evidence package and returns a normalized graph. A focused subgraph can be requested with `node_id`, `direction`, and `max_depth`.
