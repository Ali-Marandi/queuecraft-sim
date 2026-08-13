"""Sensitivity and Pareto decision analytics for QueueCraft Enterprise AI.

All candidate plans are evaluated with a common random seed. That keeps the
comparison fair: a difference between plans comes from a capacity or demand
assumption, not a different stochastic draw.
"""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ai_monte_carlo import TierConfig, run_ai_monte_carlo


def _tiers(values: Iterable[TierConfig | dict[str, Any]]) -> list[TierConfig]:
    result = [item if isinstance(item, TierConfig) else TierConfig.from_mapping(item) for item in values]
    if not result:
        raise ValueError("at least one tier configuration is required")
    return result


def is_dominated(candidate: dict[str, Any], comparator: dict[str, Any]) -> bool:
    """Return true when comparator is no worse in cost/wait and better in one."""
    no_worse = (
        comparator["server_cost"] <= candidate["server_cost"]
        and comparator["mean_wait"] <= candidate["mean_wait"]
    )
    strictly_better = (
        comparator["server_cost"] < candidate["server_cost"]
        or comparator["mean_wait"] < candidate["mean_wait"]
    )
    return no_worse and strictly_better


def pareto_frontier(candidates: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return non-dominated plans for the cost-versus-mean-wait trade-off."""
    frontier = [
        candidate
        for candidate in candidates
        if not any(is_dominated(candidate, comparator) for comparator in candidates if comparator is not candidate)
    ]
    return sorted(frontier, key=lambda item: (item["server_cost"], item["mean_wait"]))


def capacity_pareto_analysis(
    historical_counts: Sequence[float],
    base_tiers: Iterable[TierConfig | dict[str, Any]],
    *,
    server_range: tuple[int, int] = (1, 6),
    cost_per_server: float = 1.0,
    sla_mean_wait: float | None = None,
    replications: int = 100,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Evaluate capacity combinations and return cost/wait Pareto alternatives.

    The frontier does not force a single trade-off on the operator. If an SLA is
    supplied, the recommended plan is the least-cost frontier point meeting it;
    otherwise, the knee point closest to the normalized cost/wait ideal is used.
    """
    minimum, maximum = server_range
    if minimum < 1 or maximum < minimum:
        raise ValueError("server_range must be a positive inclusive range")
    if cost_per_server < 0:
        raise ValueError("cost_per_server must be non-negative")
    if sla_mean_wait is not None and sla_mean_wait < 0:
        raise ValueError("sla_mean_wait must be non-negative")

    tiers = _tiers(base_tiers)
    candidates: list[dict[str, Any]] = []
    for allocation in product(range(minimum, maximum + 1), repeat=len(tiers)):
        trial_tiers = [
            TierConfig(
                name=tier.name,
                servers=allocation[index],
                mean_service_time=tier.mean_service_time,
                service_cv=tier.service_cv,
            )
            for index, tier in enumerate(tiers)
        ]
        simulation = run_ai_monte_carlo(
            historical_counts, trial_tiers, replications=replications, seed=seed
        )["simulation"]
        candidates.append(
            {
                "servers": list(allocation),
                "server_cost": round(float(sum(allocation) * cost_per_server), 3),
                "mean_wait": float(simulation["end_to_end_mean_wait"]),
                "p95_wait": float(simulation["end_to_end_p95_wait"]),
                "mean_utilization_pct": round(
                    float(np.mean([tier["mean_utilization_pct"] for tier in simulation["tiers"].values()])), 2
                ),
                "sla_compliant": None if sla_mean_wait is None else simulation["end_to_end_mean_wait"] <= sla_mean_wait,
            }
        )

    frontier = pareto_frontier(candidates)
    compliant = [item for item in frontier if item["sla_compliant"] is True]
    if compliant:
        recommendation = min(compliant, key=lambda item: (item["server_cost"], item["mean_wait"]))
        recommendation_reason = "least_cost_sla_compliant_frontier_plan"
    else:
        costs = np.asarray([item["server_cost"] for item in frontier], dtype=float)
        waits = np.asarray([item["mean_wait"] for item in frontier], dtype=float)
        cost_scale = max(float(costs.max() - costs.min()), 1e-9)
        wait_scale = max(float(waits.max() - waits.min()), 1e-9)
        distances = ((costs - costs.min()) / cost_scale) ** 2 + ((waits - waits.min()) / wait_scale) ** 2
        recommendation = frontier[int(np.argmin(distances))]
        recommendation_reason = "balanced_knee_point_no_sla_feasible" if sla_mean_wait is not None else "balanced_knee_point"

    return {
        "objectives": {
            "minimize": ["server_cost", "end_to_end_mean_wait"],
            "cost_per_server": cost_per_server,
            "sla_mean_wait": sla_mean_wait,
            "common_random_seed": seed,
        },
        "tiers": [tier.name for tier in tiers],
        "candidates_evaluated": len(candidates),
        "candidates": sorted(candidates, key=lambda item: (item["server_cost"], item["mean_wait"])),
        "pareto_frontier": frontier,
        "recommendation": recommendation,
        "recommendation_reason": recommendation_reason,
    }


def sensitivity_analysis(
    historical_counts: Sequence[float],
    base_tiers: Iterable[TierConfig | dict[str, Any]],
    *,
    arrival_multipliers: Sequence[float] = (0.8, 1.0, 1.2),
    service_time_multipliers: Sequence[float] = (0.8, 1.0, 1.2),
    replications: int = 100,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Measure performance sensitivity to demand and service-duration changes."""
    tiers = _tiers(base_tiers)
    history = np.asarray(historical_counts, dtype=float)
    if history.ndim != 1 or history.size < 5 or np.any(history < 0):
        raise ValueError("historical_counts must contain at least five non-negative values")
    if any(value <= 0 for value in (*arrival_multipliers, *service_time_multipliers)):
        raise ValueError("sensitivity multipliers must be positive")

    rows: list[dict[str, Any]] = []
    for demand_factor, service_factor in product(arrival_multipliers, service_time_multipliers):
        scenario_tiers = [
            TierConfig(
                name=tier.name,
                servers=tier.servers,
                mean_service_time=tier.mean_service_time * service_factor,
                service_cv=tier.service_cv,
            )
            for tier in tiers
        ]
        simulation = run_ai_monte_carlo(
            history * demand_factor, scenario_tiers, replications=replications, seed=seed
        )["simulation"]
        rows.append(
            {
                "arrival_multiplier": float(demand_factor),
                "service_time_multiplier": float(service_factor),
                "mean_wait": float(simulation["end_to_end_mean_wait"]),
                "p95_wait": float(simulation["end_to_end_p95_wait"]),
                "mean_jobs": float(simulation["mean_jobs"]),
                "mean_makespan": float(simulation["end_to_end_mean_makespan"]),
            }
        )
    baseline = next(
        (row for row in rows if row["arrival_multiplier"] == 1.0 and row["service_time_multiplier"] == 1.0),
        None,
    )
    return {
        "baseline": baseline,
        "replications": replications,
        "common_random_seed": seed,
        "results": sorted(rows, key=lambda row: (row["arrival_multiplier"], row["service_time_multiplier"])),
    }


def render_pareto_chart(analysis: dict[str, Any], output_path: str | Path) -> str:
    """Render an auditable local PNG of all capacity plans and their frontier."""
    candidates = analysis["candidates"]
    frontier = analysis["pareto_frontier"]
    recommendation = analysis["recommendation"]
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    fig, axis = plt.subplots(figsize=(10, 6), dpi=160)
    axis.scatter(
        [item["server_cost"] for item in candidates],
        [item["mean_wait"] for item in candidates],
        color="#64748b", alpha=0.65, label="Capacity candidates"
    )
    axis.plot(
        [item["server_cost"] for item in frontier],
        [item["mean_wait"] for item in frontier],
        color="#38bdf8", marker="o", linewidth=2.2, label="Pareto frontier"
    )
    axis.scatter(
        [recommendation["server_cost"]], [recommendation["mean_wait"]],
        color="#f59e0b", marker="*", s=240, zorder=5, label="Recommended plan"
    )
    axis.set_title("QueueCraft Capacity Trade-off: Cost vs End-to-End Wait")
    axis.set_xlabel("Server cost")
    axis.set_ylabel("Expected end-to-end mean wait")
    axis.grid(True, color="#cbd5e1", alpha=0.55)
    axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(destination, transparent=False)
    plt.close(fig)
    return str(destination)


def render_sensitivity_chart(analysis: dict[str, Any], output_path: str | Path) -> str:
    """Render a local heatmap for demand/service-time sensitivity."""
    rows = analysis["results"]
    arrivals = sorted({row["arrival_multiplier"] for row in rows})
    services = sorted({row["service_time_multiplier"] for row in rows})
    matrix = np.zeros((len(services), len(arrivals)))
    for row in rows:
        matrix[services.index(row["service_time_multiplier"]), arrivals.index(row["arrival_multiplier"])] = row["mean_wait"]

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig, axis = plt.subplots(figsize=(9, 5), dpi=160)
    image = axis.imshow(matrix, cmap="magma", aspect="auto")
    axis.set_xticks(range(len(arrivals)), [f"{value:.0%}" for value in arrivals])
    axis.set_yticks(range(len(services)), [f"{value:.0%}" for value in services])
    axis.set_xlabel("Arrival-demand multiplier")
    axis.set_ylabel("Service-time multiplier")
    axis.set_title("Sensitivity: Expected End-to-End Mean Wait")
    for row_index in range(matrix.shape[0]):
        for column_index in range(matrix.shape[1]):
            axis.text(column_index, row_index, f"{matrix[row_index, column_index]:.2f}", ha="center", va="center", color="white")
    fig.colorbar(image, ax=axis, label="Mean wait")
    fig.tight_layout()
    fig.savefig(destination, transparent=False)
    plt.close(fig)
    return str(destination)
