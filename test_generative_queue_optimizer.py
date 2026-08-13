"""Offline regression tests for the constrained v4.0 generative advisor."""

import unittest

from generative_queue_optimizer import build_evidence_pack, create_deterministic_proposal


PARETO = {
    "objectives": {"sla_mean_wait": 5.0, "cost_per_server": 1.0},
    "tiers": ["triage", "consultation"],
    "pareto_frontier": [
        {"servers": [1, 1], "server_cost": 2.0, "mean_wait": 9.0, "p95_wait": 16.0, "mean_utilization_pct": 96.0, "sla_compliant": False},
        {"servers": [2, 2], "server_cost": 4.0, "mean_wait": 4.0, "p95_wait": 7.0, "mean_utilization_pct": 74.0, "sla_compliant": True},
        {"servers": [3, 3], "server_cost": 6.0, "mean_wait": 2.5, "p95_wait": 4.0, "mean_utilization_pct": 52.0, "sla_compliant": True},
    ],
}


class GenerativeQueueOptimizerTests(unittest.TestCase):
    def test_deterministic_advisor_uses_verified_lowest_cost_eligible_candidate(self):
        proposal = create_deterministic_proposal(PARETO)
        self.assertEqual(proposal["selected_candidate"]["candidate_id"], "plan-2")
        self.assertTrue(proposal["approval_required"])
        self.assertFalse(proposal["applied"])
        self.assertFalse(proposal["external_operations_performed"])
        self.assertEqual(proposal["execution_mode"], "deterministic-offline")

    def test_infeasible_constraints_emit_low_confidence_review_draft(self):
        proposal = create_deterministic_proposal(PARETO, constraints={"max_mean_wait": 1.0})
        self.assertEqual(proposal["selected_candidate"]["candidate_id"], "plan-3")
        self.assertEqual(proposal["confidence"], "low")
        self.assertIn("infeasible", " ".join(proposal["risks"]).lower())

    def test_evidence_pack_has_deterministic_fingerprint_and_catalog_only(self):
        evidence_one = build_evidence_pack(PARETO, constraints={"max_server_cost": 5.0})
        evidence_two = build_evidence_pack(PARETO, constraints={"max_server_cost": 5.0})
        self.assertEqual(evidence_one["evidence_fingerprint"], evidence_two["evidence_fingerprint"])
        self.assertEqual([row["candidate_id"] for row in evidence_one["candidate_catalog"]], ["plan-1", "plan-2", "plan-3"])
        self.assertNotIn("historical_counts", evidence_one)


if __name__ == "__main__":
    unittest.main(verbosity=2)
