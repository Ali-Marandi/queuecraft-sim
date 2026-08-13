"""Regression tests for QueueCraft local live SLO monitoring."""

import unittest

from live_slo_monitoring import LiveSLOMonitor
from multi_region_failover import SLODefinition


class LiveSLOMonitoringTests(unittest.TestCase):
    def test_ingest_uses_success_and_latency_as_composite_good_signal(self):
        monitor = LiveSLOMonitor(SLODefinition(availability_target=0.90, rolling_window_buckets=3))
        dashboard = monitor.ingest(
            {
                "bucket": 0,
                "region": "europe-region",
                "source": "approved-adapter",
                "total_requests": 100,
                "successful_requests": 98,
                "latency_compliant_requests": 95,
            }
        )
        self.assertEqual(dashboard["slo"]["good_requests"], 95)
        self.assertEqual(dashboard["slo"]["bad_requests"], 5)
        self.assertEqual(dashboard["region_totals"]["europe-region"]["good_requests"], 95)

    def test_history_is_bounded_and_bucket_must_be_monotonic(self):
        monitor = LiveSLOMonitor(max_history_points=2)
        for bucket in range(3):
            monitor.ingest(
                {
                    "bucket": bucket,
                    "region": "region-a",
                    "total_requests": 10,
                    "successful_requests": 10,
                    "latency_compliant_requests": 10,
                }
            )
        dashboard = monitor.dashboard_snapshot()
        self.assertEqual(len(dashboard["history"]), 2)
        self.assertEqual(dashboard["history"][0]["bucket"], 1)
        with self.assertRaises(ValueError):
            monitor.ingest(
                {
                    "bucket": 1,
                    "region": "region-a",
                    "total_requests": 1,
                    "successful_requests": 1,
                    "latency_compliant_requests": 1,
                }
            )

    def test_demo_and_metrics_preview_are_local_and_non_empty(self):
        monitor = LiveSLOMonitor()
        dashboard = monitor.advance_demo()
        self.assertEqual(dashboard["mode"], "local-in-memory")
        self.assertFalse(dashboard["outbound_telemetry_enabled"])
        self.assertEqual(dashboard["history"][0]["source"], "local-demo")
        self.assertIn("queuecraft_slo_error_budget_remaining_requests", dashboard["prometheus_text_preview"])

    def test_reset_removes_session_history(self):
        monitor = LiveSLOMonitor()
        monitor.advance_demo()
        dashboard = monitor.reset()
        self.assertEqual(dashboard["history"], [])
        self.assertEqual(dashboard["slo"]["window_observations"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
