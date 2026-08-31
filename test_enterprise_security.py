import unittest

from enterprise_security import Principal, authorize, validate_operation_request


class EnterpriseSecurityTests(unittest.TestCase):
    def test_permission_and_role_are_both_required(self):
        principal = Principal("u1", frozenset({"reviewer"}), frozenset({"decision.approve"}))
        self.assertTrue(authorize(principal, "decision.approve", required_role="reviewer")["allowed"])
        self.assertFalse(authorize(principal, "decision.execute", required_role="reviewer")["allowed"])
        self.assertFalse(authorize(principal, "decision.approve", required_role="admin")["allowed"])

    def test_external_automatic_execution_is_blocked(self):
        result = validate_operation_request({"operation": "deploy", "risk_level": "high", "external_side_effect": True, "automatic_execution": True})
        self.assertFalse(result["valid"])
        self.assertEqual(result["status"], "blocked")

    def test_high_risk_requires_review(self):
        result = validate_operation_request({"operation": "promote_model", "risk_level": "critical"})
        self.assertEqual(result["status"], "review_required")

    def test_invalid_risk_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_operation_request({"operation": "x", "risk_level": "extreme"})


if __name__ == "__main__":
    unittest.main()
