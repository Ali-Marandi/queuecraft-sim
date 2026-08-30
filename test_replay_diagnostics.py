import unittest

from replay_diagnosis import classify_changed_fields


class ReplayDiagnosticsTests(unittest.TestCase):
    def test_primary_category_prefers_data(self):
        result = classify_changed_fields(["input.history[0]", "model.version", "input.history[1]"])
        self.assertEqual(result["primary_category"], "data")
        self.assertEqual(result["diagnosis_confidence"], "heuristic")

    def test_execution_fields_are_classified(self):
        result = classify_changed_fields(["seed", "simulation.replications"])
        self.assertEqual(result["primary_category"], "execution")

    def test_empty_is_undetermined(self):
        result = classify_changed_fields([])
        self.assertIsNone(result["primary_category"])
        self.assertEqual(result["changed_field_count"], 0)


if __name__ == "__main__":
    unittest.main()
