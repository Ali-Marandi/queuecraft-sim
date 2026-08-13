"""QueueCraft Enterprise — repeatable multi-tier stress-test scenarios.

Run: python stress_test_scenarios.py
The test suite intentionally uses deterministic seeds. It exercises capacity
saturation, serial bottlenecks, and staffing optimization under high demand.
"""

from __future__ import annotations

import json

from ai_monte_carlo import optimize_staffing, run_ai_monte_carlo


BASE_TIERS = [
    {"name": "Intake", "servers": 2, "mean_service_time": 0.35, "service_cv": 0.7},
    {"name": "Processing", "servers": 2, "mean_service_time": 0.85, "service_cv": 1.1},
    {"name": "Release", "servers": 1, "mean_service_time": 0.25, "service_cv": 0.6},
]


def summarize(name: str, result: dict) -> dict:
    simulation = result["simulation"]
    return {
        "scenario": name,
        "replications": simulation["replications"],
        "mean_jobs": simulation["mean_jobs"],
        "mean_end_to_end_wait": simulation["end_to_end_mean_wait"],
        "p95_end_to_end_wait": simulation["end_to_end_p95_wait"],
        "mean_makespan": simulation["end_to_end_mean_makespan"],
    }


def run_all() -> list[dict]:
    # 1. Sudden spike: baseline rises abruptly to a sustained peak.
    traffic_burst_history = [8, 10, 11, 13, 15, 50, 70, 85, 95, 85, 60, 35]
    burst = run_ai_monte_carlo(
        traffic_burst_history, BASE_TIERS, horizon=5, replications=500, seed=1001
    )

    # 2. Serial bottleneck: fast intake releases work into a deliberately slow tier.
    bottleneck_tiers = [
        {"name": "Intake", "servers": 5, "mean_service_time": 0.2, "service_cv": 0.5},
        {"name": "Specialist Review", "servers": 1, "mean_service_time": 1.4, "service_cv": 1.3},
        {"name": "Release", "servers": 3, "mean_service_time": 0.2, "service_cv": 0.5},
    ]
    mismatch = run_ai_monte_carlo(
        [18, 20, 22, 25, 29, 34, 38, 42, 47, 52],
        bottleneck_tiers,
        horizon=5,
        replications=500,
        seed=1002,
    )

    # 3. Auto-scaling: choose lowest-cost staffing satisfying a mean-wait SLA.
    auto_scaling = optimize_staffing(
        traffic_burst_history,
        BASE_TIERS,
        server_range=(1, 4),
        max_end_to_end_mean_wait=5.0,
        cost_per_server=1.0,
        replications=200,
        seed=1003,
    )

    output = [summarize("traffic_burst", burst), summarize("serial_bottleneck", mismatch)]
    output.append(
        {
            "scenario": "cost_aware_auto_scaling",
            "candidates_evaluated": auto_scaling["candidates_evaluated"],
            "sla_compliant": auto_scaling["sla_compliant"],
            "recommended_tiers": auto_scaling["recommended_tiers"],
            "projected_mean_wait": auto_scaling["simulation"]["end_to_end_mean_wait"],
        }
    )
    return output


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2))
