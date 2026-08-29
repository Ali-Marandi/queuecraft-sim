import unittest

from streaming_drift import DriftThresholds, StreamingDriftMonitor, drift_report


class StreamingDriftTests(unittest.TestCase):
    def setUp(self):
        self.reference = [10, 11, 9, 10, 12, 8, 11, 10, 9, 11, 10, 12, 8, 10, 11, 9, 10, 12, 11, 10]

    def test_stable_series_does_not_trigger(self):
        report = drift_report(self.reference, self.reference[:10])
        self.assertEqual(report["status"], "stable")
        self.assertFalse(report["trigger"])

    def test_shift_triggers(self):
        current = [20, 21, 19, 22, 20, 21, 23, 18, 20, 22]
        report = drift_report(self.reference, current)
        self.assertTrue(report["trigger"])
        self.assertIn("mean_shift", report["reasons"])

    def test_insufficient_data(self):
        report = drift_report([1, 2, 3], [4, 5])
        self.assertEqual(report["status"], "insufficient_data")
        self.assertFalse(report["trigger"])

    def test_monitor_never_deploys(self):
        monitor = StreamingDriftMonitor(thresholds=DriftThresholds(mean_shift_ratio=0.1))
        monitor.seed_reference(self.reference)
        out = monitor.ingest([20, 21, 19, 22, 20, 21, 23, 18, 20, 22])
        self.assertTrue(out["challenger_trigger"]["evaluation_requested"])
        self.assertEqual(out["challenger_trigger"]["deployment"], "blocked")


if __name__ == "__main__":
    unittest.main()
