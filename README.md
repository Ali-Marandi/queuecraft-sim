# QueueCraft Enterprise AI

<div align="center">

![QueueCraft](https://img.shields.io/badge/QueueCraft-Enterprise%20AI%20v3.0-4f46e5?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-16a34a?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20x64-2563eb?style=for-the-badge)

**Enterprise queue simulation, AI-informed risk analysis, and capacity optimization.**

</div>

## Overview

QueueCraft Enterprise AI is a desktop simulation and capacity-planning suite for operations teams. It models deterministic, stochastic, and serial multi-tier workflows; forecasts short-horizon arrival demand; and evaluates operational risk through repeatable Monte Carlo analysis. The product is designed for service operations, healthcare, contact centers, retail, logistics, and other environments where service-level commitments, capacity cost, and waiting-time risk must be balanced transparently.

## Current Enterprise Capabilities

| Capability | What it delivers |
|---|---|
| Deterministic and stochastic modeling | Reproducible baselines alongside sampled arrivals and service-time variation |
| Multi-tier queue pipelines | Serial stage modeling in which departures from one tier become arrivals for the next tier |
| AI-informed Monte Carlo risk analysis | Demand forecasting plus repeated stochastic simulation with expected and P95 wait metrics |
| Cost-aware Auto-Scaling | Capacity recommendation under configurable wait-time SLA and per-server cost assumptions |
| Advanced queue policy model | Non-preemptive priority classes, finite waiting capacity, rejection, abandonment, and service-level indicators |
| Auditable scenario management | Validated local scenario documents, cryptographic fingerprints, explicit SLA assessments, and repeatable seeds |
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
python stress_test_scenarios.py
```

### Run an AI–Monte Carlo Scenario

```bash
python ai_monte_carlo.py --input examples/hospital_ai_monte_carlo.json
```

### Run Capacity Optimization

```bash
python ai_monte_carlo.py --input examples/hospital_staffing_optimization.json
```

## Windows Distribution

For a signed Windows installer containing application dependencies, local UI assets, and runtime libraries, follow [`WINDOWS_PACKAGING_GUIDE.md`](WINDOWS_PACKAGING_GUIDE.md). On a Windows x64 build agent with Python, Node.js, and Inno Setup installed, execute:

```powershell
.\build_windows.ps1 -Version "3.0.0"
```

The installer is created under `release\`.

## Commercial Development Roadmap

The immediate release candidate focus is data import and validation, real-world queue policies, audit trails, and forecast drift monitoring. The medium-term roadmap covers network routing, Pareto analysis, role-based collaboration, natural-language analysis with explicit access controls, and integrations with operational systems. Full prioritization appears in [`COMMERCIAL_ROADMAP_V3.md`](COMMERCIAL_ROADMAP_V3.md). The current commercial product specification and enterprise acceptance criteria are documented in [`COMMERCIAL_PRODUCT_SPEC_V4.md`](COMMERCIAL_PRODUCT_SPEC_V4.md).

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE).
