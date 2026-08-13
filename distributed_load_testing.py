"""Local distributed-load simulation for QueueCraft.

The module models globally distributed generators and regional service capacity.
It sends no HTTP requests, opens no sockets, and cannot target external systems.
Use it to evaluate routing, capacity, latency, and failure assumptions before an
approved real-world test is designed by the owning organization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import floor
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class LoadGenerator:
    name: str
    max_requests_per_bucket: int
    routing_weight: float = 1.0

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("load generator name must not be empty")
        if self.max_requests_per_bucket < 1:
            raise ValueError(f"generator '{self.name}' max_requests_per_bucket must be positive")
        if self.routing_weight <= 0:
            raise ValueError(f"generator '{self.name}' routing_weight must be positive")


@dataclass(frozen=True)
class TargetRegion:
    name: str
    capacity_per_bucket: int
    service_latency_ms: float = 30.0

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("target region name must not be empty")
        if self.capacity_per_bucket < 1:
            raise ValueError(f"target region '{self.name}' capacity_per_bucket must be positive")
        if self.service_latency_ms < 0:
            raise ValueError(f"target region '{self.name}' service_latency_ms must be non-negative")


@dataclass(frozen=True)
class DistributedLoadPolicy:
    routing_mode: str = "latency_aware"
    saturation_penalty_ms: float = 20.0
    latency_slo_ms: float = 250.0

    def validate(self) -> None:
        if self.routing_mode not in {"latency_aware", "round_robin"}:
            raise ValueError("routing_mode must be 'latency_aware' or 'round_robin'")
        if self.saturation_penalty_ms < 0:
            raise ValueError("saturation_penalty_ms must be non-negative")
        if self.latency_slo_ms < 0:
            raise ValueError("latency_slo_ms must be non-negative")


def _coerce_generators(items: Iterable[LoadGenerator | Mapping[str, Any]]) -> list[LoadGenerator]:
    converted = [item if isinstance(item, LoadGenerator) else LoadGenerator(**item) for item in items]
    if not converted:
        raise ValueError("at least one load generator is required")
    names = [item.name for item in converted]
    if len(names) != len(set(names)):
        raise ValueError("load generator names must be unique")
    for item in converted:
        item.validate()
    return converted


def _coerce_targets(items: Iterable[TargetRegion | Mapping[str, Any]]) -> list[TargetRegion]:
    converted = [item if isinstance(item, TargetRegion) else TargetRegion(**item) for item in items]
    if not converted:
        raise ValueError("at least one target region is required")
    names = [item.name for item in converted]
    if len(names) != len(set(names)):
        raise ValueError("target region names must be unique")
    for item in converted:
        item.validate()
    return converted


def _coerce_policy(item: DistributedLoadPolicy | Mapping[str, Any]) -> DistributedLoadPolicy:
    converted = item if isinstance(item, DistributedLoadPolicy) else DistributedLoadPolicy(**item)
    converted.validate()
    return converted


def _generator_allocation(demand: int, generators: Sequence[LoadGenerator]) -> tuple[dict[str, int], int]:
    """Split demand by generator weight while enforcing agent capacity."""
    assignments = {generator.name: 0 for generator in generators}
    total_weight = sum(generator.routing_weight for generator in generators)
    for generator in generators:
        proposed = floor(demand * generator.routing_weight / total_weight)
        assignments[generator.name] = min(proposed, generator.max_requests_per_bucket)
    remaining = demand - sum(assignments.values())
    ordered = sorted(generators, key=lambda item: (-item.routing_weight, item.name))
    while remaining:
        changed = False
        for generator in ordered:
            spare = generator.max_requests_per_bucket - assignments[generator.name]
            if spare > 0:
                assignments[generator.name] += 1
                remaining -= 1
                changed = True
                if remaining == 0:
                    break
        if not changed:
            break
    generated = sum(assignments.values())
    return assignments, demand - generated


def _ordered_targets(
    source: str,
    healthy_targets: Sequence[TargetRegion],
    network_latency_ms: Mapping[str, Mapping[str, float]],
    policy: DistributedLoadPolicy,
    rotation: int,
) -> list[TargetRegion]:
    if policy.routing_mode == "round_robin":
        base = sorted(healthy_targets, key=lambda item: item.name)
        return base[rotation % len(base):] + base[:rotation % len(base)] if base else []
    return sorted(
        healthy_targets,
        key=lambda target: (
            float(network_latency_ms[source][target.name]) + target.service_latency_ms,
            target.name,
        ),
    )


def _weighted_percentile(samples: Sequence[tuple[float, int]], percentile: float) -> float | None:
    total = sum(count for _, count in samples)
    if total == 0:
        return None
    threshold = total * percentile
    cumulative = 0
    for value, count in sorted(samples, key=lambda item: item[0]):
        cumulative += count
        if cumulative >= threshold:
            return round(value, 3)
    return round(samples[-1][0], 3)


def simulate_distributed_load(
    global_load_buckets: Sequence[int | float],
    load_generators: Iterable[LoadGenerator | Mapping[str, Any]],
    target_regions: Iterable[TargetRegion | Mapping[str, Any]],
    network_latency_ms: Mapping[str, Mapping[str, float]],
    policy: DistributedLoadPolicy | Mapping[str, Any],
    *,
    outages_by_bucket: Mapping[int, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Simulate geographically distributed generated load against regional capacity.

    Each bucket is an explicit model interval, not a real request burst. The
    function has no network side effects. ``outages_by_bucket`` only marks
    target regions unavailable within the simulation.
    """
    loads = list(global_load_buckets)
    if not loads:
        raise ValueError("global_load_buckets must not be empty")
    if any(not isinstance(value, (int, float)) or value < 0 or int(value) != value for value in loads):
        raise ValueError("global_load_buckets must contain non-negative whole request counts")
    generators = _coerce_generators(load_generators)
    targets = _coerce_targets(target_regions)
    current_policy = _coerce_policy(policy)
    target_names = {target.name for target in targets}
    for generator in generators:
        if generator.name not in network_latency_ms:
            raise ValueError(f"network latency is missing for generator '{generator.name}'")
        missing = target_names - set(network_latency_ms[generator.name])
        if missing:
            raise ValueError(f"network latency from '{generator.name}' is missing for targets: {sorted(missing)}")
        if any(float(network_latency_ms[generator.name][target]) < 0 for target in target_names):
            raise ValueError("network latency values must be non-negative")
    normalized_outages = {int(bucket): set(names) for bucket, names in (outages_by_bucket or {}).items()}
    for bucket, outage_names in normalized_outages.items():
        if bucket < 0:
            raise ValueError("outage bucket indices must be non-negative")
        unknown = outage_names - target_names
        if unknown:
            raise ValueError(f"outages reference unknown target regions: {sorted(unknown)}")

    timeline: list[dict[str, Any]] = []
    all_latency_samples: list[tuple[float, int]] = []
    total_requested = total_generated = total_unserved = total_generator_limited = 0

    for bucket, raw_demand in enumerate(loads):
        demand = int(raw_demand)
        generator_assignments, generator_limited = _generator_allocation(demand, generators)
        unhealthy = normalized_outages.get(bucket, set())
        healthy = [target for target in targets if target.name not in unhealthy]
        remaining_capacity = {target.name: target.capacity_per_bucket for target in healthy}
        route_assignments = {
            generator.name: {target.name: 0 for target in healthy}
            for generator in generators
        }
        for sequence, generator in enumerate(generators):
            remaining_for_source = generator_assignments[generator.name]
            for target in _ordered_targets(generator.name, healthy, network_latency_ms, current_policy, bucket + sequence):
                assigned = min(remaining_for_source, remaining_capacity[target.name])
                route_assignments[generator.name][target.name] += assigned
                remaining_capacity[target.name] -= assigned
                remaining_for_source -= assigned
                if remaining_for_source == 0:
                    break

        target_served = {
            target.name: sum(routes[target.name] for routes in route_assignments.values())
            for target in healthy
        }
        target_utilization = {
            target.name: target_served[target.name] / target.capacity_per_bucket for target in healthy
        }
        latency_samples: list[tuple[float, int]] = []
        latency_by_route: dict[str, dict[str, float]] = {}
        latency_compliant = 0
        for generator in generators:
            latency_by_route[generator.name] = {}
            for target in healthy:
                count = route_assignments[generator.name][target.name]
                utilization = target_utilization[target.name]
                queue_penalty = current_policy.saturation_penalty_ms * utilization / max(0.05, 1.0 - utilization)
                latency = float(network_latency_ms[generator.name][target.name]) + target.service_latency_ms + queue_penalty
                latency_by_route[generator.name][target.name] = round(latency, 3)
                if count:
                    latency_samples.append((latency, count))
                    if latency <= current_policy.latency_slo_ms:
                        latency_compliant += count
        served = sum(target_served.values())
        generated = sum(generator_assignments.values())
        unserved = generated - served
        p95_latency = _weighted_percentile(latency_samples, 0.95)
        mean_latency = round(sum(value * count for value, count in latency_samples) / served, 3) if served else None
        all_latency_samples.extend(latency_samples)
        total_requested += demand
        total_generated += generated
        total_generator_limited += generator_limited
        total_unserved += unserved
        timeline.append(
            {
                "bucket": bucket,
                "requested_requests": demand,
                "generator_assignments": generator_assignments,
                "generator_capacity_limited_requests": generator_limited,
                "unhealthy_target_regions": sorted(unhealthy),
                "target_served_requests": target_served,
                "target_utilization": {name: round(value, 4) for name, value in target_utilization.items()},
                "route_assignments": route_assignments,
                "route_latency_ms": latency_by_route,
                "served_requests": served,
                "unserved_requests": unserved,
                "latency_slo_compliant_requests": latency_compliant,
                "mean_estimated_latency_ms": mean_latency,
                "p95_estimated_latency_ms": p95_latency,
            }
        )

    total_latency_compliant = sum(row["latency_slo_compliant_requests"] for row in timeline)
    return {
        "safe_mode": {
            "network_requests_sent": 0,
            "description": "Local discrete-event capacity simulation only; no traffic is sent to any target.",
        },
        "load_generators": [asdict(generator) for generator in generators],
        "target_regions": [asdict(target) for target in targets],
        "policy": asdict(current_policy),
        "summary": {
            "buckets": len(timeline),
            "total_requested_requests": total_requested,
            "total_generated_requests": total_generated,
            "generator_capacity_limited_requests": total_generator_limited,
            "total_served_requests": total_generated - total_unserved,
            "total_unserved_requests": total_unserved,
            "served_pct_of_generated": round(100 * (total_generated - total_unserved) / total_generated, 4) if total_generated else 100.0,
            "latency_slo_compliance_pct": round(100 * total_latency_compliant / total_generated, 4) if total_generated else 100.0,
            "global_p95_estimated_latency_ms": _weighted_percentile(all_latency_samples, 0.95),
            "peak_unserved_requests": max(row["unserved_requests"] for row in timeline),
        },
        "timeline": timeline,
    }
