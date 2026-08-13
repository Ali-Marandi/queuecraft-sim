"""Unit tests for the QueueCraft AI-informed Monte Carlo engine."""

import unittest

from ai_monte_carlo import forecast_arrival_rates, optimize_staffing, run_ai_monte_carlo


HISTORY = [8, 11, 13, 19, 22, 24, 20, 18, 21, 27, 31, 34]
TIERS = [
    {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
    {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
]


class AiMonteCarloTests(unittest.TestCase):
    def test_forecast_returns_requested_horizon(self):
        forecast = forecast_arrival_rates(HISTORY, horizon=4)
        self.assertEqual(forecast["historical_bucket_count"], len(HISTORY))
        self.assertEqual(len(forecast["forecast_arrivals_per_bucket"]), 4)
        self.assertTrue(all(value >= 0 for value in forecast["forecast_arrivals_per_bucket"]))

    def test_multi_tier_simulation_is_reproducible_with_seed(self):
        first = run_ai_monte_carlo(HISTORY, TIERS, horizon=4, replications=40, seed=2026)
        second = run_ai_monte_carlo(HISTORY, TIERS, horizon=4, replications=40, seed=2026)
        self.assertEqual(first, second)
        self.assertEqual(first["simulation"]["replications"], 40)
        self.assertIn("Triage", first["simulation"]["tiers"])
        self.assertIn("Consultation", first["simulation"]["tiers"])
        self.assertGreaterEqual(first["simulation"]["mean_jobs"], 0)

    def test_optimizer_returns_one_recommendation_per_tier(self):
        result = optimize_staffing(
            HISTORY,
            TIERS,
            server_range=(1, 2),
            max_end_to_end_mean_wait=3.0,
            cost_per_server=1.0,
            replications=30,
            seed=2026,
        )
        self.assertEqual(len(result["recommended_tiers"]), len(TIERS))
        self.assertEqual(result["candidates_evaluated"], 4)
        self.assertGreater(result["objective"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
