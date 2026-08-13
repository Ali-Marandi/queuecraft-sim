"""QueueCraft Enterprise AI v3.0 — AI-informed Monte Carlo optimization engine.

This module forecasts bucketed arrival demand from historical counts, simulates
single- or multi-tier queues over many stochastic replications, and chooses a
cost-aware staffing plan that satisfies an SLA whenever feasible.

The model is deliberately deterministic when a seed is provided. It uses only
NumPy, so it can be packaged with the desktop application through PyInstaller.
"""

from __future__ import annotations

import argparse
import heapq
import itertools
import json
from dataclasses import dataclass, asdict
from typing import Any, Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class TierConfig:
    """Configuration for one serial processing stage."""

    name: str
    servers: int
    mean_service_time: float
    service_cv: float = 1.0

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "TierConfig":
        return cls(
            name=str(value.get("name", "Unnamed tier")),
            servers=int(value.get("servers", 1)),
            mean_service_time=float(value.get("mean_service_time", 1.0)),
            service_cv=float(value.get("service_cv", 1.0)),
        )


def _validate_history(historical_counts: Sequence[float]) -> np.ndarray:
    values = np.asarray(historical_counts, dtype=float)
    if values.ndim != 1 or values.size < 5:
        raise ValueError("historical_counts must contain at least five bucket counts")
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("historical_counts must contain finite, non-negative values")
    return values


def forecast_arrival_rates(historical_counts: Sequence[float], horizon: int = 5) -> dict[str, Any]:
    """Forecast future arrivals per time bucket using a fitted quadratic trend.

    Residual standard deviation is retained as an uncertainty proxy. Monte Carlo
    replications use this value to introduce forecast-risk variation before
    drawing the actual Poisson arrival counts.
    """
    if horizon < 1:
        raise ValueError("horizon must be at least one")

    history = _validate_history(historical_counts)
    x = np.arange(history.size, dtype=float)
    coefficients = np.polyfit(x, history, deg=2)
    model = np.poly1d(coefficients)
    fitted = np.maximum(model(x), 0.0)
    residual_sigma = float(np.std(history - fitted, ddof=1)) if history.size > 2 else 0.0
    future_x = np.arange(history.size, history.size + horizon, dtype=float)
    predicted = np.maximum(model(future_x), 0.0)

    return {
        "model": "quadratic_trend_with_poisson_arrivals",
        "historical_bucket_count": int(history.size),
        "horizon": horizon,
        "coefficients": [round(float(item), 8) for item in coefficients],
        "forecast_arrivals_per_bucket": [round(float(item), 3) for item in predicted],
        "residual_sigma": round(residual_sigma, 3),
    }


def _sample_service_times(
    jobs: int, mean: float, service_cv: float, rng: np.random.Generator
) -> np.ndarray:
    """Draw positive Gamma-distributed services with configurable coefficient of variation."""
    if jobs == 0:
        return np.empty(0, dtype=float)
    if mean <= 0 or service_cv <= 0:
        raise ValueError("mean_service_time and service_cv must be positive")
    shape = 1.0 / (service_cv**2)
    scale = mean / shape
    return rng.gamma(shape=shape, scale=scale, size=jobs)


def _simulate_tier(
    arrivals: np.ndarray, tier: TierConfig, rng: np.random.Generator
) -> tuple[np.ndarray, dict[str, float]]:
    """Simulate one FCFS multi-server tier and return departure times and metrics."""
    if tier.servers < 1:
        raise ValueError(f"tier '{tier.name}' must have at least one server")
    if arrivals.size == 0:
        return arrivals.copy(), {
            "mean_wait": 0.0,
            "p95_wait": 0.0,
            "max_wait": 0.0,
            "mean_utilization_pct": 0.0,
            "makespan": 0.0,
        }

    ordered_arrivals = np.sort(np.asarray(arrivals, dtype=float))
    available = np.zeros(tier.servers, dtype=float)
    service_times = _sample_service_times(
        len(ordered_arrivals), tier.mean_service_time, tier.service_cv, rng
    )
    waits = np.empty(len(ordered_arrivals), dtype=float)
    departures = np.empty(len(ordered_arrivals), dtype=float)
    busy_time = np.zeros(tier.servers, dtype=float)

    for index, arrival in enumerate(ordered_arrivals):
        server = int(np.argmin(available))
        start = max(float(arrival), float(available[server]))
        end = start + float(service_times[index])
        waits[index] = start - arrival
        departures[index] = end
        available[server] = end
        busy_time[server] += service_times[index]

    makespan = float(np.max(departures))
    utilization = 100.0 * float(np.mean(busy_time / makespan)) if makespan > 0 else 0.0
    return departures, {
        "mean_wait": float(np.mean(waits)),
        "p95_wait": float(np.quantile(waits, 0.95)),
        "max_wait": float(np.max(waits)),
        "mean_utilization_pct": utilization,
        "makespan": makespan,
    }


def _sample_arrivals(
    arrival_rates: np.ndarray,
    bucket_duration: float,
    residual_sigma: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Generate non-homogeneous Poisson arrivals with forecast uncertainty."""
    arrivals: list[float] = []
    for bucket, forecast in enumerate(arrival_rates):
        uncertain_rate = max(0.0, float(forecast) + rng.normal(0.0, residual_sigma))
        count = int(rng.poisson(uncertain_rate))
        if count:
            arrivals.extend((bucket * bucket_duration + rng.uniform(0, bucket_duration, count)).tolist())
    return np.sort(np.asarray(arrivals, dtype=float))


def run_ai_monte_carlo(
    historical_counts: Sequence[float],
    tier_configs: Iterable[TierConfig | dict[str, Any]],
    *,
    horizon: int = 5,
    bucket_duration: float = 1.0,
    replications: int = 500,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Run AI-informed stochastic queue simulation and aggregate risk metrics.

    The forecast determines time-varying expected arrivals. Every replication
    varies both demand and service times. Completion times move forward from one
    tier to the next, so this is a genuine serial, multi-tier Monte Carlo model.
    """
    if replications < 30:
        raise ValueError("replications must be at least 30 for a stable risk estimate")
    if bucket_duration <= 0:
        raise ValueError("bucket_duration must be positive")

    tiers = [config if isinstance(config, TierConfig) else TierConfig.from_mapping(config) for config in tier_configs]
    if not tiers:
        raise ValueError("at least one tier configuration is required")

    forecast = forecast_arrival_rates(historical_counts, horizon=horizon)
    rates = np.asarray(forecast["forecast_arrivals_per_bucket"], dtype=float)
    rng = np.random.default_rng(seed)
    final_waits: list[float] = []
    final_p95_waits: list[float] = []
    final_makespans: list[float] = []
    total_jobs: list[int] = []
    tier_metrics: dict[str, dict[str, list[float]]] = {
        tier.name: {"mean_wait": [], "p95_wait": [], "mean_utilization_pct": []} for tier in tiers
    }

    for _ in range(replications):
        arrivals = _sample_arrivals(rates, bucket_duration, forecast["residual_sigma"], rng)
        total_jobs.append(int(arrivals.size))
        total_wait = 0.0
        total_p95_wait = 0.0
        current_arrivals = arrivals

        for tier in tiers:
            current_arrivals, metrics = _simulate_tier(current_arrivals, tier, rng)
            total_wait += metrics["mean_wait"]
            total_p95_wait += metrics["p95_wait"]
            tier_metrics[tier.name]["mean_wait"].append(metrics["mean_wait"])
            tier_metrics[tier.name]["p95_wait"].append(metrics["p95_wait"])
            tier_metrics[tier.name]["mean_utilization_pct"].append(metrics["mean_utilization_pct"])

        final_waits.append(total_wait)
        final_p95_waits.append(total_p95_wait)
        final_makespans.append(float(np.max(current_arrivals)) if current_arrivals.size else 0.0)

    tier_summary = {}
    for tier in tiers:
        metrics = tier_metrics[tier.name]
        tier_summary[tier.name] = {
            "servers": tier.servers,
            "mean_wait_expected": round(float(np.mean(metrics["mean_wait"])), 3),
            "mean_wait_p95": round(float(np.quantile(metrics["mean_wait"], 0.95)), 3),
            "p95_wait_expected": round(float(np.mean(metrics["p95_wait"])), 3),
            "mean_utilization_pct": round(float(np.mean(metrics["mean_utilization_pct"])), 2),
        }

    sla_wait = np.asarray(final_waits, dtype=float)
    return {
        "forecast": forecast,
        "simulation": {
            "replications": replications,
            "seed": seed,
            "mean_jobs": round(float(np.mean(total_jobs)), 2),
            "p95_jobs": round(float(np.quantile(total_jobs, 0.95)), 2),
            "end_to_end_mean_wait": round(float(np.mean(sla_wait)), 3),
            "end_to_end_p95_wait": round(float(np.quantile(np.asarray(final_p95_waits), 0.95)), 3),
            "end_to_end_mean_makespan": round(float(np.mean(final_makespans)), 3),
            "tiers": tier_summary,
        },
    }


def optimize_staffing(
    historical_counts: Sequence[float],
    base_tiers: Iterable[TierConfig | dict[str, Any]],
    *,
    server_range: tuple[int, int] = (1, 6),
    max_end_to_end_mean_wait: float = 5.0,
    cost_per_server: float = 1.0,
    replications: int = 200,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Select a cost-minimal staffing configuration under a wait-time SLA.

    Every candidate config is evaluated under the same seed. This produces a
    fair comparison: differences arise from staffing decisions rather than a
    different random sample of demand or service time.
    """
    minimum, maximum = server_range
    if minimum < 1 or maximum < minimum:
        raise ValueError("server_range must be a valid positive inclusive range")
    if max_end_to_end_mean_wait < 0 or cost_per_server < 0:
        raise ValueError("SLA and cost parameters must be non-negative")

    tiers = [config if isinstance(config, TierConfig) else TierConfig.from_mapping(config) for config in base_tiers]
    if not tiers:
        raise ValueError("at least one tier configuration is required")

    evaluations = []
    candidate_space = itertools.product(range(minimum, maximum + 1), repeat=len(tiers))
    for servers in candidate_space:
        candidate_tiers = [
            TierConfig(
                name=tier.name,
                servers=servers[index],
                mean_service_time=tier.mean_service_time,
                service_cv=tier.service_cv,
            )
            for index, tier in enumerate(tiers)
        ]
        result = run_ai_monte_carlo(
            historical_counts,
            candidate_tiers,
            replications=replications,
            seed=seed,
        )
        mean_wait = result["simulation"]["end_to_end_mean_wait"]
        server_cost = sum(servers) * cost_per_server
        sla_breach = max(0.0, mean_wait - max_end_to_end_mean_wait)
        # A high finite penalty favors SLA-compliant solutions while retaining a fallback.
        objective = server_cost + (sla_breach * 1_000.0)
        evaluations.append({
            "servers": list(servers),
            "mean_wait": mean_wait,
            "server_cost": round(server_cost, 3),
            "sla_compliant": mean_wait <= max_end_to_end_mean_wait,
            "objective": round(objective, 3),
            "result": result,
        })

    selected = min(evaluations, key=lambda item: (item["objective"], item["server_cost"]))
    return {
        "recommended_tiers": [
            {"name": tier.name, "servers": selected["servers"][index]}
            for index, tier in enumerate(tiers)
        ],
        "objective": selected["objective"],
        "sla_compliant": selected["sla_compliant"],
        "simulation": selected["result"]["simulation"],
        "candidates_evaluated": len(evaluations),
    }


def _load_payload(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"input must be valid JSON: {error.msg}") from error
    if not isinstance(payload, dict):
        raise ValueError("input JSON must be an object")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="AI-informed Monte Carlo queue optimizer")
    parser.add_argument("--input", required=True, help="JSON string or path to a JSON file")
    parser.add_argument("--output", help="Optional JSON output file path")
    args = parser.parse_args()

    try:
        try:
            with open(args.input, "r", encoding="utf-8") as source:
                payload = _load_payload(source.read())
        except OSError:
            payload = _load_payload(args.input)

        mode = payload.get("mode", "simulate")
        if mode == "optimize":
            result = optimize_staffing(
                payload["historical_counts"],
                payload["tiers"],
                server_range=tuple(payload.get("server_range", [1, 6])),
                max_end_to_end_mean_wait=float(payload.get("max_end_to_end_mean_wait", 5.0)),
                cost_per_server=float(payload.get("cost_per_server", 1.0)),
                replications=int(payload.get("replications", 200)),
                seed=payload.get("seed", 42),
            )
        else:
            result = run_ai_monte_carlo(
                payload["historical_counts"],
                payload["tiers"],
                horizon=int(payload.get("horizon", 5)),
                bucket_duration=float(payload.get("bucket_duration", 1.0)),
                replications=int(payload.get("replications", 500)),
                seed=payload.get("seed", 42),
            )
        encoded = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as target:
                target.write(encoded + "\n")
        print(encoded)
    except (KeyError, TypeError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()


@dataclass(frozen=True)
class PriorityQueuePolicy:
    """Operational constraints for an advanced FCFS-with-priority queue.

    Lower numeric priority wins. For example, use priority 0 for emergency,
    priority 1 for premium, and priority 2 for standard requests. Patience is
    the maximum permitted queue waiting time; ``None`` disables abandonment.
    """

    servers: int
    queue_capacity: int | None = None
    default_patience: float | None = None
    sla_wait_target: float | None = None


def simulate_priority_queue(
    jobs: Sequence[dict[str, Any]],
    policy: PriorityQueuePolicy | dict[str, Any],
    *,
    seed: int | None = 42,
) -> dict[str, Any]:
    """Simulate a capacity-limited, non-preemptive priority queue.

    Each job requires ``arrival`` and either ``service_time`` or
    ``mean_service_time``. Optional values are ``priority`` (lower is more
    important), ``patience`` and ``class_name``. A job can end as ``served``,
    ``abandoned`` after its patience expires, or ``rejected`` if the waiting
    queue is full at arrival. Existing services are never interrupted; priority
    applies when selecting the next waiting job.
    """
    active_policy = policy if isinstance(policy, PriorityQueuePolicy) else PriorityQueuePolicy(**policy)
    if active_policy.servers < 1:
        raise ValueError("servers must be at least one")
    if active_policy.queue_capacity is not None and active_policy.queue_capacity < 0:
        raise ValueError("queue_capacity must be zero or a positive integer")
    if active_policy.default_patience is not None and active_policy.default_patience < 0:
        raise ValueError("default_patience cannot be negative")

    normalized_jobs: list[dict[str, Any]] = []
    rng = np.random.default_rng(seed)
    for index, raw_job in enumerate(jobs):
        if not isinstance(raw_job, dict):
            raise ValueError("each job must be an object")
        arrival = float(raw_job.get("arrival", -1))
        if not np.isfinite(arrival) or arrival < 0:
            raise ValueError("job arrival times must be finite and non-negative")
        if "service_time" in raw_job:
            service_time = float(raw_job["service_time"])
        else:
            mean_service_time = float(raw_job.get("mean_service_time", -1))
            service_cv = float(raw_job.get("service_cv", 1.0))
            service_time = float(_sample_service_times(1, mean_service_time, service_cv, rng)[0])
        if not np.isfinite(service_time) or service_time < 0:
            raise ValueError("service_time must be finite and non-negative")
        patience_raw = raw_job.get("patience", active_policy.default_patience)
        patience = None if patience_raw is None else float(patience_raw)
        if patience is not None and (not np.isfinite(patience) or patience < 0):
            raise ValueError("patience must be a non-negative finite number or null")
        normalized_jobs.append(
            {
                "id": str(raw_job.get("id", index + 1)),
                "arrival": arrival,
                "service_time": service_time,
                "priority": int(raw_job.get("priority", 0)),
                "patience": patience,
                "class_name": str(raw_job.get("class_name", "standard")),
                "status": "pending",
                "start": None,
                "end": None,
                "wait": None,
                "server": None,
            }
        )

    # Event fields: (time, event_order, stable_sequence, type, job_index, server_index)
    # Completion is intentionally processed before arrivals at the same time.
    events: list[tuple[float, int, int, str, int, int | None]] = []
    sequence = 0
    for job_index, job in enumerate(normalized_jobs):
        heapq.heappush(events, (job["arrival"], 2, sequence, "arrival", job_index, None))
        sequence += 1

    waiting: list[tuple[int, float, int, int]] = []
    waiting_count = 0
    server_available = [True] * active_policy.servers
    served_waits: list[float] = []

    def start_next_job(time: float, server_index: int) -> None:
        """Start the highest-priority waiting job that has not abandoned."""
        nonlocal waiting_count, sequence
        while waiting:
            _, _, _, next_job_index = heapq.heappop(waiting)
            next_job = normalized_jobs[next_job_index]
            if next_job["status"] != "waiting":
                continue
            waiting_count -= 1
            next_job["status"] = "in_service"
            next_job["server"] = server_index + 1
            next_job["start"] = time
            next_job["wait"] = time - next_job["arrival"]
            next_job["end"] = time + next_job["service_time"]
            server_available[server_index] = False
            heapq.heappush(
                events,
                (next_job["end"], 0, sequence, "complete", next_job_index, server_index),
            )
            sequence += 1
            return
        server_available[server_index] = True

    while events:
        event_time, _, _, event_type, job_index, server_index = heapq.heappop(events)
        job = normalized_jobs[job_index]

        if event_type == "complete":
            if job["status"] != "in_service":
                continue
            job["status"] = "served"
            served_waits.append(float(job["wait"]))
            start_next_job(event_time, int(server_index))
            continue

        if event_type == "abandon":
            if job["status"] == "waiting":
                job["status"] = "abandoned"
                job["end"] = event_time
                job["wait"] = event_time - job["arrival"]
                waiting_count -= 1
            continue

        # Arrival event
        free_server = next((i for i, free in enumerate(server_available) if free), None)
        if free_server is not None:
            job["status"] = "waiting"
            heapq.heappush(waiting, (job["priority"], job["arrival"], job_index, job_index))
            waiting_count += 1
            start_next_job(event_time, free_server)
        elif active_policy.queue_capacity is not None and waiting_count >= active_policy.queue_capacity:
            job["status"] = "rejected"
            job["end"] = event_time
            job["wait"] = 0.0
        else:
            job["status"] = "waiting"
            heapq.heappush(waiting, (job["priority"], job["arrival"], job_index, job_index))
            waiting_count += 1
            if job["patience"] is not None:
                heapq.heappush(
                    events,
                    (event_time + job["patience"], 1, sequence, "abandon", job_index, None),
                )
                sequence += 1

    counts = {status: sum(job["status"] == status for job in normalized_jobs) for status in ("served", "abandoned", "rejected")}
    total = len(normalized_jobs)
    class_summary: dict[str, dict[str, float | int]] = {}
    for class_name in sorted({job["class_name"] for job in normalized_jobs}):
        class_jobs = [job for job in normalized_jobs if job["class_name"] == class_name]
        class_waits = [float(job["wait"]) for job in class_jobs if job["status"] == "served"]
        class_summary[class_name] = {
            "arrivals": len(class_jobs),
            "served": sum(job["status"] == "served" for job in class_jobs),
            "abandoned": sum(job["status"] == "abandoned" for job in class_jobs),
            "rejected": sum(job["status"] == "rejected" for job in class_jobs),
            "mean_wait_served": round(float(np.mean(class_waits)), 3) if class_waits else 0.0,
        }

    mean_wait = float(np.mean(served_waits)) if served_waits else 0.0
    sla_target = active_policy.sla_wait_target
    return {
        "policy": asdict(active_policy),
        "summary": {
            "arrivals": total,
            "served": counts["served"],
            "abandoned": counts["abandoned"],
            "rejected": counts["rejected"],
            "service_level_pct": round(100.0 * counts["served"] / total, 2) if total else 100.0,
            "mean_wait_served": round(mean_wait, 3),
            "p95_wait_served": round(float(np.quantile(served_waits, 0.95)), 3) if served_waits else 0.0,
            "sla_wait_target": sla_target,
            "sla_violations": (
                sum(wait > sla_target for wait in served_waits) if sla_target is not None else None
            ),
        },
        "classes": class_summary,
        "jobs": normalized_jobs,
    }
