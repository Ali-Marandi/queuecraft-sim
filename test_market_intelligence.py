import unittest

import numpy as np

from market_intelligence import (
    altman_z_score,
    analyze_market_snapshot,
    beneish_m_score,
    black_litterman,
    capm,
    contagion_network,
    factor_regression,
    garch11_forecast,
    macro_regime,
    taylor_rule_rate,
    topsis,
)


class MarketIntelligenceTests(unittest.TestCase):
    def test_taylor_rule_and_macro_regime(self):
        self.assertAlmostEqual(taylor_rule_rate(2.0, 0.0), 4.0)
        out = macro_regime({"inflation": 3.5, "output_gap_pct": 1.5, "policy_rate": 5.0})
        self.assertEqual(out["regime"], "overheating_tightening")

    def test_factor_and_capm(self):
        market = np.array([-.02, .01, .03, .00, .02, -.01])
        asset = 0.004 + 1.2 * market
        capm_out = capm(asset, market)
        self.assertAlmostEqual(capm_out["beta"], 1.2, places=4)
        out = factor_regression(asset, {"market": market, "value": np.zeros(len(market))})
        self.assertAlmostEqual(out["loadings"]["market"], 1.2, places=4)

    def test_garch_is_positive_and_deterministic(self):
        r = np.array([0.01 * ((i % 7) - 3) for i in range(60)], dtype=float)
        a = garch11_forecast(r, horizon=4)
        b = garch11_forecast(r, horizon=4)
        self.assertEqual(a, b)
        self.assertTrue(all(x > 0 for x in a["variance_forecast"]))
        self.assertLess(a["persistence"], 1.0)

    def test_financial_screening(self):
        self.assertEqual(altman_z_score(1, 1, 1, 1, 1)["zone"], "safe")
        self.assertIn("m_score", beneish_m_score(1, 1, 1, 1, 1, 1, 0, 1))

    def test_black_litterman_and_topsis(self):
        bl = black_litterman(
            [0.6, 0.4],
            [[0.04, 0.01], [0.01, 0.03]],
            2.5,
            [0.03],
            [[1.0, -1.0]],
        )
        self.assertEqual(len(bl["posterior_returns"]), 2)
        tx = topsis([[0.8, 10], [0.7, 6], [0.9, 8]], [0.6, 0.4], [True, False])
        self.assertEqual(sorted(tx["ranking"]), [0, 1, 2])

    def test_network_contagion_is_bounded(self):
        out = contagion_network([[0, 1, 0], [1, 0, 1], [0, 1, 0]], 0, shock=1, steps=4)
        self.assertEqual(len(out["shock_paths"]), 5)
        self.assertTrue(all(abs(v) < 2 for row in out["shock_paths"] for v in row))

    def test_unified_snapshot(self):
        returns = [0.01 * ((i % 5) - 2) for i in range(30)]
        out = analyze_market_snapshot(
            {
                "macro": {"inflation": 2.3, "output_gap_pct": 0.5, "policy_rate": 3.8},
                "asset_returns": returns,
                "factors": {"market_excess": returns},
                "base": {"market": 0.0},
                "shocks": {"rates": 1.0, "political": 0.5, "climate": 0.2},
                "sensitivities": {"rates": 0.8, "political": 0.7, "climate": 0.5},
                "behavior": {"winner_sell_ratio": 0.5, "loser_sell_ratio": 0.2, "top5_weight": 0.55, "turnover": 1.0},
            }
        )
        self.assertEqual(out["engine_version"], "1.0.0")
        self.assertIn("macro", out)
        self.assertIn("frontier", out)


if __name__ == "__main__":
    unittest.main()
