import unittest

from experiment_engine import bootstrap_mean_ci, paired_effect, scenario_experiment


class ExperimentEngineTests(unittest.TestCase):
    def test_bootstrap_is_deterministic(self):
        values = [1, 2, 3, 4, 5]
        a = bootstrap_mean_ci(values, resamples=300, seed=7)
        b = bootstrap_mean_ci(values, resamples=300, seed=7)
        self.assertEqual(a, b)
        self.assertLessEqual(a["lower"], a["mean"])
        self.assertGreaterEqual(a["upper"], a["mean"])

    def test_paired_effect_direction(self):
        base = [10, 11, 9, 10, 12]
        candidate = [8, 9, 8, 7, 10]
        result = paired_effect(base, candidate, resamples=300, seed=3)
        self.assertLess(result["mean_difference"], 0)
        self.assertEqual(result["direction_for_lower_is_better"], "improves")
        self.assertIn("standardized_effect", result)

    def test_scenario_experiment_contract(self):
        result = scenario_experiment([1, 2, 3], [2, 2, 2], resamples=300)
        self.assertEqual(result["metric"], "mean_wait")
        self.assertEqual(result["engine_version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
