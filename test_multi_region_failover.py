"""Regression tests for QueueCraft multi-region failover and SLO monitoring."""

import unittest

from multi_region_failover import (
    FailoverPolicy,
    RegionConfig,
    SLODefinition,
    SLOMonitor,
    simulate_multi_region_failover,
)


REGIONS = [
    RegionConfig("region-a", capacity_per_bucket=10, routing_weight=2, base_latency_ms=40),
    RegionConfig("region-b", capacity_per_bucket=10, routing_weight=1, base_latency_ms=70),
]
SLO = SLODefinition(availability_target=0.99, latency_threshold_ms=120, rolling_window_buckets=3)


class MultiRegionFailoverTests(unittest.TestCase):
    def test_active_active_routes_within_combined_capacity(self):
        result = simulate_multi_region_failover(
            [9], REGIONS, FailoverPolicy(mode="active_active"), SLO
        )
        bucket = result["timeline"][0]
        self.assertEqual(bucket["served_requests"], 9)
        self.assertEqual(bucket["unserved_requests"], 0)
        self.assertEqual(sum(bucket["region_assignments"].values()), 9)
        self.assertEqual(result["summary"]["final_slo"]["alert_level"], "healthy")

    def test_active_passive_routes_to_secondary_during_primary_outage(self):
        result = simulate_multi_region_failover(
            [8],
            REGIONS,
            FailoverPolicy(mode="active_passive", primary_region="region-a", failover_latency_penalty_ms=25),
            SLO,
            outages_by_bucket={0: {"region-a"}},
        )
        bucket = result["timeline"][0]
        self.assertEqual(bucket["event"], "failover_routed")
        self.assertEqual(bucket["region_assignments"]["region-b"], 8)
        self.assertEqual(bucket["failover_jobs"], 8)
        self.assertEqual(bucket["estimated_weighted_latency_ms"], 95.0)

    def test_outage_with_insufficient_capacity_consumes_error_budget(self):
        result = simulate_multi_region_failover(
            [18],
            REGIONS,
            FailoverPolicy(mode="active_passive", primary_region="region-a"),
            SLO,
            outages_by_bucket={0: {"region-a"}},
        )
        final_slo = result["summary"]["final_slo"]
        self.assertEqual(result["timeline"][0]["unserved_requests"], 8)
        self.assertEqual(final_slo["bad_requests"], 8)
        self.assertEqual(final_slo["alert_level"], "critical")

    def test_monitor_uses_rolling_window_and_exposes_burn_rate(self):
        monitor = SLOMonitor(SLODefinition(availability_target=0.90, rolling_window_buckets=2))
        monitor.record(bucket=0, total_requests=10, good_requests=10)
        monitor.record(bucket=1, total_requests=10, good_requests=8)
        snapshot = monitor.record(bucket=2, total_requests=10, good_requests=10)
        self.assertEqual(snapshot["window_observations"], 2)
        self.assertEqual(snapshot["total_requests"], 20)
        self.assertEqual(snapshot["bad_requests"], 2)
        self.assertGreater(snapshot["error_budget_burn_rate"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
