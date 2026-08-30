import unittest

from data_plane import SchemaVersion, ValidationProfile, build_cache_key, build_dataset_manifest, build_run_bundle, fingerprint, validate_records


class DataPlaneTests(unittest.TestCase):
    def test_validation_profile(self):
        profile = ValidationProfile("arrivals-v1", ("count",), ("count",), 2)
        self.assertTrue(validate_records([{"count": 1}, {"count": 3}], profile)["valid"])
        self.assertFalse(validate_records([{"count": -1}, {"count": 3}], profile)["valid"])

    def test_manifest_is_stable(self):
        schema = SchemaVersion("arrivals", "1.0")
        records = [{"count": 1}, {"count": 2}]
        a = build_dataset_manifest(dataset_id="d1", records=records, schema=schema, quality_score=1.0)
        b = build_dataset_manifest(dataset_id="d1", records=records, schema=schema, quality_score=1.0)
        self.assertEqual(a["content_fingerprint"], b["content_fingerprint"])
        self.assertEqual(len(a["content_fingerprint"]), 64)

    def test_cache_key_changes_with_inputs(self):
        a = build_cache_key(dataset_fingerprint="a", scenario_fingerprint="b", model_versions=["m1"], runtime_version="3.17")
        b = build_cache_key(dataset_fingerprint="a", scenario_fingerprint="c", model_versions=["m1"], runtime_version="3.17")
        self.assertNotEqual(a, b)

    def test_run_bundle_has_fingerprint(self):
        bundle = build_run_bundle(
            run_id="r1",
            dataset_manifest={"content_fingerprint": fingerprint({"x": 1})},
            scenario={"id": "s1"},
            model_versions=[{"id": "m1", "version": "1"}],
            seed=42,
            outputs={"sla": "pass"},
        )
        self.assertEqual(len(bundle["bundle_fingerprint"]), 64)
        self.assertEqual(bundle["run_id"], "r1")


if __name__ == "__main__":
    unittest.main()
