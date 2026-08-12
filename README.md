# QueueCraft Enterprise Simulation Studio

<div align="center">

![QueueCraft Logo](https://img.shields.io/badge/QueueCraft-Enterprise%20v2.1-indigo?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue?style=for-the-badge)

**Commercial-Grade Multi-Server Queue Simulation & Resource Optimization Suite**

</div>

---

## 🚀 Overview

**QueueCraft Enterprise** is a high-performance, enterprise-grade discrete-event queue simulation and capacity planning software designed to rival industry-standard simulation tools (such as Rockwell Arena, Simio, and AnyLogic). Built for operations research, industrial engineering, retail traffic management, call centers, and healthcare capacity planning, QueueCraft Enterprise bridges the gap between complex mathematical queueing theory and intuitive modern desktop software.

---

## ✨ Key Enterprise Features

- **Dual Simulation Modes**:
  - **Stochastic (Monte Carlo)**: Advanced probabilistic modeling using Poisson arrival processes (exponential inter-arrival times) and exponential service time distributions.
  - **Deterministic**: Exact custom arrival and service time array processing for precise baseline modeling.
- **Interactive Desktop GUI**:
  - Built with native desktop rendering (`pywebview` + Tailwind CSS + Chart.js).
  - Modern dark-mode enterprise UI with real-time KPI metrics (Average Wait Time, Maximum Wait Time, Total Makespan, Server Utilization).
- **Multi-Server Scenario Optimization**:
  - Side-by-side comparative analysis across varying server counts (1 to 20 servers) to identify optimal staffing levels and prevent bottlenecks.
- **Advanced Visualizations**:
  - Interactive bar charts for individual job wait times.
  - Dynamic doughnut charts for server workload distribution.
  - Sensitivity and utilization curves.
- **Automated CI/CD Release Pipeline**:
  - GitHub Actions workflow that automatically cross-compiles a standalone Windows executable (`QueueCraftEnterprise.exe`) and publishes releases.

---

## 📊 Quick Start & Installation

### Option 1: Download Pre-built Windows Executable (`.exe`)
1. Go to the [Releases](https://github.com/Ali-Marandi/queuecraft-sim/releases) page.
2. Download `QueueCraftEnterprise.exe`.
3. Run the application directly (no installation or Python runtime required on client machines).

### Option 2: Run from Source (Python + WebUI)
```bash
# Clone repository
git clone https://github.com/Ali-Marandi/queuecraft-sim.git
cd queuecraft-sim

# Install dependencies
pip install pyinstaller pywebview

# Run simulation studio GUI
python app.py
```

---

## 🧪 Running Tests
```bash
npm test
```

---

## 🏢 Commercial & Enterprise Roadmap
- **Phase 1**: Core discrete-event engine & basic metrics ✅
- **Phase 2**: Stochastic Monte Carlo distributions & GUI desktop app ✅
- **Phase 3**: Multi-server scenario optimization & automated Windows build pipeline ✅
- **Phase 4**: Real-time queue animation canvas & cloud database sync (Upcoming)

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.
