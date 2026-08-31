import unittest
from datetime import datetime, timezone

from decision_readiness import evaluate_readiness
from governance_hardening import build_decision_envelope


class DecisionReadinessTests(unittest.TestCase):
    def _artifacts(self, approval_required=True):
        decision = {"decision": "scale", "risk": 0.2}
        evidence = {"dataset": "d1", "model": "m1", "expires_at": "2026-09-02T00:00:00+00:00"}
        envelope = build_decision_envelope(
            decision_id="D-1",
            created_at="2026-09-01T00:00:00+00:00",
            decision=decision,
            policy_id="ops",
            policy_version="1.0",
            evidence=evidence,
            approval_required=approval_required,
        )
        return envelope, decision, evidence

    def test_ready_requires_explicit_approval(self):
        envelope, decision, evidence = self._artifacts()
        result = evaluate_readiness(
            envelope=envelope,
            decision=decision,
            evidence=evidence,
            policy_result={"action": "allow"},
            approval={"state": "approved"},
            required_evidence_fields=("dataset", "model"),
            now=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(result["outcome"], "READY")
        self.assertTrue(result["ready"])

    def test_missing_approval_blocks(self):
        envelope, decision, evidence = self._artifacts()
        result = evaluate_readiness(
            envelope=envelope,
            decision=decision,
            evidence=evidence,
            policy_result={"action": "allow"},
            required_evidence_fields=("dataset", "model"),
            now=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(result["outcome"], "BLOCK")

    def test_policy_block_wins(self):
        envelope, decision, evidence = self._artifacts(approval_required=False)
        result = evaluate_readiness(
            envelope=envelope,
            decision=decision,
            evidence=evidence,
            policy_result={"action": "block"},
            required_evidence_fields=("dataset",),
            now=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(result["outcome"], "BLOCK")

    def test_fingerprint_mismatch_blocks(self):
        envelope, decision, evidence = self._artifacts(approval_required=False)
        altered = dict(decision, risk=0.9)
        result = evaluate_readiness(
            envelope=envelope,
            decision=altered,
            evidence=evidence,
            policy_result={"action": "allow"},
            now=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(result["outcome"], "BLOCK")

    def test_missing_expiry_is_review_not_ready(self):
        envelope, decision, evidence = self._artifacts(approval_required=False)
        evidence = dict(evidence)
        evidence.pop("expires_at")
        envelope = dict(envelope, evidence_fingerprint=envelope["evidence_fingerprint"])
        # The intentionally stale identity above is caught as BLOCK; exercise the
        # explicit freshness behavior separately with a fresh envelope.
        envelope = build_decision_envelope(
            decision_id="D-2",
            created_at="2026-09-01T00:00:00+00:00",
            decision=decision,
            policy_id="ops",
            policy_version="1.0",
            evidence=evidence,
            approval_required=False,
        )
        result = evaluate_readiness(
            envelope=envelope,
            decision=decision,
            evidence=evidence,
            policy_result={"action": "allow"},
            now=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(result["outcome"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
