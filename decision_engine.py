"""QueueCraft v4 decision engine.

Combines simulation, sensitivity, Pareto optimization and constrained AI advice
into a reproducible decision package. Offline-first: no operational change can
be applied by this module.
"""
from __future__ import annotations
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from ai_monte_carlo import run_ai_monte_carlo
from decision_analytics import capacity_pareto_analysis, sensitivity_analysis
from generative_queue_optimizer import create_generative_proposal
from scenario_manager import evaluate_sla


def _fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _risk_summary(simulation: Mapping[str, Any], sla_mean_wait: float | None) -> dict[str, Any]:
    observed = float(simulation["simulation"]["end_to_end_mean_wait"])
    p95 = float(simulation["simulation"].get("end_to_end_p95_wait", observed))
    sla = evaluate_sla(dict(simulation), sla_mean_wait)
    if sla_mean_wait is None:
        indicator = None
        status = "not_configured"
    else:
        gap_ratio = max(observed - sla_mean_wait, 0.0) / max(sla_mean_wait, 1e-9)
        tail_ratio = max(p95 - observed, 0.0) / max(p95, 1e-9)
        indicator = round(min(0.99, gap_ratio + tail_ratio * 0.15), 4)
        status = "elevated" if indicator >= 0.25 else "watch" if indicator >= 0.10 else "low"
    return {
        "status": status,
        "screening_sla_failure_risk": indicator,
        "observed_mean_wait": round(observed, 4),
        "p95_wait": round(p95, 4),
        "sla": sla,
        "disclaimer": "Risk value is a deterministic screening indicator, not a calibrated probability.",
    }


def build_decision_package(
    historical_counts: Sequence[float],
    tiers: Sequence[Mapping[str, Any]],
    *,
    sla_mean_wait: float | None = 5.0,
    cost_per_server: float = 1.0,
    server_range: tuple[int, int] = (1, 6),
    replications: int = 200,
    seed: int | None = 42,
    arrival_multipliers: Sequence[float] = (0.8, 1.0, 1.2),
    service_time_multipliers: Sequence[float] = (0.8, 1.0, 1.2),
    enable_llm: bool = False,
    model: str = "gpt-5-mini",
    constraints: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one benchmark, risk, optimization and advisory package."""
    baseline = run_ai_monte_carlo(historical_counts, tiers, replications=replications, seed=seed)
    pareto = capacity_pareto_analysis(
        historical_counts, tiers, server_range=server_range, cost_per_server=cost_per_server,
        sla_mean_wait=sla_mean_wait, replications=max(30, min(replications, 300)), seed=seed,
    )
    sensitivity = sensitivity_analysis(
        historical_counts, tiers, arrival_multipliers=arrival_multipliers,
        service_time_multipliers=service_time_multipliers,
        replications=max(30, min(replications, 300)), seed=seed,
    )
    recommendation = create_generative_proposal(
        pareto, sensitivity,
        constraints=dict(constraints or {"require_sla_compliance": sla_mean_wait is not None}),
        enable_llm=enable_llm, model=model,
    )
    proposed = pareto["recommendation"]
    benchmark = {
        "baseline": {
            "servers": [int(tier["servers"]) for tier in tiers],
            "mean_wait": float(baseline["simulation"]["end_to_end_mean_wait"]),
            "p95_wait": float(baseline["simulation"]["end_to_end_p95_wait"]),
            "mean_makespan": float(baseline["simulation"]["end_to_end_mean_makespan"]),
        },
        "proposed": {
            "servers": list(proposed["servers"]),
            "server_cost": proposed["server_cost"],
            "mean_wait": proposed["mean_wait"],
            "p95_wait": proposed["p95_wait"],
            "sla_compliant": proposed.get("sla_compliant"),
        },
    }
    benchmark["delta"] = {
        "mean_wait": round(benchmark["proposed"]["mean_wait"] - benchmark["baseline"]["mean_wait"], 4),
        "p95_wait": round(benchmark["proposed"]["p95_wait"] - benchmark["baseline"]["p95_wait"], 4),
        "server_count": sum(benchmark["proposed"]["servers"]) - sum(benchmark["baseline"]["servers"]),
    }
    package = {
        "version": "4.0.0",
        "decision_engine": "offline-first",
        "inputs": {
            "history_points": len(historical_counts), "tier_names": [t["name"] for t in tiers],
            "sla_mean_wait": sla_mean_wait, "cost_per_server": cost_per_server,
            "server_range": list(server_range), "replications": replications, "seed": seed,
        },
        "benchmark": benchmark,
        "risk": _risk_summary(baseline, sla_mean_wait),
        "pareto": pareto,
        "sensitivity": sensitivity,
        "recommendation": recommendation,
        "approval": {"status": "pending", "required": True, "applied": False, "external_operations_performed": False},
    }
    package["package_fingerprint"] = _fingerprint(package)
    return package
