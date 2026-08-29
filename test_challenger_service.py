import json
import unittest

from challenger_service import build_evaluation_request, build_evaluation_request_json


class ChallengerServiceTests(unittest.TestCase):
    def payload(self):
        return {
            "drift": {"status": "drift_detected"},
            "current_model_id": "champion-v1",
            "family": "forecast",
            "registry_candidates": [
                {"model_id": "challenger-v2", "family": "forecast", "version": "2.0", "status": "candidate", "validation_status": "passed", "priority": 4},
                {"model_id": "other-v1", "family": "capacity", "version": "1.0", "status": "candidate", "validation_status": "passed", "priority": 9},
            ],
        }

    def test_service_filters_by_family(self):
        result = build_evaluation_request(self.payload())
        self.assertEqual(result["status"], "evaluation_requested")
        self.assertEqual(result["candidate"]["model_id"], "challenger-v2")
        self.assertEqual(result["deployment"], "blocked")

    def test_json_adapter(self):
        result = json.loads(build_evaluation_request_json(json.dumps(self.payload())))
        self.assertTrue(result["human_approval_required"])


if __name__ == "__main__":
    unittest.main()
