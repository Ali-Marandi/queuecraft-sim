# QueueCraft Enterprise AI

<div align="center">

![QueueCraft](https://img.shields.io/badge/QueueCraft-Enterprise%20AI%20v3.4-4f46e5?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-16a34a?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20x64-2563eb?style=for-the-badge)

**Enterprise queue simulation, market intelligence, scenario stress-testing, and auditable decision support.**

</div>

## Overview

QueueCraft Enterprise AI is an offline-first desktop decision-support suite for service operations, capacity planning, resilience engineering, and cross-disciplinary scenario analysis. It combines deterministic and stochastic queue simulation with market-intelligence analytics so operators can model a full stress chain before any operational change is approved.

## Current Enterprise Capabilities

| Capability | What it delivers |
|---|---|
| Deterministic and stochastic modeling | Reproducible baselines alongside sampled arrivals and service-time variation |
| Multi-tier queue pipelines | Serial stage modeling in which departures from one tier become arrivals for the next tier |
| AI-informed Monte Carlo risk analysis | Demand forecasting plus repeated stochastic simulation with expected and P95 wait metrics |
| Cost-aware Auto-Scaling | Capacity recommendation under configurable wait-time SLA and per-server cost assumptions |
| Advanced queue policy model | Non-preemptive priority classes, finite waiting capacity, rejection, abandonment, and service-level indicators |
| Auditable scenario management | Validated local scenario documents, cryptographic fingerprints, explicit SLA assessments, and repeatable seeds |
| Market Intelligence | Taylor-style macro regime, CAPM/factor regression, GARCH(1,1), Altman Z, Beneish M, Black-Litterman, contagion, behavioral/fuzzy/TOPSIS and stress scenarios |
| Scenario Intelligence 2.0 | Market-to-operations scenario graph, counterfactual stress transformation, governance manifest, and integrated evidence fingerprint |
| Commercial workspace and reporting | Browse, run, delete, and export fingerprint-verified saved scenarios as portable audit-ready JSON reports |
| Localization foundation | English and Persian interface vocabulary with persistent language selection and RTL support |
| Offline-ready desktop bundle | Locally bundled chart/CSS assets, PyInstaller runtime collection, Inno Setup installer definition, and release workflow |

## Quick Start for Developers

```bash
# Clone and enter the project
git clone https://github.com/Ali-Marandi/queuecraft-sim.git
cd queuecraft-sim

# Python runtime dependencies
python -m pip install -r requirements.txt

# Run the desktop app
python app.py
```

### Run the Verification Suite

```bash
npm test
python -m unittest -v test_ai_monte_carlo.py test_priority_queue.py test_scenario_manager.py
python -m unittest -v test_market_intelligence.py test_scenario_intelligence.py
python stress_test_scenarios.py
```

### Run Scenario Intelligence 2.0

```bash
python scenario_intelligence_cli.py examples/integrated_scenario_intelligence.json \
  --output artifacts/integrated-scenario.json
```

The integrated console produces market analysis, operational decision output, scenario-graph propagation, counterfactual stress paths, governance controls, and a SHA-256 scenario fingerprint. It does not place trades or apply infrastructure changes.

## Research Boundary

Research-only families such as DSGE, causal ML, topological data analysis, diffusion finance, quantum finance, federated learning, and ANFIS are explicitly separated from the executable analytics layer until they have dedicated calibration, validation, and governance.

## Windows Distribution

For a signed Windows installer containing application dependencies, local UI assets, and runtime libraries, follow [`WINDOWS_PACKAGING_GUIDE.md`](WINDOWS_PACKAGING_GUIDE.md). On a Windows x64 build agent with Python, Node.js, and Inno Setup installed, execute:

```powershell
.\build_windows.ps1 -Version "3.4.0"
```

The installer is created under `release\\`.

## Commercial Development Roadmap

The next commercial increments should focus on signed scenario packages, role-aware project workspaces, baseline/counterfactual comparison dashboards, PDF/XLSX decision reports, read-only connectors, encrypted local stores, SSO/RBAC, and policy-driven approval workflows.

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE).
