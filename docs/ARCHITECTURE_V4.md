# QueueCraft Architecture v4

## Purpose

QueueCraft is evolving from a collection of analytics into a governed decision platform. The architecture is organized around one invariant: **every important decision must be reproducible, attributable, reviewable, and exportable without granting the analytics layer operational authority**.

## Core control plane

```text
Data
  ↓
Data Manifest ── Quality / Schema / Fingerprint
  ↓
Model Registry ── Version / Validation / Drift / Challenger
  ↓
Scenario ── Assumptions / Counterfactuals / Fingerprint
  ↓
Experiment ── Seed / Configuration / Metrics / Run Bundle
  ↓
Decision ── Recommendation / Risk / Decision Fingerprint
  ↓
Policy Engine ── allow / review / block
  ↓
Evidence ── Lineage / Provenance / Integrity
  ↓
Human Approval ── identity / role / review note
  ↓
Readiness Gate ── READY / REVIEW / BLOCK
  ↓
Replay / Audit / Export
```

## Design invariants

1. Analytics are side-effect free. They produce evidence and recommendations, not operational mutations.
2. Deterministic inputs are fingerprinted before they become part of a governed run.
3. Policy decisions are explicit and auditable.
4. Human approval is represented as a first-class artifact when required.
5. Readiness is fail-closed for identity, evidence, policy-block, and approval failures.
6. Replay is evidence of execution reproducibility; it is not proof of causal validity or business correctness.
7. Sensitive values are redacted at export boundaries rather than silently persisted in governance metadata.

## Readiness semantics

`decision_readiness.py` provides the final pre-action control boundary. A decision can be:

- `READY`: all required controls pass.
- `REVIEW`: no hard failure exists, but an explicit human or freshness review remains necessary.
- `BLOCK`: at least one hard control has failed.

The readiness gate verifies decision/evidence fingerprints, required evidence fields, freshness, policy outcome, and approval state.

## Extension points

Future work should add signed evidence packages, stronger identity binding, RBAC-aware approval policy, immutable event stores, workload isolation, performance telemetry, and reviewed read-only external connectors. These layers must preserve the control-plane invariants above.
