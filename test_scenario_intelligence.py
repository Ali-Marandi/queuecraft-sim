import unittest

from scenario_intelligence import (
    build_scenario_graph,
    counterfactual_scale,
    governance_manifest,
)


class ScenarioIntelligenceTests(unittest.TestCase):
    def test_graph_propagates_and_ranks(self):
        out = build_scenario_graph(
            [
                {"id": "rates", "shock": 1.0},
                {"id": "liquidity", "shock": 0.0},
                {"id": "ops", "shock": 0.0},
            ],
            [
                {"from": "rates", "to": "liquidity", "weight": 0.5},
                {"from": "liquidity", "to": "ops", "weight": 0.8},
            ],
        )
        self.assertGreater(out["scores"]["liquidity"], 0.0)
        self.assertGreater(out["scores"]["ops"], 0.0)
        self.assertEqual(out["ranking"][0]["node"], "rates")

    def test_counterfactual_is_transparent(self):
        out = counterfactual_scale([10, 20, 30], 1.2, 1.1)
        self.assertEqual(out, [13.2, 26.4, 39.6])

    def test_governance_manifest_fingerprints_and_controls(self):
        manifest = governance_manifest(
            inputs={"market": {}, "operational": {}},
            models=["market_intelligence", "decision_engine"],
            assumptions=["operator-specified linkage"],
            ai_enabled=False,
        )
        self.assertEqual(len(manifest["manifest_fingerprint"]), 64)
        self.assertTrue(manifest["controls"]["human_approval_required"])
        self.assertFalse(manifest["controls"]["external_operations_performed"])


if __name__ == "__main__":
    unittest.main()
