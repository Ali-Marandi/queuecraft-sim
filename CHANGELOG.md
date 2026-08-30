# Changelog

## v3.15.0 — Governed Decision Platform

### Added

- Added a deterministic Decision Lineage Graph connecting data, models, scenarios, experiments, decisions, approvals, evidence, and replays.
- Added typed provenance edges with ancestor/descendant traversal and graph fingerprints.
- Added cycle detection so lineage graphs remain acyclic and queryable.
- Embedded lineage into governance evidence packs.
- Added a lineage JSON service contract and dedicated verification suite.
- Refreshed the README to document model lifecycle, drift monitoring, continuous evaluation, observability, replay, governance, and lineage capabilities.

### Governance

- Evidence packages now carry provenance context alongside assumptions, model metadata, experiments, and approval state.
- Replay, drift, promotion, and lineage remain advisory controls; no analytics layer performs external deployment or operational mutation.

### Quality

- Added lineage coverage for model-to-experiment, scenario-to-decision, approval, replay, duplicate-node, unknown-endpoint, and cycle cases.
- Added `npm run test:lineage` and included lineage tests in `test:ai`.
