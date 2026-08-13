"""Regression tests for QueueCraft sensitivity and Pareto decision analytics."""

import tempfile
import unittest
from pathlib import Path

from decision_analytics import (
    capacity_pareto_analysis,
    is_dominated,
    render_pareto_chart,
    render_sensitivity_chart,
    sensitivity_analysis,
)


HISTORY = [8, 11, 13, 19, 22, 24, 20]
TIERS = [
    {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
    {"name": "Consultation", "servers": 2, "mean_service_time": 0.9, "service_cv": 1.0},
]


class DecisionAnalyticsTests(unittest.TestCase):
    def test_dominance_definition(self):
        self.assertTrue(is_dominated({"server_cost": 5, "mean_wait": 4}, {"server_cost": 4, "mean_wait": 3}))
        self.assertFalse(is_dominated({"server_cost": 5, "mean_wait": 3}, {"server_cost": 4, "mean_wait": 4}))

    def test_pareto_frontier_contains_only_non_dominated_plans(self):
        analysis = capacity_pareto_analysis(
            HISTORY, TIERS, server_range=(1, 2), replications=30, seed=42, sla_mean_wait=5.0
        )
        self.assertEqual(analysis["candidates_evaluated"], 4)
        self.assertGreaterEqual(len(analysis["pareto_frontier"]), 1)
        frontier = analysis["pareto_frontier"]
        for candidate in frontier:
            self.assertFalse(any(is_dominated(candidate, comparator) for comparator in frontier if comparator is not candidate))
        self.assertIn(analysis["recommendation"], frontier)

    def test_sensitivity_matrix_and_chart_exports(self):
        sensitivity = sensitivity_analysis(
            HISTORY, TIERS, arrival_multipliers=(0.8, 1.0), service_time_multipliers=(1.0, 1.2), replications=30, seed=42
        )
        self.assertEqual(len(sensitivity["results"]), 4)
        self.assertIsNotNone(sensitivity["baseline"])
        pareto = capacity_pareto_analysis(HISTORY, TIERS, server_range=(1, 2), replications=30, seed=42)
        with tempfile.TemporaryDirectory() as temporary_directory:
            pareto_path = Path(temporary_directory) / "pareto.png"
            sensitivity_path = Path(temporary_directory) / "sensitivity.png"
            render_pareto_chart(pareto, pareto_path)
            render_sensitivity_chart(sensitivity, sensitivity_path)
            self.assertGreater(pareto_path.stat().st_size, 1000)
            self.assertGreater(sensitivity_path.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
