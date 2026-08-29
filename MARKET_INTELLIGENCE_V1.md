# QueueCraft Market Intelligence v1

QueueCraft now includes a deterministic cross-disciplinary market-intelligence layer for research and scenario analysis. It does not fetch live prices, submit orders, or act as investment advice.

## Implemented analytics

- **Macro regime:** Taylor-style policy-rate estimate, policy-vs-rule gap, and transparent regime buckets.
- **Asset pricing:** CAPM and arbitrary-factor OLS, including Fama/French-style inputs such as market excess return, SMB, HML, RMW, and CMA.
- **Volatility:** deterministic GARCH(1,1) estimation/forecasting with bounded grid search.
- **Accounting screens:** classic Altman Z-score and Beneish M-score calculations from supplied ratios.
- **Portfolio views:** Black-Litterman posterior-return calculation from market weights, covariance and explicit views.
- **Systemic risk:** bounded network-contagion simulation plus an eigenvector-centrality proxy.
- **Behavioral indicators:** supplied-summary proxies for disposition, concentration and turnover/overconfidence risk.
- **Decision ranking:** TOPSIS and a simple fuzzy membership primitive for qualitative uncertainty.
- **Scenario stress:** transparent aggregation of rate, political, climate, liquidity and other user-supplied shocks.

## Research frontier

The following source topics are intentionally exposed as roadmap metadata rather than production claims: DSGE, causal ML, topological data analysis, diffusion-based synthetic finance, quantum finance, federated learning, and ANFIS. Each requires domain-specific calibration, identification, validation, or infrastructure beyond the current offline desktop scope.

## Verification

Run:

```bash
python -m unittest -v test_market_intelligence.py
```

Or run it with the project's broader AI suite:

```bash
npm run test:ai
```

Example:

```bash
python market_intelligence_cli.py examples/global_market_intelligence.json --output artifacts/market-intelligence.json
```

## Scientific positioning

The implementation deliberately separates **model calculation** from **prediction claims**. For example, the GARCH module produces conditional-variance forecasts; it does not claim that these forecasts produce positive trading returns. Likewise, the Taylor component is an analytical policy-rule benchmark, not a forecast of a central bank's actual next decision.
