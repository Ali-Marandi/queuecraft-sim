import unittest

from promotion_gate import evaluate_promotion_gate


class PromotionGateTests(unittest.TestCase):
    def test_eligible_gate(self):
        out = evaluate_promotion_gate(
            validation_status="validated",
            data_quality_score=0.95,
            drift_status="stable",
            champion_metric=5.0,
            challenger_metric=4.0,
            minimum_improvement=0.10,
            evidence_fingerprint="fp",
        )
        self.assertTrue(out["eligible"])
        self.assertFalse(out["governance"]["automatic_promotion"])

    def test_blocked_gate(self):
        out = evaluate_promotion_gate(
            validation_status="unvalidated",
            data_quality_score=0.70,
            drift_status="drift",
            champion_metric=5.0,
            challenger_metric=4.9,
            minimum_improvement=0.10,
            evidence_fingerprint=None,
        )
        self.assertFalse(out["eligible"])
        self.assertGreaterEqual(len(out["reasons"]), 4)

    def test_higher_is_better(self):
        out = evaluate_promotion_gate(
            validation_status="validated",
            data_quality_score=0.9,
            drift_status="not_configured",
            champion_metric=0.70,
            challenger_metric=0.77,
            metric_direction="higher_better",
            minimum_improvement=0.05,
            evidence_fingerprint="fp",
        )
        self.assertTrue(out["eligible"])


if __name__ == "__main__":
    unittest.main()
