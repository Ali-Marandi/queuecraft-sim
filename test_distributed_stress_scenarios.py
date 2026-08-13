"""Tests for QueueCraft's safe local distributed stress scenario pack."""

import unittest

from distributed_stress_scenarios import _scenario_definitions, run_scenario


class DistributedStressScenarioTests(unittest.TestCase):
    def test_all_scenario_expectations_are_met_without_network_requests(self):
        for name in _scenario_definitions():
            report = run_scenario(name)
            self.assertTrue(report["safe_mode"]["network_requests_sent"] == 0)
            self.assertTrue(report["expectation_met"], msg=name)

    def test_sustained_saturation_is_explicitly_classified_as_expected_failure(self):
        report = run_scenario("sustained_saturation")
        self.assertEqual(report["expected_outcome"], "fail")
        self.assertFalse(report["acceptance"]["passed"])
        self.assertGreater(report["summary"]["total_unserved_requests"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
