# QueueCraft Enterprise AI

<div align="center">

![QueueCraft](https://img.shields.io/badge/QueueCraft-Enterprise%20AI%20v3.22-4f46e5?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-16a34a?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20x64-2563eb?style=for-the-badge)

**Enterprise simulation, scenario intelligence, governed model evaluation, policy workflows, and auditable decision support.**

</div>

## Overview

QueueCraft Enterprise AI is an offline-first desktop decision-support suite for service operations, capacity planning, resilience engineering, and cross-disciplinary scenario analysis. It combines deterministic and stochastic queue simulation with market-intelligence analytics, stress testing, governed model lifecycle controls, replay, provenance tracking, policy evaluation, human approval workflows, enterprise data contracts, distributed execution, and integrated model governance so operators can evaluate a decision before any operational change is approved.

## Current Enterprise Capabilities

| Capability | What it delivers |
|---|---|
| Deterministic and stochastic modeling | Reproducible baselines alongside sampled arrivals and service-time variation |
| Multi-tier queue pipelines | Serial stage modeling in which departures from one tier become arrivals for the next tier |
| Decision Engine | Benchmark, Pareto optimization, sensitivity analysis, screening risk, recommendations, and auditable fingerprints |
| Scenario Intelligence 2.0 | Market-to-operations scenario graph, explicit counterfactual stress paths, governance manifest, and scenario fingerprint |
| Market Intelligence | Taylor-style macro benchmark, CAPM/factor regression, GARCH(1,1), Altman Z, Beneish M, Black-Litterman, contagion, behavioral/fuzzy/TOPSIS and stress scenarios |
| Walk-forward validation | Chronological folds, rolling performance metrics, regime classification, and regime-aware model selection |
| Model Lifecycle | Calibration, drift screening, champion/challenger comparison, model registry, and explicit promotion gates |
| Integrated Model Governance | One report spanning validation, candidate comparison, continuous evaluation, promotion eligibility, and human-approval boundary |
| Streaming Drift | Reference/current window monitoring with challenger-evaluation triggers; deployment remains blocked |
| Continuous Evaluation | Primary-metric improvement checks plus protected-metric regression guardrails |
| Enterprise Data Plane | Versioned schemas, validation profiles, dataset manifests, deterministic cache keys, and reproducible run bundles |
| Distributed Execution | Bounded parallel replication, deterministic task identity, checkpoint/resume, cancellation, and progress reporting |
| Security Controls | Deny-by-default authorization, role/permission evaluation, operation risk classification, and automatic external-side-effect blocking |
| Observability | Append-only local decision ledger, hash chaining, integrity verification, event timeline queries |
| Decision Replay | Deterministic replay contract, fingerprint comparison, field-level divergence, and heuristic diagnosis |
| Decision Lineage | Typed provenance graph linking data, models, scenarios, experiments, decisions, approvals, evidence, and replays |
| Governed Evidence Packs | Portable evidence packages with data/model metadata, assumptions, experiment details, approval state, and embedded lineage |
| Policy Engine | Declarative allow/review/block rules with deterministic precedence and auditable rule matches |
| Approval Workflow | Explicit human reviewer role, state transitions, notes, and deployment-side-effect guard |
| Audit Bundles | Fingerprinted, minimized, redacted decision packages suitable for deterministic local archival |
| Decision Readiness | Final READY / REVIEW / BLOCK control boundary for governed decisions |
| Commercial workspace and reporting | Browse, run, delete, and export fingerprint-verified saved scenarios as portable audit-ready JSON reports |
| Localization foundation | English and Persian interface vocabulary with persistent language selection and RTL support |
| Offline-ready desktop bundle | Locally bundled chart/CSS assets, PyInstaller runtime collection, Inno Setup installer definition, and release workflow |

## Verification

```bash
npm test
npm run test:ai
npm run test:enterprise
npm run test:model-governance
npm run test:market
npm run test:scenario-intelligence
npm run test:experiments
npm run test:governance
npm run test:validation
npm run test:drift
npm run test:challenger
npm run test:evaluation
npm run test:observability
npm run test:replay
npm run test:lineage
npm run test:policy
npm run test:approval
```

CI status should be treated as authoritative for the specific commit being evaluated.

## Governance Flow

```text
Data → Model → Scenario → Experiment → Decision
                                      ↓
                                   Policy
                                      ↓
                              Evidence / Audit
                                      ↓
                            Human Approval
                                      ↓
                              Readiness Gate
                               ↙         ↘
                           READY       REVIEW/BLOCK
                               ↓
                          Replay / Audit
```

`policy_engine.py` is deterministic and side-effect free. `approval_workflow.py` requires explicit human identity and role for approval/rejection, and does not deploy anything. `model_governance.py` composes validation, comparison, evaluation, and promotion eligibility without performing deployment.

## Decision Lineage

A decision is represented as provenance metadata:

```text
Data → Model → Scenario → Experiment → Decision → Approval → Replay
```

`decision_lineage.py` provides a deterministic graph representation, cycle detection, and focused ancestor/descendant queries. `governance_layer.build_evidence_pack()` embeds the resulting graph into the evidence package.

## Replay and Governance Boundary

Replay proves that a supplied deterministic execution path reproduces or diverges from a stored decision record. It does not establish model correctness or causal validity. Drift, risk, lineage, diagnostic, and policy signals are decision-support controls rather than guarantees.

QueueCraft does not automatically deploy, trade, scale infrastructure, or mutate external systems through these analytics and governance layers. Human approval remains required for governed promotion and operational action.

## Quick Start

```bash
git clone https://github.com/Ali-Marandi/queuecraft-sim.git
cd queuecraft-sim
python -m pip install -r requirements.txt
python app.py
```

### Decision Replay

```bash
python decision_replay_service.py examples/decision_replay.json
```

### Decision Lineage

```bash
python decision_lineage_service.py examples/integrated_scenario_intelligence.json
```

### Integrated Model Governance

The local JSON service accepts a deterministic built-in model catalog and returns validation, challenger, evaluation, and promotion-gate evidence without allowing model execution outside the approved catalog.

```text
model_governance_service.py
        ↓
walk-forward validation
        ↓
candidate comparison
        ↓
continuous evaluation
        ↓
promotion gate
        ↓
human approval boundary
```

## Research Boundary

Research-only families such as DSGE, causal ML, topological data analysis, diffusion finance, quantum finance, federated learning, and ANFIS remain separated from the executable analytics layer until they have dedicated calibration, validation, and governance.

## Security and Privacy

Local analytics are offline-first. Credentials and local environment files are excluded by `.gitignore`, outbound telemetry is not enabled by default, and governance/replay helpers do not perform external operational actions. Decision artifacts use deterministic fingerprints and export-boundary redaction where appropriate. These controls do not replace an enterprise security review.

## Commercial Roadmap

Future enterprise layers can add signed scenario packages, role-aware workspaces, SSO/RBAC integrations, centralized catalogues, reviewed read-only connectors, richer performance telemetry, multi-tenant server-side governance, and external evidence stores. Such integrations should preserve the existing least-privilege and human-approval boundaries.

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE).
