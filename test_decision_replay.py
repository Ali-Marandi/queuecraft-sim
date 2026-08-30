import unittest

from decision_replay import compare_records, fingerprint, replay_decision, replay_snapshot


class DecisionReplayTests(unittest.TestCase):
    def test_fingerprint_is_order_invariant_for_dicts(self):
        self.assertEqual(fingerprint({"b": 2, "a": 1}), fingerprint({"a": 1, "b": 2}))

    def test_replay_identical(self):
        evidence = {"decision": {"capacity": 11, "sla": 0.96}, "seed": 42}
        result = replay_decision(evidence, lambda _: {"capacity": 11, "sla": 0.96})
        self.assertTrue(result.identical)
        self.assertEqual(result.status, "identical")
        self.assertEqual(result.changed_fields, ())

    def test_replay_detects_divergence(self):
        evidence = {"decision": {"capacity": 11, "sla": 0.96}, "seed": 42}
        result = replay_decision(evidence, lambda _: {"capacity": 12, "sla": 0.97})
        self.assertFalse(result.identical)
        self.assertEqual(result.status, "diverged")
        self.assertIn("capacity", result.changed_fields)

    def test_compare_records_handles_nested_values(self):
        same, changed = compare_records({"a": {"b": 1}}, {"a": {"b": 1}})
        self.assertTrue(same)
        self.assertEqual(changed, ())

    def test_snapshot_exposes_replay_metadata(self):
        snapshot = replay_snapshot({"scenario_id": "QC-1", "seed": 7, "decision": {"x": 1}, "assumptions": {"cv": 0.8}})
        self.assertTrue(snapshot["replay_supported"])
        self.assertEqual(snapshot["scenario_id"], "QC-1")
        self.assertEqual(snapshot["seed"], 7)


if __name__ == "__main__":
    unittest.main()
