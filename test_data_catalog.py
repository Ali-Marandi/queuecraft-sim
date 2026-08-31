import unittest

from data_catalog import DataCatalog, DatasetRecord, FeatureDefinition, cache_invalidation_reason


class DataCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = DataCatalog()
        self.catalog.register_dataset(DatasetRecord("arrivals", "2026.1", "fp-a", "arrivals", "1.0"))

    def test_feature_registration_requires_known_dataset(self):
        self.catalog.register_feature(FeatureDefinition("f1", "rolling_mean", "1", ("arrivals",)))
        with self.assertRaises(ValueError):
            self.catalog.register_feature(FeatureDefinition("f2", "bad", "1", ("missing",)))

    def test_run_registry_tracks_dataset_usage(self):
        run = self.catalog.record_run(run_id="run-1", dataset_fingerprints=("fp-a",), scenario_fingerprint="scn", model_versions=("m1@1",), runtime_version="3.18")
        self.assertTrue(run.cache_key)
        usage = self.catalog.usage("arrivals")
        self.assertEqual(usage["runs"], ["run-1"])

    def test_dataset_change_invalidates_cache(self):
        out = cache_invalidation_reason(
            old_dataset_fingerprint="old",
            new_dataset_fingerprint="new",
            scenario_fingerprint="scn",
            model_versions=("m1@1",),
            runtime_version="3.18",
        )
        self.assertTrue(out["invalidated"])

    def test_same_inputs_keep_cache(self):
        out = cache_invalidation_reason(
            old_dataset_fingerprint="same",
            new_dataset_fingerprint="same",
            scenario_fingerprint="scn",
            model_versions=("m1@1",),
            runtime_version="3.18",
        )
        self.assertFalse(out["invalidated"])


if __name__ == "__main__":
    unittest.main()
