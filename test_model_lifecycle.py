import unittest

from model_lifecycle import (
    ModelCandidate,
    calibration_by_bins,
    compare_challengers,
    distribution_drift,
    forecast_metrics,
    model_lifecycle_snapshot,
)


class ModelLifecycleTests(unittest.TestCase):
    def test_forecast_metrics(self):
        out = forecast_metrics([10, 20, 30], [11, 18, 33])
        self.assertEqual(out["observations"], 3)
        self.assertGreater(out["rmse"], 0)
        self.assertAlmostEqual(out["bias"], (-1 + 2 - 3) / 3)

    def test_distribution_drift(self):
        stable = distribution_drift([10, 11, 12], [10.2, 10.8, 11.9], relative_threshold=0.2)
        shifted = distribution_drift([10, 11, 12], [15, 16, 17], relative_threshold=0.2)
        self.assertEqual(stable["status"], "stable")
        self.assertEqual(shifted["status"], "drift")

    def test_calibration(self):
        out = calibration_by_bins([10, 20, 30, 40, 50], [11, 19, 31, 39, 48], bins=5)
        self.assertEqual(len(out["bins"]), 5)
        self.assertIsNotNone(out["mean_absolute_calibration_gap"])

    def test_challenger_does_not_auto_promote(self):
        out = compare_challengers(
            [
                ModelCandidate("champion", "forecast", "1.0", {"rmse": 2.0}),
                ModelCandidate("challenger", "forecast", "2.0", {"rmse": 1.5}),
            ],
            primary_metric="rmse",
        )
        self.assertEqual(out["recommended_candidate"], "challenger")
        self.assertFalse(out["promotion"]["automatic"])
        self.assertTrue(out["promotion"]["requires_human_approval"])

    def test_snapshot(self):
        model = ModelCandidate("m1", "forecast", "1.0", {"rmse": 1.2}, ("small sample",))
        out = model_lifecycle_snapshot(
            model=model,
            actual=[10, 20, 30, 40, 50],
            predicted=[11, 19, 31, 39, 48],
            reference_load=[100, 100, 110],
            current_load=[100, 140, 150],
        )
        self.assertEqual(out["model"]["model_id"], "m1")
        self.assertIn("performance", out)
        self.assertEqual(out["governance"]["promotion_allowed"], False)


if __name__ == "__main__":
    unittest.main()
