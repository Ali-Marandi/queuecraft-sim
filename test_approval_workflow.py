import unittest

from approval_workflow import create_request, transition, workflow_snapshot


class ApprovalWorkflowTests(unittest.TestCase):
    def test_approval_requires_matching_role(self):
        request = create_request(request_id="AR-1", decision_id="D-1", required_role="ops-manager")
        with self.assertRaises(ValueError):
            transition(request, new_state="approved", reviewer_id="u1", role="analyst")

    def test_approval_records_human_action_without_deployment(self):
        request = create_request(request_id="AR-2", decision_id="D-2")
        approved = transition(request, new_state="approved", reviewer_id="u2", role="reviewer", review_note="approved after review")
        self.assertEqual(approved["state"], "approved")
        self.assertEqual(approved["reviewer_id"], "u2")
        self.assertFalse(approved["deployment_performed"])
        with self.assertRaises(ValueError):
            transition(approved, new_state="rejected", reviewer_id="u3", role="reviewer")

    def test_summary(self):
        requests = [
            create_request(request_id="AR-3", decision_id="D-3"),
            create_request(request_id="AR-4", decision_id="D-4"),
        ]
        requests.append(transition(requests[0], new_state="rejected", reviewer_id="u4", role="reviewer"))
        summary = workflow_snapshot(requests)
        self.assertEqual(summary["request_count"], 3)
        self.assertEqual(summary["states"]["pending"], 1)
        self.assertEqual(summary["states"]["rejected"], 1)
        self.assertFalse(summary["governance"]["automatic_approval"])


if __name__ == "__main__":
    unittest.main()
