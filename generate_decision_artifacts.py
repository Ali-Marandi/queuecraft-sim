"""Create illustrative decision-analysis visuals from the included sample scenario."""

from pathlib import Path

from decision_analytics import (
    capacity_pareto_analysis,
    render_pareto_chart,
    render_sensitivity_chart,
    sensitivity_analysis,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "assets" / "analytics"
HISTORY = [8, 11, 13, 19, 22, 24, 20, 18, 21, 27, 31, 34]
TIERS = [
    {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
    {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
]

pareto = capacity_pareto_analysis(HISTORY, TIERS, server_range=(1, 6), replications=100, seed=42, sla_mean_wait=5.0)
sensitivity = sensitivity_analysis(HISTORY, TIERS, replications=100, seed=42)

pareto_path = render_pareto_chart(pareto, OUTPUT / "pareto_tradeoff_illustrative.png")
sensitivity_path = render_sensitivity_chart(sensitivity, OUTPUT / "sensitivity_heatmap_illustrative.png")
print(pareto_path)
print(sensitivity_path)
