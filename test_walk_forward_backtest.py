import unittest

from walk_forward_backtest import regime_label, select_champion, walk_forward
from regime_aware_model_selection import current_regime_recommendation, select_by_regime


class WalkForwardBacktestTests(unittest.TestCase):
    def test_walk_forward_is_chronological(self):
        data = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]
        models = {
            "last": lambda history: history[-1],
            "mean": lambda history: sum(history) / len(history),
        }
        folds, summaries = walk_forward(data, models, min_train_size=4)
        self.assertEqual(folds[0].test_index, 4)
        self.assertEqual(len(summaries), 2)

    def test_champion_prefers_lower_error(self):
        data = [10, 12, 14, 16, 18, 20, 22, 24]
        models = {
            "last": lambda history: history[-1],
            "perfect_linear": lambda history: history[-1] + 2,
        }
        _, summaries = walk_forward(data, models, min_train_size=4)
        champion = select_champion(summaries)
        self.assertEqual(champion.model_id, "perfect_linear")

    def test_regime_and_regime_winner(self):
        self.assertIn(regime_label([10, 10, 10, 20, 20, 30]), {"surge", "volatile"})
        data = [10, 11, 12, 13, 14, 20, 22, 24, 26, 28]
        models = {"last": lambda history: history[-1], "plus_two": lambda history: history[-1] + 2}
        folds, _ = walk_forward(data, models, min_train_size=5)
        winners = select_by_regime(data, folds)
        recommendation = current_regime_recommendation(data, winners)
        self.assertIn(recommendation["status"], {"validated_regime_match", "no_validated_regime_winner"})


if __name__ == "__main__":
    unittest.main()
