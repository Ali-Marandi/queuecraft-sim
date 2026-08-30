# QueueCraft Enterprise AI

<div align="center">

![QueueCraft](https://img.shields.io/badge/QueueCraft-Enterprise%20AI%20v3.15-4f46e5?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-16a34a?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20x64-2563eb?style=for-the-badge)

**Enterprise simulation, scenario intelligence, governed model evaluation, and auditable decision support.**

</div>

## Overview

QueueCraft Enterprise AI is an offline-first desktop decision-support suite for service operations, capacity planning, resilience engineering, and cross-disciplinary scenario analysis. It combines deterministic and stochastic queue simulation with market-intelligence analytics, stress testing, governed model lifecycle controls, replay, and provenance tracking so operators can evaluate a decision before any operational change is approved.

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
| Streaming Drift | Reference/current window monitoring with challenger-evaluation triggers; deployment remains blocked |
| Continuous Evaluation | Primary-metric improvement checks plus protected-metric regression guardrails |
| Observability | Append-only local decision ledger, hash chaining, integrity verification, event timeline queries |
| Decision Replay | Deterministic replay contract, fingerprint comparison, field-level divergence, and heuristic diagnosis |
| Decision Lineage | Typed provenance graph linking data, models, scenarios, experiments, decisions, approvals, evidence, and replays |
| Governed Evidence Packs | Portable evidence packages with data/model metadata, assumptions, experiment details, approval state, and embedded lineage |
| Commercial workspace and reporting | Browse, run, delete, and export fingerprint-verified saved scenarios as portable audit-ready JSON reports |
| Localization foundation | English and Persian interface vocabulary with persistent language selection and RTL support |
| Offline-ready desktop bundle | Locally bundled chart/CSS assets, PyInstaller runtime collection, Inno Setup installer definition, and release workflow |

## Verification

The repository maintains separate commands for major control layers:

```bash
npm test
npm run test:ai
npm run test:market
npm run test:scenario-intelligence
npm run test:experiments
npm run test:model-lifecycle
npm run test:validation
npm run test:drift
npm run test:challenger
npm run test:evaluation
npm run test:observability
npm run test:replay
npm run test:lineage
```

The GitHub Actions workflow runs Node.js and Python verification across its configured version matrix. CI status should be treated as authoritative for the specific commit being evaluated.

## Decision Lineage

A decision can now be represented as a provenance chain:

```text
Data → Model → Scenario → Experiment → Decision → Approval → Replay
```

`decision_lineage.py` provides a deterministic graph representation and focused ancestor/descendant queries. `governance_layer.build_evidence_pack()` embeds the resulting graph into the evidence package.

## Replay and Governance Boundary

Replay proves that a supplied deterministic execution path reproduces or diverges from a stored decision record. It does not establish model correctness or causal validity. Drift, risk, lineage, and diagnostic signals are decision-support controls rather than guarantees.

QueueCraft does not automatically deploy, trade, scale infrastructure, or mutate external systems through these analytics and governance layers. Human approval remains required for governed promotion and operational action.

## Quick Start

```bash
git clone https://github.com/Ali-Marandi/queuecraft-sim.git
cd queuecraft-sim
python -m pip install -r requirements.txt
python app.py
```

### Scenario Intelligence 2.0

```bash
python scenario_intelligence_cli.py examples/integrated_scenario_intelligence.json \
  --output artifacts/integrated-scenario.json
```

### Decision Replay

```bash
python decision_replay_service.py examples/decision_replay.json
```

### Decision Lineage

```bash
python decision_lineage_service.py examples/integrated_scenario_intelligence.json
```

## Research Boundary

Research-only families such as DSGE, causal ML, topological data analysis, diffusion finance, quantum finance, federated learning, and ANFIS remain separated from the executable analytics layer until they have dedicated calibration, validation, and governance.

## Security and Privacy

Local analytics are offline-first. Credentials and local environment files are excluded by `.gitignore`, outbound telemetry is not enabled by default, and governance/replay helpers do not perform external operational actions. These controls do not replace an enterprise security review.

## Commercial Roadmap

Future enterprise layers can add signed scenario packages, role-aware workspaces, PDF/XLSX reporting, encrypted local stores, SSO/RBAC, centralized catalogues, and reviewed read-only connectors. Such integrations should preserve the existing least-privilege and human-approval boundaries.

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE).
