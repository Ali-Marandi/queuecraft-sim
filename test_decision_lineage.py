import unittest

from decision_lineage import build_lineage_from_evidence, build_lineage_graph, fingerprint, lineage_subgraph


class DecisionLineageTests(unittest.TestCase):
    def test_builds_typed_graph(self):
        graph = build_lineage_graph(
            [
                {"id": "data-1", "type": "data", "label": "Arrivals"},
                {"id": "model-1", "type": "model", "label": "Forecast v1"},
                {"id": "decision-1", "type": "decision", "label": "Capacity decision"},
            ],
            [
                {"from": "data-1", "to": "model-1", "type": "uses"},
                {"from": "model-1", "to": "decision-1", "type": "supports"},
            ],
        )
        self.assertEqual(graph["node_count"], 3)
        self.assertEqual(graph["edge_count"], 2)
        self.assertEqual(graph["roots"], ["data-1"])
        self.assertEqual(graph["leaves"], ["decision-1"])
        self.assertEqual(len(graph["graph_fingerprint"]), 64)

    def test_ancestor_query(self):
        graph = build_lineage_graph(
            [{"id": "a", "type": "data"}, {"id": "b", "type": "model"}, {"id": "c", "type": "decision"}],
            [{"from": "a", "to": "b", "type": "uses"}, {"from": "b", "to": "c", "type": "supports"}],
        )
        sub = lineage_subgraph(graph, "c", direction="ancestors")
        self.assertEqual({n["node_id"] for n in sub["nodes"]}, {"a", "b", "c"})

    def test_evidence_builder_links_common_entities(self):
        evidence = {
            "decision_id": "dec-1",
            "decision": {"capacity": 11},
            "scenario_id": "scn-1",
            "scenario_fingerprint": fingerprint({"scenario": 1}),
            "models": [{"model_id": "m-1", "version": "1.0"}],
            "source_data": [{"asset_id": "data-1", "source_type": "csv"}],
            "experiment": {"metric": "rmse", "mean_difference": -0.2},
            "approval": {"id": "apr-1", "status": "pending"},
            "replay": {"status": "identical", "replay_fingerprint": "abc"},
            "replay_id": "replay-1",
        }
        graph = build_lineage_from_evidence(evidence)
        ids = {n["node_id"] for n in graph["nodes"]}
        self.assertGreaterEqual(graph["node_count"], 6)
        self.assertIn("dec-1", ids)
        self.assertIn("replay-1", ids)
        self.assertTrue(any(e["edge_type"] == "approved_by" for e in graph["edges"]))
        self.assertTrue(any(e["edge_type"] == "evaluated_by" for e in graph["edges"]))
        self.assertTrue(any(e["edge_type"] == "replayed_from" for e in graph["edges"]))

    def test_rejects_unknown_edge_endpoint(self):
        with self.assertRaises(ValueError):
            build_lineage_graph([{"id": "a", "type": "data"}], [{"from": "a", "to": "missing", "type": "uses"}])

    def test_rejects_cycles(self):
        with self.assertRaises(ValueError):
            build_lineage_graph(
                [{"id": "a", "type": "data"}, {"id": "b", "type": "model"}],
                [{"from": "a", "to": "b", "type": "uses"}, {"from": "b", "to": "a", "type": "supports"}],
            )


if __name__ == "__main__":
    unittest.main()
