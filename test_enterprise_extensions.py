import unittest

from decision_audit_bundle import build_audit_bundle, verify_audit_bundle
from experiment_registry import ExperimentSpec, build_experiment_run, compare_metrics, register_experiment


class EnterpriseExtensionsTests(unittest.TestCase):
    def test_experiment_identity_is_stable(self):
        spec = ExperimentSpec("exp-1", "baseline", "1.0", ("model-a:1",), 42, {"replications": 100}, "mean_wait")
        self.assertEqual(spec.identity(), spec.identity())
        self.assertEqual(register_experiment(spec)["model_versions"], ["model-a:1"])

    def test_metric_comparison(self):
        result = compare_metrics({"wait": 4.0, "sla": 0.9}, {"wait": 3.0, "sla": 0.95}, higher_is_better=("sla",))
        self.assertEqual(result["improved_metrics"], 2)

    def test_run_has_dataset_and_fingerprint(self):
        spec = ExperimentSpec("exp-2", "run", "1", ("m1",), 7, {}, "wait")
        run = build_experiment_run(spec, dataset_fingerprint="a" * 64, outputs={"x": 1}, metrics={"wait": 2.0})
        self.assertEqual(len(run["run_fingerprint"]), 64)
        self.assertEqual(run["dataset_fingerprint"], "a" * 64)

    def test_audit_bundle_detects_tampering(self):
        bundle = build_audit_bundle(
            envelope={"decision_fingerprint": "a" * 64},
            decision={"action": "review"},
            evidence={"token": "hidden", "score": 0.8},
            policy_result={"action": "review"},
            approval={"state": "pending"},
        )
        self.assertTrue(verify_audit_bundle(bundle)["valid"])
        bundle["decision"]["action"] = "allow"
        self.assertFalse(verify_audit_bundle(bundle)["valid"])
        self.assertEqual(bundle["evidence"]["token"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
