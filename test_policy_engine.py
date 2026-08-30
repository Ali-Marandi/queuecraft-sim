import unittest

from policy_engine import PolicyRule, PolicySet, evaluate_policy, policy_from_mapping


class PolicyEngineTests(unittest.TestCase):
    def test_block_wins_over_review(self):
        policy = PolicySet("ops", "1.0", (
            PolicyRule("sla", "risk.screening_sla_failure_risk", "gt", 0.25, "review"),
            PolicyRule("critical", "risk.screening_sla_failure_risk", "gt", 0.50, "block"),
        ), default_action="allow")
        result = evaluate_policy(policy, {"risk": {"screening_sla_failure_risk": 0.60}})
        self.assertEqual(result["action"], "block")
        self.assertTrue(result["blocked"])

    def test_default_review(self):
        policy = PolicySet("ops", "1.0", (), default_action="review")
        result = evaluate_policy(policy, {"risk": {"score": 0.1}})
        self.assertTrue(result["review_required"])

    def test_missing_field_is_not_evaluable(self):
        policy = PolicySet("ops", "1.0", (PolicyRule("r1", "risk.score", "gt", 0.8, "block"),), default_action="allow")
        result = evaluate_policy(policy, {"risk": {}})
        self.assertEqual(result["action"], "allow")
        self.assertEqual(result["checks"][0]["status"], "not_evaluable")

    def test_mapping_parser(self):
        policy = policy_from_mapping({"policy_id": "p", "version": "2", "default_action": "block", "rules": []})
        self.assertEqual(policy.policy_id, "p")
        self.assertEqual(policy.default_action, "block")


if __name__ == "__main__":
    unittest.main()
