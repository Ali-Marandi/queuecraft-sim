import unittest

from model_governance import evaluate_model_governance, governance_snapshot
from model_lifecycle import ModelCandidate
from model_registry import RegistryRecord


def baseline_model(values):
    return values[-1]


def mean_model(values):
    return sum(values) / len(values)


class ModelGovernanceTests(unittest.TestCase):
    def test_integrated_governance_is_fail_closed(self):
        result = evaluate_model_governance(
            observations=[10, 11, 12, 11, 13, 14, 15, 14, 16, 17],
            models={"last_value": baseline_model, "mean": mean_model},
            candidates=[
                ModelCandidate("champion", "forecast", "1.0", {"rmse": 1.2}),
                ModelCandidate("challenger", "forecast", "2.0", {"rmse": 1.0}),
            ],
            champion_metric=1.2,
            challenger_metric=1.0,
            data_quality_score=0.9,
            drift_status="drift",
            evidence_fingerprint="f" * 64,
            validation_status="validated",
        )
        self.assertFalse(result["promotion_gate"]["eligible"])
        self.assertTrue(result["continuous_evaluation"]["promotion_blocked"])
        self.assertFalse(result["governance"]["automatic_promotion"])
        self.assertFalse(result["governance"]["deployment_performed"])

    def test_governance_snapshot_exposes_registry_posture(self):
        records = [
            RegistryRecord("m1", "forecast", "1.0", stage="champion", validation_status="validated"),
            RegistryRecord("m2", "forecast", "2.0", stage="candidate", validation_status="validated"),
        ]
        result = governance_snapshot(records)
        self.assertEqual(result["posture"]["champion_count"], 1)
        self.assertFalse(result["posture"]["external_deployment"])


if __name__ == "__main__":
    unittest.main()
