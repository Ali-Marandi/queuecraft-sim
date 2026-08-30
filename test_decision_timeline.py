import tempfile
import unittest
from pathlib import Path

from decision_ledger import DecisionLedger
from decision_timeline import query_ledger, timeline_summary


class DecisionTimelineTests(unittest.TestCase):
    def test_summary_counts_event_types(self):
        events = [
            {"event_type": "drift_evaluation", "created_at": 1, "event_hash": "a"},
            {"event_type": "drift_evaluation", "created_at": 2, "event_hash": "b"},
            {"event_type": "promotion_blocked", "created_at": 3, "event_hash": "c"},
        ]
        summary = timeline_summary(events)
        self.assertEqual(summary["event_count"], 3)
        self.assertEqual(summary["event_types"]["drift_evaluation"], 2)
        self.assertTrue(summary["integrity_ready"])

    def test_query_filters_without_changing_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            ledger = DecisionLedger(path)
            ledger.append("drift_evaluation", {"score": 0.1})
            ledger.append("promotion_blocked", {"reason": "regression"})
            result = query_ledger(path, event_type="drift_evaluation")
            self.assertEqual(len(result["events"]), 1)
            self.assertTrue(result["integrity"]["valid"])


if __name__ == "__main__":
    unittest.main()
