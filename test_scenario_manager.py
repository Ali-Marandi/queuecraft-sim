"""Tests for QueueCraft's reproducible enterprise scenario repository."""

import tempfile
import unittest
from pathlib import Path

from ai_monte_carlo import run_ai_monte_carlo
from scenario_manager import ScenarioRepository, ScenarioValidationError, evaluate_sla


SCENARIO = {
    "name": "Hospital morning capacity",
    "description": "Auditable baseline for weekday morning operations.",
    "historical_counts": [8, 11, 13, 19, 22, 24, 20],
    "tiers": [
        {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
        {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
    ],
    "simulation": {"horizon": 3, "replications": 30, "seed": 42},
    "sla": {"max_end_to_end_mean_wait": 5.0},
}


class ScenarioRepositoryTests(unittest.TestCase):
    def test_save_load_and_list_verify_fingerprint(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = ScenarioRepository(Path(temporary_directory))
            saved = repository.save(SCENARIO, scenario_id="hospital-morning")
            loaded = repository.load("hospital-morning")
            summaries = repository.list()
            self.assertEqual(saved["fingerprint"], loaded["fingerprint"])
            self.assertEqual(loaded["scenario"]["name"], SCENARIO["name"])
            self.assertEqual(summaries[0]["id"], "hospital-morning")

    def test_invalid_scenario_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repository = ScenarioRepository(Path(temporary_directory))
            invalid = dict(SCENARIO)
            invalid["tiers"] = []
            with self.assertRaises(ScenarioValidationError):
                repository.save(invalid)

    def test_sla_assessment_is_explicit(self):
        result = run_ai_monte_carlo(
            SCENARIO["historical_counts"], SCENARIO["tiers"], horizon=3, replications=30, seed=42
        )
        assessment = evaluate_sla(result, max_mean_wait=5.0)
        self.assertIn(assessment["status"], {"pass", "fail"})
        self.assertTrue(assessment["configured"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
