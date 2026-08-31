import unittest

from governance_hardening import build_decision_envelope, canonical_json, fingerprint, redact_sensitive


class GovernanceHardeningTests(unittest.TestCase):
    def test_canonical_fingerprint_is_order_independent(self):
        self.assertEqual(fingerprint({"b": 2, "a": 1}), fingerprint({"a": 1, "b": 2}))
        self.assertEqual(canonical_json({"b": 2, "a": 1}), '{"a":1,"b":2}')

    def test_nan_is_rejected(self):
        with self.assertRaises(ValueError):
            canonical_json(float("nan"))

    def test_redaction_does_not_mutate_input(self):
        payload = {"token": "secret", "nested": {"password": "pw", "value": 3}}
        result = redact_sensitive(payload)
        self.assertEqual(result["token"], "[REDACTED]")
        self.assertEqual(result["nested"]["password"], "[REDACTED]")
        self.assertEqual(payload["token"], "secret")
        self.assertEqual(payload["nested"]["password"], "pw")

    def test_envelope_contains_reproducible_artifact_identity(self):
        envelope = build_decision_envelope(
            decision_id="d-1",
            created_at="2026-09-01T00:00:00+00:00",
            decision={"action": "review", "score": 0.7},
            policy_id="ops-policy",
            policy_version="1.2.0",
            evidence={"run": 42, "model": "m1"},
        )
        self.assertEqual(envelope["schema_version"], 1)
        self.assertEqual(len(envelope["decision_fingerprint"]), 64)
        self.assertEqual(len(envelope["evidence_fingerprint"]), 64)
        self.assertTrue(envelope["approval_required"])

    def test_envelope_rejects_non_mapping_artifacts(self):
        with self.assertRaises(ValueError):
            build_decision_envelope(
                decision_id="d-1",
                created_at="now",
                decision=[],
                policy_id="p",
                policy_version="1",
                evidence={},
            )


if __name__ == "__main__":
    unittest.main()
