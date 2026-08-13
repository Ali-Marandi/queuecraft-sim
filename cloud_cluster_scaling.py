"""Cloud-cluster load distribution and autoscaling simulation for QueueCraft.

This module models a *decision-support simulation*, not an executor for a cloud
provider. It estimates how a routing policy, per-node capacity, warm-up delay,
and scaling thresholds affect backlog, utilization, service level, and cost.
No infrastructure account, credentials, or external resource is changed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Any, Sequence

import numpy as np

from ai_monte_carlo import forecast_arrival_rates


@dataclass(frozen=True)
class ClusterPolicy:
    """Guardrails for a simulated horizontal cluster.

    ``node_capacity`` is the maximum jobs one active worker can complete in a
    simulation bucket. ``target_utilization`` deliberately keeps headroom below
    100% so a predicted peak does not immediately produce a backlog.
    """

    min_nodes: int = 2
    max_nodes: int = 12
    node_capacity: int = 20
    target_utilization: float = 0.70
    scale_up_step: int = 1
    scale_down_step: int = 1
    scale_down_threshold: float = 0.35
    warmup_buckets: int = 1
    cooldown_buckets: int = 1
    per_node_cost_per_bucket: float = 1.0
    backlog_penalty_per_job: float = 0.10
    routing_strategy: str = "least_loaded"

    def validate(self) -> None:
        if self.min_nodes < 1 or self.max_nodes < self.min_nodes:
            raise ValueError("min_nodes and max_nodes must define a valid positive range")
        if self.node_capacity < 1:
            raise ValueError("node_capacity must be at least one job per bucket")
        if not 0 < self.target_utilization <= 1:
            raise ValueError("target_utilization must be in the interval (0, 1]")
        if self.scale_up_step < 1 or self.scale_down_step < 1:
            raise ValueError("scaling step sizes must be positive")
        if not 0 <= self.scale_down_threshold <= 1:
            raise ValueError("scale_down_threshold must be in [0, 1]")
        if self.warmup_buckets < 0 or self.cooldown_buckets < 0:
            raise ValueError("warmup and cooldown must be non-negative")
        if self.per_node_cost_per_bucket < 0 or self.backlog_penalty_per_job < 0:
            raise ValueError("cost parameters must be non-negative")
        if self.routing_strategy not in {"least_loaded", "round_robin"}:
            raise ValueError("routing_strategy must be 'least_loaded' or 'round_robin'")


def _as_policy(policy: ClusterPolicy | dict[str, Any]) -> ClusterPolicy:
    current = policy if isinstance(policy, ClusterPolicy) else ClusterPolicy(**policy)
    current.validate()
    return current


def distribute_load(jobs: int, active_nodes: int, strategy: str, rotation: int = 0) -> list[int]:
    """Return deterministic per-node assignments for a completed bucket load."""
    if jobs < 0 or active_nodes < 1:
        raise ValueError("jobs must be non-negative and active_nodes must be positive")
    base, remainder = divmod(jobs, active_nodes)
    assigned = [base] * active_nodes
    if strategy == "round_robin":
        for offset in range(remainder):
            assigned[(rotation + offset) % active_nodes] += 1
    elif strategy == "least_loaded":
        for index in range(remainder):
            assigned[index] += 1
    else:
        raise ValueError("unsupported routing strategy")
    return assigned


def _desired_nodes(offered_jobs: int, policy: ClusterPolicy) -> int:
    if offered_jobs <= 0:
        return policy.min_nodes
    protected_capacity = policy.node_capacity * policy.target_utilization
    return min(policy.max_nodes, max(policy.min_nodes, ceil(offered_jobs / protected_capacity)))


def simulate_cluster_scaling(
    arrival_buckets: Sequence[int | float],
    policy: ClusterPolicy | dict[str, Any],
    *,
    initial_nodes: int | None = None,
) -> dict[str, Any]:
    """Simulate bucket-level routing, backlog, and horizontal autoscaling.

    A scale-up request takes effect after ``warmup_buckets``. Scale-down happens
    only after a cooldown window, and it never removes pending scale-up capacity.
    The result includes the detailed time series required for audit and charts.
    """
    current_policy = _as_policy(policy)
    arrivals = np.asarray(arrival_buckets, dtype=float)
    if arrivals.ndim != 1 or arrivals.size == 0:
        raise ValueError("arrival_buckets must be a non-empty one-dimensional sequence")
    if not np.all(np.isfinite(arrivals)) or np.any(arrivals < 0):
        raise ValueError("arrival_buckets must contain finite, non-negative values")
    if not np.allclose(arrivals, np.round(arrivals)):
        raise ValueError("arrival_buckets must contain whole job counts")

    active_nodes = initial_nodes if initial_nodes is not None else current_policy.min_nodes
    if not current_policy.min_nodes <= active_nodes <= current_policy.max_nodes:
        raise ValueError("initial_nodes must fall within the policy range")

    pending_activations: list[tuple[int, int]] = []
    backlog = 0
    last_scale_action_bucket = -current_policy.cooldown_buckets
    round_robin_rotation = 0
    timeline: list[dict[str, Any]] = []

    for bucket, raw_arrivals in enumerate(arrivals.astype(int).tolist()):
        activated = sum(count for activation_bucket, count in pending_activations if activation_bucket <= bucket)
        if activated:
            active_nodes = min(current_policy.max_nodes, active_nodes + activated)
            pending_activations = [item for item in pending_activations if item[0] > bucket]

        pending_nodes = sum(count for _, count in pending_activations)
        serving_nodes = active_nodes
        offered_jobs = backlog + raw_arrivals
        capacity = serving_nodes * current_policy.node_capacity
        completed_jobs = min(offered_jobs, capacity)
        backlog = offered_jobs - completed_jobs
        offered_utilization = offered_jobs / capacity if capacity else 0.0
        served_utilization = completed_jobs / capacity if capacity else 0.0
        distribution = distribute_load(
            completed_jobs, serving_nodes, current_policy.routing_strategy, round_robin_rotation
        )
        round_robin_rotation = (round_robin_rotation + completed_jobs) % serving_nodes
        backlog_delay = backlog / capacity if capacity else float("inf")

        action = "hold"
        desired = _desired_nodes(offered_jobs, current_policy)
        cooldown_ready = bucket - last_scale_action_bucket >= current_policy.cooldown_buckets
        effective_nodes = active_nodes + pending_nodes
        if desired > effective_nodes and cooldown_ready:
            increment = min(current_policy.scale_up_step, desired - effective_nodes, current_policy.max_nodes - effective_nodes)
            if increment > 0:
                pending_activations.append((bucket + current_policy.warmup_buckets, increment))
                last_scale_action_bucket = bucket
                action = f"scale_up_requested:+{increment}"
        elif (
            desired < active_nodes
            and served_utilization <= current_policy.scale_down_threshold
            and cooldown_ready
            and not pending_activations
        ):
            decrement = min(current_policy.scale_down_step, active_nodes - desired, active_nodes - current_policy.min_nodes)
            if decrement > 0:
                active_nodes -= decrement
                last_scale_action_bucket = bucket
                action = f"scale_down_applied:-{decrement}"

        node_cost = serving_nodes * current_policy.per_node_cost_per_bucket
        backlog_penalty = backlog * current_policy.backlog_penalty_per_job
        timeline.append(
            {
                "bucket": bucket,
                "arrivals": raw_arrivals,
                "offered_jobs": offered_jobs,
                "completed_jobs": completed_jobs,
                "backlog": backlog,
                "active_nodes": serving_nodes,
                "next_bucket_active_nodes": active_nodes,
                "pending_nodes": sum(count for _, count in pending_activations),
                "capacity": capacity,
                "offered_utilization_pct": round(100.0 * offered_utilization, 2),
                "served_utilization_pct": round(100.0 * served_utilization, 2),
                "estimated_backlog_delay_buckets": round(backlog_delay, 3),
                "node_assignments": distribution,
                "max_node_jobs": max(distribution) if distribution else 0,
                "min_node_jobs": min(distribution) if distribution else 0,
                "action": action,
                "node_cost": round(node_cost, 3),
                "backlog_penalty": round(backlog_penalty, 3),
                "total_operating_cost": round(node_cost + backlog_penalty, 3),
            }
        )

    summary = {
        "buckets": len(timeline),
        "total_arrivals": int(sum(item["arrivals"] for item in timeline)),
        "total_completed": int(sum(item["completed_jobs"] for item in timeline)),
        "ending_backlog": int(timeline[-1]["backlog"]),
        "peak_backlog": int(max(item["backlog"] for item in timeline)),
        "peak_active_nodes": int(max(item["active_nodes"] for item in timeline)),
        "mean_active_nodes": round(float(np.mean([item["active_nodes"] for item in timeline])), 2),
        "mean_offered_utilization_pct": round(float(np.mean([item["offered_utilization_pct"] for item in timeline])), 2),
        "mean_served_utilization_pct": round(float(np.mean([item["served_utilization_pct"] for item in timeline])), 2),
        "estimated_p95_backlog_delay_buckets": round(float(np.quantile([item["estimated_backlog_delay_buckets"] for item in timeline], 0.95)), 3),
        "total_node_cost": round(float(sum(item["node_cost"] for item in timeline)), 3),
        "total_backlog_penalty": round(float(sum(item["backlog_penalty"] for item in timeline)), 3),
        "total_operating_cost": round(float(sum(item["total_operating_cost"] for item in timeline)), 3),
        "scaling_actions": [item["action"] for item in timeline if item["action"] != "hold"],
    }
    return {"policy": asdict(current_policy), "summary": summary, "timeline": timeline}


def forecast_cluster_scaling(
    historical_counts: Sequence[int | float],
    policy: ClusterPolicy | dict[str, Any],
    *,
    horizon: int = 5,
) -> dict[str, Any]:
    """Convert a QueueCraft demand forecast into a pre-scaling capacity plan."""
    current_policy = _as_policy(policy)
    forecast = forecast_arrival_rates(historical_counts, horizon=horizon)
    plan = []
    for bucket, expected_arrivals in enumerate(forecast["forecast_arrivals_per_bucket"]):
        jobs = int(ceil(expected_arrivals))
        plan.append(
            {
                "bucket": bucket,
                "forecast_arrivals": expected_arrivals,
                "recommended_nodes": _desired_nodes(jobs, current_policy),
                "protected_capacity": int(
                    _desired_nodes(jobs, current_policy) * current_policy.node_capacity
                ),
            }
        )
    return {"forecast": forecast, "policy": asdict(current_policy), "pre_scaling_plan": plan}
