"""Regression tests for QueueCraft cloud cluster scaling simulation."""

import unittest

from cloud_cluster_scaling import (
    ClusterPolicy,
    distribute_load,
    forecast_cluster_scaling,
    simulate_cluster_scaling,
)


class CloudClusterScalingTests(unittest.TestCase):
    def test_load_distribution_is_balanced(self):
        self.assertEqual(distribute_load(10, 3, "least_loaded"), [4, 3, 3])
        self.assertEqual(distribute_load(5, 3, "round_robin", rotation=1), [1, 2, 2])

    def test_scale_up_respects_warmup_then_increases_capacity(self):
        policy = ClusterPolicy(
            min_nodes=1,
            max_nodes=4,
            node_capacity=10,
            target_utilization=0.70,
            scale_up_step=2,
            warmup_buckets=1,
            cooldown_buckets=0,
        )
        result = simulate_cluster_scaling([5, 40, 40, 20], policy)
        actions = result["summary"]["scaling_actions"]
        self.assertTrue(any(action.startswith("scale_up_requested") for action in actions))
        self.assertGreater(result["summary"]["peak_active_nodes"], 1)
        self.assertGreaterEqual(result["timeline"][2]["active_nodes"], 2)

    def test_scale_down_keeps_current_bucket_serving_capacity_auditable(self):
        policy = ClusterPolicy(
            min_nodes=1,
            max_nodes=4,
            node_capacity=10,
            target_utilization=0.75,
            scale_down_step=1,
            scale_down_threshold=0.35,
            cooldown_buckets=0,
        )
        result = simulate_cluster_scaling([30, 0, 0], policy, initial_nodes=4)
        second_bucket = result["timeline"][1]
        self.assertEqual(second_bucket["active_nodes"], 4)
        self.assertEqual(second_bucket["next_bucket_active_nodes"], 3)
        self.assertTrue(second_bucket["action"].startswith("scale_down_applied"))

    def test_forecast_produces_pre_scaling_plan(self):
        policy = ClusterPolicy(min_nodes=1, max_nodes=5, node_capacity=10, target_utilization=0.7)
        result = forecast_cluster_scaling([8, 11, 13, 19, 22, 24, 20], policy, horizon=3)
        self.assertEqual(len(result["pre_scaling_plan"]), 3)
        self.assertTrue(all(1 <= item["recommended_nodes"] <= 5 for item in result["pre_scaling_plan"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
