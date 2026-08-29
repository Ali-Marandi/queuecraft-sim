import json
import unittest

from model_lifecycle_service import evaluate_model_lifecycle_json


class ModelLifecycleServiceTests(unittest.TestCase):
    def test_json_adapter_returns_comparison(self):
        payload = {
            "models": [
                {"model_id": "a", "family": "forecast", "version": "1", "metrics": {"rmse": 3.0}},
                {"model_id": "b", "family": "forecast", "version": "2", "metrics": {"rmse": 2.0}},
            ]
        }
        out = json.loads(evaluate_model_lifecycle_json(json.dumps(payload)))
        self.assertEqual(out["comparison"]["recommended_candidate"], "b")
        self.assertFalse(out["comparison"]["promotion"]["automatic"])

    def test_json_adapter_validates_root_type(self):
        out = json.loads(evaluate_model_lifecycle_json("[]"))
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
