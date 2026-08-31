import unittest

from decision_audit_bundle import build_audit_bundle, verify_audit_bundle
from enterprise_security import Principal, authorize, validate_operation_request
from experiment_registry import ExperimentSpec, build_experiment_run, compare_metrics
from governance_hardening import build_decision_envelope, canonical_json, fingerprint, redact_sensitive


class GovernanceContractsTests(unittest.TestCase):
    def test_canonical_json_rejects_nan_and_is_stable(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), '{"a":1,"b":2}')
        with self.assertRaises(ValueError):
            canonical_json(float("nan"))

    def test_redaction_is_recursive_and_non_mutating(self):
        source = {"token": "secret", "nested": {"password": "pw"}}
        safe = redact_sensitive(source)
        self.assertEqual(safe["nested"]["password"], "[REDACTED]")
        self.assertEqual(source["token"], "secret")

    def test_decision_envelope_binds_decision_and_evidence(self):
        envelope = build_decision_envelope(
            decision_id="d1",
            created_at="2026-09-01T00:00:00Z",
            decision={"action": "review"},
            policy_id="p1",
            policy_version="1",
            evidence={"run_id": "r1"},
        )
        self.assertEqual(envelope["decision_fingerprint"], fingerprint({"action": "review"}))
        self.assertEqual(len(envelope["evidence_fingerprint"]), 64)

    def test_security_is_deny_by_default(self):
        principal = Principal("u1", frozenset({"reviewer"}), frozenset({"decision.approve"}))
        self.assertTrue(authorize(principal, "decision.approve", required_role="reviewer")["allowed"])
        self.assertFalse(authorize(principal, "decision.execute", required_role="reviewer")["allowed"])
        self.assertFalse(validate_operation_request({"operation": "deploy", "external_side_effect": True, "automatic_execution": True})["valid"])

    def test_experiment_run_is_fingerprinted(self):
        spec = ExperimentSpec("e1", "baseline", "1", ("model:1",), 42, {"replications": 100}, "mean_wait")
        run = build_experiment_run(spec, dataset_fingerprint="a" * 64, outputs={"sla": 0.99}, metrics={"wait": 2.0})
        self.assertEqual(len(run["run_fingerprint"]), 64)

    def test_metric_comparison_handles_direction(self):
        result = compare_metrics({"wait": 4.0, "sla": 0.90}, {"wait": 3.0, "sla": 0.95}, higher_is_better=("sla",))
        self.assertEqual(result["improved_metrics"], 2)

    def test_audit_bundle_detects_tampering(self):
        bundle = build_audit_bundle(
            envelope={"decision_fingerprint": "a" * 64},
            decision={"action": "review"},
            evidence={"api_key": "secret", "run": 1},
            policy_result={"action": "review"},
            approval={"state": "pending"},
        )
        self.assertTrue(verify_audit_bundle(bundle)["valid"])
        self.assertEqual(bundle["evidence"]["api_key"], "[REDACTED]")
        bundle["decision"]["action"] = "allow"
        self.assertFalse(verify_audit_bundle(bundle)["valid"])


if __name__ == "__main__":
    unittest.main()
