import unittest

from model_registry import (
    RegistryRecord,
    promote_to_champion,
    register_model,
    registry_snapshot,
    retire_model,
    review_candidate,
)


class ModelRegistryTests(unittest.TestCase):
    def test_registration_and_candidate_review(self):
        record = RegistryRecord("m1", "forecast", "1.0", metric_value=2.0)
        self.assertTrue(register_model(record)["registered"])
        reviewed = review_candidate(record, validation_status="validated", evidence_fingerprint="abc123", reviewer_note="ok")
        self.assertEqual(reviewed["stage"], "candidate")
        self.assertEqual(reviewed["evidence_fingerprint"], "abc123")

    def test_promotion_requires_approval(self):
        record = RegistryRecord("m2", "forecast", "2.0", metric_value=1.5)
        review_candidate(record, validation_status="validated_with_limits", evidence_fingerprint="fp")
        promoted = promote_to_champion(record, approval_id="APR-1")
        self.assertEqual(promoted["stage"], "champion")

    def test_retire_and_snapshot(self):
        record = RegistryRecord("m3", "forecast", "3.0", stage="candidate", validation_status="validated", metric_value=1.7)
        retire_model(record, approval_id="APR-2")
        snap = registry_snapshot([record])
        self.assertEqual(record.stage, "retired")
        self.assertEqual(snap["total_models"], 1)
        self.assertFalse(snap["governance"]["automatic_promotion"])

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            register_model(RegistryRecord("bad", "forecast", "1.0", stage="deploying"))


if __name__ == "__main__":
    unittest.main()
