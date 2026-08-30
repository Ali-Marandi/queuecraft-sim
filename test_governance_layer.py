import unittest

from governance_layer import DataAsset, GovernanceRegistry, ModelRecord, build_evidence_pack, data_quality_score, fingerprint


class GovernanceLayerTests(unittest.TestCase):
    def test_quality_scoring(self):
        self.assertEqual(data_quality_score([1, 2, 3])["score"], 1.0)
        self.assertEqual(data_quality_score([1, None, 3])["status"], "watch")
        self.assertEqual(data_quality_score([])["status"], "insufficient")

    def test_registry_snapshot(self):
        registry = GovernanceRegistry()
        registry.register_data(DataAsset("arrivals", "local_csv", "arrival buckets", quality_score=0.98))
        registry.register_model(ModelRecord("garch11", "volatility", "1.0.0", "volatility screening"))
        snapshot = registry.snapshot()
        self.assertEqual(len(snapshot["data_assets"]), 1)
        self.assertEqual(snapshot["models"][0]["model_id"], "garch11")

    def test_evidence_pack_is_deterministic_and_contains_lineage(self):
        data = [DataAsset("arrivals", "local_csv", "arrival buckets", quality_score=0.98)]
        models = [ModelRecord("decision-engine", "optimization", "4.0.0", "capacity recommendation")]
        kwargs = dict(decision={"candidate": "plan-2"}, source_data=data, models=models, assumptions={"sla": 5.0})
        a = build_evidence_pack(**kwargs)
        b = build_evidence_pack(**kwargs)
        self.assertEqual(a["evidence_fingerprint"], b["evidence_fingerprint"])
        self.assertEqual(len(a["evidence_fingerprint"]), 64)
        self.assertIn("lineage", a)
        self.assertGreaterEqual(a["lineage"]["node_count"], 3)

    def test_fingerprint_changes_with_content(self):
        self.assertNotEqual(fingerprint({"x": 1}), fingerprint({"x": 2}))


if __name__ == "__main__":
    unittest.main()
