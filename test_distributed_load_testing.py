"""Regression tests for the safe local distributed-load simulator."""

import unittest

from distributed_load_testing import (
    DistributedLoadPolicy,
    LoadGenerator,
    TargetRegion,
    simulate_distributed_load,
)


GENERATORS = [
    LoadGenerator("us-client", max_requests_per_bucket=30, routing_weight=1),
    LoadGenerator("eu-client", max_requests_per_bucket=30, routing_weight=1),
]
TARGETS = [
    TargetRegion("us-region", capacity_per_bucket=12, service_latency_ms=20),
    TargetRegion("eu-region", capacity_per_bucket=12, service_latency_ms=20),
]
LATENCY = {
    "us-client": {"us-region": 15, "eu-region": 110},
    "eu-client": {"us-region": 105, "eu-region": 15},
}
POLICY = DistributedLoadPolicy(routing_mode="latency_aware", saturation_penalty_ms=0, latency_slo_ms=200)


class DistributedLoadTestingTests(unittest.TestCase):
    def test_latency_aware_routing_prefers_local_regions(self):
        result = simulate_distributed_load([20], GENERATORS, TARGETS, LATENCY, POLICY)
        bucket = result["timeline"][0]
        self.assertEqual(bucket["route_assignments"]["us-client"]["us-region"], 10)
        self.assertEqual(bucket["route_assignments"]["eu-client"]["eu-region"], 10)
        self.assertEqual(result["summary"]["total_unserved_requests"], 0)
        self.assertEqual(result["safe_mode"]["network_requests_sent"], 0)

    def test_generator_capacity_limit_is_reported_explicitly(self):
        generators = [LoadGenerator("limited-agent", max_requests_per_bucket=5)]
        targets = [TargetRegion("target", capacity_per_bucket=50)]
        result = simulate_distributed_load(
            [12], generators, targets, {"limited-agent": {"target": 10}}, POLICY
        )
        self.assertEqual(result["summary"]["generator_capacity_limited_requests"], 7)
        self.assertEqual(result["summary"]["total_generated_requests"], 5)
        self.assertEqual(result["summary"]["total_served_requests"], 5)

    def test_outage_reroutes_when_secondary_has_capacity(self):
        generators = [LoadGenerator("client", max_requests_per_bucket=20)]
        targets = [
            TargetRegion("primary", capacity_per_bucket=10, service_latency_ms=20),
            TargetRegion("secondary", capacity_per_bucket=10, service_latency_ms=70),
        ]
        result = simulate_distributed_load(
            [8],
            generators,
            targets,
            {"client": {"primary": 10, "secondary": 80}},
            POLICY,
            outages_by_bucket={0: {"primary"}},
        )
        bucket = result["timeline"][0]
        self.assertEqual(bucket["target_served_requests"]["secondary"], 8)
        self.assertEqual(bucket["unserved_requests"], 0)
        self.assertEqual(bucket["unhealthy_target_regions"], ["primary"])

    def test_capacity_shortfall_becomes_unserved_requests(self):
        generators = [LoadGenerator("client", max_requests_per_bucket=30)]
        targets = [TargetRegion("target", capacity_per_bucket=6)]
        result = simulate_distributed_load(
            [15], generators, targets, {"client": {"target": 10}}, POLICY
        )
        self.assertEqual(result["summary"]["total_unserved_requests"], 9)
        self.assertEqual(result["summary"]["peak_unserved_requests"], 9)


if __name__ == "__main__":
    unittest.main(verbosity=2)
