import unittest

from challenger_orchestrator import (
    build_challenger_trigger,
    orchestrate_challenger_evaluation,
    select_challenger,
)


class ChallengerOrchestratorTests(unittest.TestCase):
    def test_non_drift_does_not_trigger(self):
        result = orchestrate_challenger_evaluation(
            {"status": "stable"},
            [{"model_id": "m2", "status": "candidate", "validation_status": "passed"}],
        )
        self.assertEqual(result["status"], "not_triggered")
        self.assertFalse(result["trigger"]["evaluation_requested"])
        self.assertEqual(result["deployment"], "blocked")

    def test_drift_selects_highest_priority_candidate(self):
        candidates = [
            {"model_id": "low", "status": "candidate", "validation_status": "passed", "priority": 1},
            {"model_id": "high", "status": "candidate", "validation_status": "passed", "priority": 5},
        ]
        chosen = select_challenger(candidates)
        self.assertEqual(chosen["model_id"], "high")

    def test_current_model_is_excluded_and_local_evaluation_allowed(self):
        calls = []
        candidates = [
            {"model_id": "champ", "status": "candidate", "validation_status": "passed", "priority": 10},
            {"model_id": "challenger", "status": "candidate", "validation_status": "passed", "priority": 3},
        ]

        def evaluator(candidate):
            calls.append(candidate["model_id"])
            return {"mae": 0.4, "rmse": 0.6}

        result = orchestrate_challenger_evaluation(
            {"status": "drift_detected"},
            candidates,
            current_model_id="champ",
            evaluator=evaluator,
        )
        self.assertEqual(result["status"], "evaluation_completed")
        self.assertEqual(result["candidate"]["model_id"], "challenger")
        self.assertEqual(result["evaluation"]["rmse"], 0.6)
        self.assertEqual(calls, ["challenger"])
        self.assertEqual(result["deployment"], "blocked")
        self.assertTrue(result["human_approval_required"])

    def test_trigger_contract(self):
        trigger = build_challenger_trigger({"status": "drift_detected"})
        self.assertTrue(trigger.evaluation_requested)
        self.assertEqual(trigger.source, "streaming_drift")
        self.assertEqual(trigger.deployment, "blocked")


if __name__ == "__main__":
    unittest.main()
