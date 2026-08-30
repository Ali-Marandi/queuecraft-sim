import json
import tempfile
import unittest
from pathlib import Path

from decision_ledger import DecisionLedger


class DecisionLedgerTests(unittest.TestCase):
    def test_append_chain_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = DecisionLedger(Path(tmp) / "ledger.jsonl")
            first = ledger.append("drift_detected", {"score": 0.42})
            second = ledger.append("promotion_blocked", {"reason": "regression"})
            self.assertIsNone(first["previous_hash"])
            self.assertEqual(second["previous_hash"], first["event_hash"])
            self.assertTrue(ledger.verify()["valid"])

    def test_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            ledger = DecisionLedger(path)
            ledger.append("evaluation", {"rmse": 2.0})
            raw = json.loads(path.read_text(encoding="utf-8"))
            raw["payload"]["rmse"] = 0.1
            path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
            self.assertFalse(ledger.verify()["valid"])

    def test_read_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = DecisionLedger(Path(tmp) / "ledger.jsonl")
            for index in range(4):
                ledger.append("metric", {"index": index})
            self.assertEqual(len(ledger.read(limit=2)), 2)


if __name__ == "__main__":
    unittest.main()
