# QueueCraft Governance & Evidence v1

QueueCraft now supports an offline governance layer around scenario decisions.

## Lineage

A decision can reference explicit data assets, model records, assumptions, experiments, and the resulting decision package. Each evidence pack carries a SHA-256 fingerprint over its canonical JSON representation.

## Data quality

`data_quality_score()` reports completeness, basic validity, a bounded 0–1 score, and a human-readable status. It is a screening metric, not a statistical guarantee of data fitness.

## Model registry

`ModelRecord` captures model id, family, version, purpose, validation status, and limitations. This keeps model identity separate from scenario inputs.

## Evidence pack

`build_evidence_pack()` produces a portable record containing:

- decision output and decision fingerprint
- source data assets and quality metadata
- model identities and limitations
- assumptions
- optional experiment result
- approval state
- evidence fingerprint

The pack is immutable-by-convention: changing any covered field changes its fingerprint.

## CLI

```bash
python governance_cli.py examples/integrated_scenario_intelligence.json --output artifacts/evidence-pack.json
```

The command does not send data externally and does not apply operational changes.

## Trust boundary

Market analytics, scenario intelligence, and AI explanations are advisory. Operational changes remain outside the simulation path and require explicit human approval.
