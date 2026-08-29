import unittest

from decision_engine import build_decision_package


class DecisionEngineTests(unittest.TestCase):
    def setUp(self):
        self.history = [8, 11, 13, 19, 22, 24, 20, 18, 21, 27]
        self.tiers = [
            {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
            {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
        ]

    def test_package_has_benchmark_risk_and_governance(self):
        package = build_decision_package(
            self.history,
            self.tiers,
            sla_mean_wait=5.0,
            server_range=(1, 3),
            replications=30,
            seed=7,
        )
        self.assertEqual(package["version"], "4.0.0")
        self.assertIn("baseline", package["benchmark"])
        self.assertIn("proposed", package["benchmark"])
        self.assertIn("delta", package["benchmark"])
        self.assertIn("screening_sla_failure_risk", package["risk"])
        self.assertTrue(package["approval"]["required"])
        self.assertFalse(package["approval"]["applied"])
        self.assertFalse(package["approval"]["external_operations_performed"])
        self.assertEqual(len(package["package_fingerprint"]), 64)

    def test_deterministic_replay_is_stable(self):
        kwargs = dict(sla_mean_wait=5.0, server_range=(1, 3), replications=30, seed=11)
        first = build_decision_package(self.history, self.tiers, **kwargs)
        second = build_decision_package(self.history, self.tiers, **kwargs)
        self.assertEqual(first["package_fingerprint"], second["package_fingerprint"])
        self.assertEqual(first["benchmark"], second["benchmark"])
        self.assertEqual(first["recommendation"]["selected_candidate"], second["recommendation"]["selected_candidate"])

    def test_llm_is_off_by_default(self):
        package = build_decision_package(self.history, self.tiers, server_range=(1, 2), replications=30)
        self.assertEqual(package["recommendation"]["execution_mode"], "deterministic-offline")


if __name__ == "__main__":
    unittest.main()
