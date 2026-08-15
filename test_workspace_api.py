import json
import tempfile
import unittest
from pathlib import Path

from app import API
from scenario_manager import ScenarioRepository


class WorkspaceApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        api = API()
        api.repository = ScenarioRepository(Path(self.temp_dir.name))
        self.api = api

    def tearDown(self):
        self.temp_dir.cleanup()

    def scenario_payload(self):
        return {
            "scenario": {
                "name": "Workspace smoke test",
                "description": "Deterministic audit fixture",
                "historical_counts": [8, 11, 13, 19, 22, 24],
                "tiers": [{"name": "Service", "servers": 2, "mean_service_time": 0.9, "service_cv": 1.0}],
                "simulation": {"horizon": 2, "replications": 30, "seed": 7},
                "sla": {"max_end_to_end_mean_wait": 5.0},
            }
        }

    def test_load_delete_and_export_are_integrity_safe(self):
        saved = json.loads(self.api.save_scenario(json.dumps(self.scenario_payload())))
        scenario_id = saved["id"]
        loaded = json.loads(self.api.load_scenario(scenario_id))
        self.assertEqual(loaded["fingerprint"], saved["fingerprint"])

        report = json.loads(self.api.export_scenario_report(scenario_id))
        self.assertEqual(report["product"], "QueueCraft Enterprise AI")
        self.assertEqual(report["scenario"]["fingerprint"], saved["fingerprint"])
        self.assertIn(report["sla"]["status"], {"pass", "fail"})

        deleted = json.loads(self.api.delete_scenario(scenario_id))
        self.assertTrue(deleted["deleted"])
        self.assertIn("error", json.loads(self.api.load_scenario(scenario_id)))


if __name__ == "__main__":
    unittest.main()

