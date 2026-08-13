"""Desktop API regression coverage for the controlled v4.0 capacity draft."""

import json
import unittest

from app import API


class DesktopV4BridgeTests(unittest.TestCase):
    def test_capacity_draft_uses_offline_mode_and_never_applies_a_change(self):
        response = json.loads(
            API().create_v4_queue_proposal(
                json.dumps(
                    {
                        "historical_counts": [8, 11, 13, 19, 22, 24, 20, 18],
                        "tiers": [
                            {"name": "Triage", "servers": 2, "mean_service_time": 0.6, "service_cv": 0.8},
                            {"name": "Consultation", "servers": 3, "mean_service_time": 0.9, "service_cv": 1.0},
                        ],
                        "server_range": [1, 3],
                        "replications": 30,
                        "enable_llm": False,
                    }
                )
            )
        )
        self.assertNotIn("error", response)
        proposal = response["proposal"]
        self.assertEqual(proposal["execution_mode"], "deterministic-offline")
        self.assertTrue(proposal["approval_required"])
        self.assertFalse(proposal["applied"])
        self.assertFalse(proposal["external_operations_performed"])
        self.assertGreater(response["pareto_summary"]["candidate_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
