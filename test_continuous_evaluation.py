import unittest

from continuous_evaluation import EvaluationPolicy, continuous_evaluation


class ContinuousEvaluationTests(unittest.TestCase):
    def test_clean_candidate_is_eligible(self):
        champion = {"primary_loss": 1.0, "sla_failure_rate": 0.05, "latency_p95": 100.0, "bias": 0.01}
        challenger = {"primary_loss": 0.8, "sla_failure_rate": 0.04, "latency_p95": 98.0, "bias": 0.009}
        result = continuous_evaluation(champion, challenger, 0.95, 0.05)
        self.assertEqual(result["status"], "eligible_for_promotion_review")
        self.assertTrue(result["human_approval_required"])
        self.assertEqual(result["deployment"], "blocked")

    def test_regression_blocks(self):
        champion = {"primary_loss": 1.0, "sla_failure_rate": 0.05, "latency_p95": 100.0, "bias": 0.01}
        challenger = {"primary_loss": 0.8, "sla_failure_rate": 0.08, "latency_p95": 130.0, "bias": 0.012}
        result = continuous_evaluation(champion, challenger, 0.95, 0.05)
        self.assertTrue(result["promotion_blocked"])
        self.assertEqual(result["guardrails"]["status"], "blocked")

    def test_bad_data_or_high_drift_blocks(self):
        champion = {"primary_loss": 1.0, "sla_failure_rate": 0.05, "latency_p95": 100.0, "bias": 0.01}
        challenger = {"primary_loss": 0.8, "sla_failure_rate": 0.04, "latency_p95": 98.0, "bias": 0.009}
        result = continuous_evaluation(champion, challenger, 0.5, 0.4, EvaluationPolicy())
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
