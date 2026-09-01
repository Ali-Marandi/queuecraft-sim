import json
import unittest

from model_governance_service import evaluate_model_governance_json


class ModelGovernanceServiceTests(unittest.TestCase):
    def test_service_returns_governance_report(self):
        payload = {
            "observations": [10, 11, 12, 11, 13, 14, 15, 14, 16, 17],
            "models": {"last_value": {}, "mean": {}},
            "candidates": [
                {"model_id": "m1", "family": "forecast", "version": "1", "metrics": {"rmse": 1.2}},
            ],
            "champion_metric": 1.2,
            "challenger_metric": 1.1,
            "data_quality_score": 0.95,
            "drift_status": "stable",
            "validation_status": "validated",
            "evidence_fingerprint": "a" * 64,
        }
        result = json.loads(evaluate_model_governance_json(json.dumps(payload)))
        self.assertIn("validation", result)
        self.assertIn("promotion_gate", result)
        self.assertFalse(result["governance"]["automatic_promotion"])
        self.assertFalse(result["governance"]["deployment_performed"])

    def test_unknown_model_is_rejected(self):
        payload = {"observations": [1, 2, 3], "models": {"unknown": {}}, "candidates": [], "champion_metric": 1, "challenger_metric": 1}
        result = json.loads(evaluate_model_governance_json(json.dumps(payload)))
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
