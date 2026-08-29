"""QueueCraft market-intelligence layer.

This module translates a curated subset of the financial/economic sciences
into deterministic, auditable calculations suitable for scenario analysis.
It intentionally does not fetch live market data or place trades.

Implemented families:
- macro regime + Taylor-rule gap
- CAPM and Fama/French-style factor regression
- GARCH(1,1) variance forecasting
- Altman Z and Beneish M screening
- Black-Litterman posterior returns
- network contagion stress simulation
- behavioral, fuzzy and TOPSIS scoring
- political/climate stress scenario aggregation

Research-only families are exposed via ``research_frontier`` so the product
can distinguish executable analytics from methods that require future data,
validation, or specialist infrastructure.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp, log, sqrt
from typing import Any, Mapping, Sequence

import numpy as np


RESEARCH_FRONTIER = {
    "DSGE": "research_only: needs calibrated macro blocks and external priors",
    "causal_ml": "research_only: requires identification strategy and validated instruments",
    "topological_data_analysis": "research_only: useful for regime-change research, not an operational signal here",
    "diffusion_finance": "research_only: synthetic path generation needs dedicated validation",
    "quantum_finance": "research_only: hardware/runtime advantage is not established for this product",
    "federated_learning": "research_only: requires multi-party training and privacy infrastructure",
    "ANFIS": "research_only: model fitting and governance not enabled by default",
}


@dataclass(frozen=True)
class TaylorRuleConfig:
    neutral_real_rate: float = 2.0
    inflation_target: float = 2.0
    inflation_weight: float = 0.5
    output_gap_weight: float = 0.5


def taylor_rule_rate(inflation: float, output_gap_pct: float, config: TaylorRuleConfig | None = None) -> float:
    """Return the policy rate implied by a standard Taylor-style rule."""
    cfg = config or TaylorRuleConfig()
    return cfg.neutral_real_rate + inflation + cfg.inflation_weight * (inflation - cfg.inflation_target) + cfg.output_gap_weight * output_gap_pct


def macro_regime(snapshot: Mapping[str, float], config: TaylorRuleConfig | None = None) -> dict[str, Any]:
    """Score a macro snapshot into transparent regime buckets."""
    inflation = float(snapshot["inflation"])
    output_gap = float(snapshot.get("output_gap_pct", 0.0))
    policy_rate = float(snapshot["policy_rate"])
    implied = taylor_rule_rate(inflation, output_gap, config)
    gap = policy_rate - implied
    if inflation > (config or TaylorRuleConfig()).inflation_target + 1.0 and output_gap > 0:
        regime = "overheating_tightening"
    elif inflation > (config or TaylorRuleConfig()).inflation_target and output_gap < 0:
        regime = "stagflation_risk"
    elif inflation < (config or TaylorRuleConfig()).inflation_target and output_gap < -1.0:
        regime = "disinflation_slack"
    elif output_gap > 1.0 and inflation <= (config or TaylorRuleConfig()).inflation_target:
        regime = "expansion_balanced"
    else:
        regime = "mixed_transition"
    return {
        "regime": regime,
        "taylor_implied_rate": round(implied, 4),
        "policy_vs_rule_gap": round(gap, 4),
        "inputs": dict(snapshot),
    }


def _ols(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residuals = y - X @ beta
    ss_res = float(residuals @ residuals)
    ss_tot = float(((y - y.mean()) @ (y - y.mean())))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
    return beta, residuals, r2


def factor_regression(asset_returns: Sequence[float], factor_returns: Mapping[str, Sequence[float]]) -> dict[str, Any]:
    """Fit an intercept plus supplied factor returns (CAPM/FF-style)."""
    names = list(factor_returns)
    arrays = [np.asarray(factor_returns[name], dtype=float) for name in names]
    y = np.asarray(asset_returns, dtype=float)
    n = min(len(y), *(len(a) for a in arrays))
    if n < len(names) + 3:
        raise ValueError("insufficient observations for factor regression")
    X = np.column_stack([np.ones(n), *[a[:n] for a in arrays]])
    beta, residuals, r2 = _ols(y[:n], X)
    return {
        "intercept": float(beta[0]),
        "factor_names": names,
        "loadings": {name: float(beta[i + 1]) for i, name in enumerate(names)},
        "r_squared": float(r2),
        "residual_volatility": float(np.std(residuals, ddof=1)),
        "observations": n,
    }


def capm(asset_returns: Sequence[float], market_returns: Sequence[float], risk_free: Sequence[float] | float = 0.0) -> dict[str, float]:
    rf = np.full(len(asset_returns), float(risk_free)) if np.isscalar(risk_free) else np.asarray(risk_free, dtype=float)
    y = np.asarray(asset_returns, dtype=float) - rf
    m = np.asarray(market_returns, dtype=float) - rf[: len(market_returns)]
    n = min(len(y), len(m))
    result = factor_regression(y[:n], {"market_excess": m[:n]})
    return {"alpha": result["intercept"], "beta": result["loadings"]["market_excess"], "r_squared": result["r_squared"]}


def garch11_forecast(returns: Sequence[float], horizon: int = 1, omega: float | None = None, alpha: float | None = None, beta: float | None = None) -> dict[str, Any]:
    """Forecast conditional variance with a simple GARCH(1,1) estimator.

    The estimator uses a deterministic moment/grid search rather than an
    external optimizer, keeping the desktop app dependency-light.
    """
    r = np.asarray(returns, dtype=float)
    if len(r) < 20:
        raise ValueError("at least 20 returns are required")
    r = r - r.mean()
    h = max(float(np.var(r)), 1e-12)
    if omega is None or alpha is None or beta is None:
        best = (float("inf"), max(h * 0.05, 1e-8), 0.08, 0.88)
        for a in np.linspace(0.03, 0.20, 18):
            for b in np.linspace(0.65, 0.95, 16):
                if a + b >= 0.995:
                    continue
                o = max(h * (1.0 - a - b), 1e-8)
                var = h
                nll = 0.0
                for x in r:
                    var = o + a * x * x + b * var
                    nll += log(var) + (x * x) / var
                if nll < best[0]:
                    best = (nll, o, a, b)
        _, omega, alpha, beta = best
    var = h
    for x in r:
        var = omega + alpha * x * x + beta * var
    forecasts = []
    next_var = var
    long_run = omega / max(1.0 - alpha - beta, 1e-9)
    for _ in range(horizon):
        next_var = omega + (alpha + beta) * next_var
        forecasts.append(float(next_var))
    return {
        "omega": float(omega),
        "alpha": float(alpha),
        "beta": float(beta),
        "persistence": float(alpha + beta),
        "long_run_variance": float(long_run),
        "variance_forecast": forecasts,
        "volatility_forecast": [sqrt(v) for v in forecasts],
    }


def altman_z_score(x1: float, x2: float, x3: float, x4: float, x5: float) -> dict[str, Any]:
    """Classic manufacturing Altman Z-score screening calculation."""
    z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
    zone = "distress" if z < 1.81 else "grey" if z <= 2.99 else "safe"
    return {"z_score": round(z, 4), "zone": zone}


def beneish_m_score(dsri: float, gmi: float, aqi: float, sgi: float, depi: float, sgai: float, tata: float, lvgi: float) -> dict[str, Any]:
    """Beneish M-score screening calculation from the eight published ratios."""
    m = -4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi
    return {"m_score": round(m, 4), "screening_flag": m > -1.78, "threshold": -1.78}


def black_litterman(market_weights: Sequence[float], cov: Sequence[Sequence[float]], risk_aversion: float, views: Sequence[float], view_matrix: Sequence[Sequence[float]], tau: float = 0.05, view_confidence: float = 1.0) -> dict[str, Any]:
    w = np.asarray(market_weights, dtype=float)
    sigma = np.asarray(cov, dtype=float)
    P = np.asarray(view_matrix, dtype=float)
    Q = np.asarray(views, dtype=float)
    pi = risk_aversion * sigma @ w
    omega = np.eye(len(Q)) * max(tau, 1e-9) / max(view_confidence, 1e-9)
    prior_precision = np.linalg.pinv(tau * sigma)
    view_precision = P.T @ np.linalg.pinv(omega) @ P
    posterior_cov_inv = prior_precision + view_precision
    posterior = np.linalg.pinv(posterior_cov_inv) @ (prior_precision @ pi + P.T @ np.linalg.pinv(omega) @ Q)
    return {"implied_equilibrium_returns": pi.tolist(), "posterior_returns": posterior.tolist(), "tau": tau, "view_confidence": view_confidence}


def contagion_network(adj: Sequence[Sequence[float]], shock_node: int, shock: float = 1.0, steps: int = 5, damping: float = 0.35) -> dict[str, Any]:
    """Run a bounded linear contagion simulation on a weighted network."""
    A = np.asarray(adj, dtype=float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError("adjacency matrix must be square")
    if not (0 <= shock_node < A.shape[0]):
        raise ValueError("shock_node out of range")
    strength = np.sum(np.abs(A), axis=1)
    norm = np.maximum(strength, 1e-9)
    W = A / norm[:, None]
    x = np.zeros(A.shape[0])
    x[shock_node] = float(shock)
    history = [x.tolist()]
    for _ in range(steps):
        x = (1.0 - damping) * x + damping * (W @ x)
        history.append(x.tolist())
    centrality = np.ones(A.shape[0]) / A.shape[0]
    for _ in range(50):
        centrality = np.abs(A.T @ centrality)
        s = centrality.sum()
        if s <= 1e-12:
            break
        centrality /= s
    return {"shock_paths": history, "eigenvector_centrality_proxy": centrality.tolist(), "peak_systemic_exposure": float(np.max(np.abs(history)))}


def behavioral_score(metrics: Mapping[str, float]) -> dict[str, Any]:
    """Convert observable behavioral summary metrics into bounded indicators."""
    disposition = float(metrics.get("winner_sell_ratio", 0.0)) - float(metrics.get("loser_sell_ratio", 0.0))
    concentration = float(metrics.get("top5_weight", 0.0))
    turnover = float(metrics.get("turnover", 0.0))
    overconfidence_proxy = min(1.0, max(0.0, turnover / 4.0))
    return {
        "disposition_bias_proxy": round(disposition, 4),
        "concentration_risk": round(min(1.0, concentration), 4),
        "overconfidence_proxy": round(overconfidence_proxy, 4),
        "note": "Behavioral indicators are proxies from supplied summary data, not direct psychological measurements.",
    }


def fuzzy_membership(x: float, low: float, high: float) -> float:
    if high <= low:
        raise ValueError("high must exceed low")
    return float(np.clip((x - low) / (high - low), 0.0, 1.0))


def topsis(matrix: Sequence[Sequence[float]], weights: Sequence[float], benefit: Sequence[bool]) -> dict[str, Any]:
    X = np.asarray(matrix, dtype=float)
    w = np.asarray(weights, dtype=float)
    if X.ndim != 2 or X.shape[1] != len(w) or X.shape[1] != len(benefit):
        raise ValueError("matrix dimensions do not match weights/benefit flags")
    norm = np.sqrt((X * X).sum(axis=0))
    R = X / np.maximum(norm, 1e-12)
    V = R * w
    ideal = np.array([V[:, j].max() if benefit[j] else V[:, j].min() for j in range(V.shape[1])])
    anti = np.array([V[:, j].min() if benefit[j] else V[:, j].max() for j in range(V.shape[1])])
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_minus = np.sqrt(((V - anti) ** 2).sum(axis=1))
    score = d_minus / np.maximum(d_plus + d_minus, 1e-12)
    return {"scores": score.tolist(), "ranking": np.argsort(-score).tolist()}


def market_stress_scenario(base: Mapping[str, float], shocks: Mapping[str, float], sensitivities: Mapping[str, float]) -> dict[str, Any]:
    """Aggregate macro/political/climate shocks into a transparent scenario score."""
    contributions = {}
    for key, shock in shocks.items():
        contributions[key] = float(shock) * float(sensitivities.get(key, 1.0))
    total = float(sum(contributions.values()))
    return {
        "base": dict(base),
        "shock_contributions": contributions,
        "aggregate_stress": total,
        "severity": "high" if abs(total) >= 2.0 else "moderate" if abs(total) >= 0.75 else "low",
    }


def analyze_market_snapshot(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Build a single auditable cross-discipline market intelligence package."""
    macro = macro_regime(snapshot["macro"])
    factors = factor_regression(snapshot["asset_returns"], snapshot["factors"]) if snapshot.get("asset_returns") and snapshot.get("factors") else None
    volatility = garch11_forecast(snapshot["asset_returns"], horizon=int(snapshot.get("volatility_horizon", 3))) if snapshot.get("asset_returns") else None
    stress = market_stress_scenario(snapshot.get("base", {}), snapshot.get("shocks", {}), snapshot.get("sensitivities", {}))
    behavior = behavioral_score(snapshot.get("behavior", {}))
    return {
        "engine_version": "1.0.0",
        "macro": macro,
        "factor_model": factors,
        "volatility": volatility,
        "stress": stress,
        "behavior": behavior,
        "frontier": RESEARCH_FRONTIER,
        "disclaimer": "Analytical screening and scenario outputs only; not investment advice and not a live trading signal.",
    }
