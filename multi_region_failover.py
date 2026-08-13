"""Multi-region failover and SLO error-budget simulation for QueueCraft.

This is a local decision-support simulator. It deliberately has no cloud SDK,
network call, credential handling, or provider-side mutation capability.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from math import floor
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RegionConfig:
    name: str
    capacity_per_bucket: int
    routing_weight: float = 1.0
    base_latency_ms: float = 50.0

    def validate(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("region name must not be empty")
        if self.capacity_per_bucket < 1:
            raise ValueError(f"region '{self.name}' capacity_per_bucket must be positive")
        if self.routing_weight <= 0:
            raise ValueError(f"region '{self.name}' routing_weight must be positive")
        if self.base_latency_ms < 0:
            raise ValueError(f"region '{self.name}' base_latency_ms must be non-negative")


@dataclass(frozen=True)
class FailoverPolicy:
    mode: str = "active_active"
    primary_region: str | None = None
    failover_latency_penalty_ms: float = 25.0

    def validate(self, regions: Sequence[RegionConfig]) -> None:
        if self.mode not in {"active_active", "active_passive"}:
            raise ValueError("mode must be 'active_active' or 'active_passive'")
        if self.failover_latency_penalty_ms < 0:
            raise ValueError("failover_latency_penalty_ms must be non-negative")
        names = {region.name for region in regions}
        if self.primary_region is not None and self.primary_region not in names:
            raise ValueError("primary_region must name one of the configured regions")
        if self.mode == "active_passive" and self.primary_region is None:
            raise ValueError("active_passive mode requires primary_region")


@dataclass(frozen=True)
class SLODefinition:
    availability_target: float = 0.999
    latency_threshold_ms: float = 250.0
    rolling_window_buckets: int = 30
    warning_budget_remaining_ratio: float = 0.25
    critical_budget_remaining_ratio: float = 0.0

    def validate(self) -> None:
        if not 0 < self.availability_target < 1:
            raise ValueError("availability_target must be in the interval (0, 1)")
        if self.latency_threshold_ms < 0:
            raise ValueError("latency_threshold_ms must be non-negative")
        if self.rolling_window_buckets < 1:
            raise ValueError("rolling_window_buckets must be positive")
        if not 0 <= self.critical_budget_remaining_ratio <= self.warning_budget_remaining_ratio <= 1:
            raise ValueError("budget alert thresholds must satisfy 0 <= critical <= warning <= 1")


class SLOMonitor:
    """In-memory rolling SLO monitor suitable for a desktop simulation session.

    A production telemetry adapter can call ``record`` once per aggregation
    interval and forward ``snapshot`` to an approved observability system.
    """

    def __init__(self, definition: SLODefinition | Mapping[str, Any]) -> None:
        self.definition = definition if isinstance(definition, SLODefinition) else SLODefinition(**definition)
        self.definition.validate()
        self._observations: deque[dict[str, int | float]] = deque(maxlen=self.definition.rolling_window_buckets)

    def record(
        self,
        *,
        bucket: int,
        total_requests: int,
        good_requests: int,
        latency_compliant_requests: int | None = None,
    ) -> dict[str, Any]:
        if bucket < 0 or total_requests < 0 or good_requests < 0:
            raise ValueError("bucket, total_requests, and good_requests must be non-negative")
        if good_requests > total_requests:
            raise ValueError("good_requests cannot exceed total_requests")
        if latency_compliant_requests is not None and not 0 <= latency_compliant_requests <= total_requests:
            raise ValueError("latency_compliant_requests must be between zero and total_requests")
        self._observations.append(
            {
                "bucket": bucket,
                "total_requests": total_requests,
                "good_requests": good_requests,
                "latency_compliant_requests": latency_compliant_requests if latency_compliant_requests is not None else good_requests,
            }
        )
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        total = sum(int(item["total_requests"]) for item in self._observations)
        good = sum(int(item["good_requests"]) for item in self._observations)
        latency_good = sum(int(item["latency_compliant_requests"]) for item in self._observations)
        bad = total - good
        allowed_bad = total * (1.0 - self.definition.availability_target)
        remaining = allowed_bad - bad
        availability = good / total if total else 1.0
        latency_compliance = latency_good / total if total else 1.0
        burn_rate = (bad / total) / (1.0 - self.definition.availability_target) if total else 0.0
        remaining_ratio = remaining / allowed_bad if allowed_bad > 0 else 1.0
        if remaining_ratio <= self.definition.critical_budget_remaining_ratio:
            alert = "critical"
        elif remaining_ratio <= self.definition.warning_budget_remaining_ratio:
            alert = "warning"
        else:
            alert = "healthy"
        return {
            "definition": asdict(self.definition),
            "window_observations": len(self._observations),
            "total_requests": total,
            "good_requests": good,
            "bad_requests": bad,
            "availability_pct": round(100.0 * availability, 4),
            "latency_compliance_pct": round(100.0 * latency_compliance, 4),
            "allowed_bad_requests": round(allowed_bad, 4),
            "remaining_error_budget_requests": round(remaining, 4),
            "remaining_error_budget_ratio": round(remaining_ratio, 4),
            "error_budget_burn_rate": round(burn_rate, 4),
            "alert_level": alert,
        }


def _coerce_regions(regions: Iterable[RegionConfig | Mapping[str, Any]]) -> list[RegionConfig]:
    converted = [region if isinstance(region, RegionConfig) else RegionConfig(**region) for region in regions]
    if not converted:
        raise ValueError("at least one region is required")
    names = [region.name for region in converted]
    if len(names) != len(set(names)):
        raise ValueError("region names must be unique")
    for region in converted:
        region.validate()
    return converted


def _coerce_policy(policy: FailoverPolicy | Mapping[str, Any], regions: Sequence[RegionConfig]) -> FailoverPolicy:
    converted = policy if isinstance(policy, FailoverPolicy) else FailoverPolicy(**policy)
    converted.validate(regions)
    return converted


def _coerce_slo(definition: SLODefinition | Mapping[str, Any]) -> SLODefinition:
    converted = definition if isinstance(definition, SLODefinition) else SLODefinition(**definition)
    converted.validate()
    return converted


def _allocate_active_active(demand: int, healthy: Sequence[RegionConfig]) -> dict[str, int]:
    """Allocate demand by weight and rebalance overflow to spare capacity."""
    assignments = {region.name: 0 for region in healthy}
    if demand == 0 or not healthy:
        return assignments
    total_weight = sum(region.routing_weight for region in healthy)
    for region in healthy:
        proposed = floor(demand * region.routing_weight / total_weight)
        assignments[region.name] = min(proposed, region.capacity_per_bucket)
    remaining = demand - sum(assignments.values())
    ordered = sorted(healthy, key=lambda item: (-item.routing_weight, item.name))
    while remaining > 0:
        changed = False
        for region in ordered:
            spare = region.capacity_per_bucket - assignments[region.name]
            if spare > 0:
                assignments[region.name] += 1
                remaining -= 1
                changed = True
                if remaining == 0:
                    break
        if not changed:
            break
    return assignments


def _allocate_active_passive(demand: int, healthy: Sequence[RegionConfig], primary_region: str) -> dict[str, int]:
    ordered = sorted(healthy, key=lambda item: (item.name != primary_region, -item.routing_weight, item.name))
    assignments = {region.name: 0 for region in healthy}
    remaining = demand
    for region in ordered:
        assigned = min(remaining, region.capacity_per_bucket)
        assignments[region.name] = assigned
        remaining -= assigned
        if remaining == 0:
            break
    return assignments


def simulate_multi_region_failover(
    arrival_buckets: Sequence[int | float],
    regions: Iterable[RegionConfig | Mapping[str, Any]],
    policy: FailoverPolicy | Mapping[str, Any],
    slo_definition: SLODefinition | Mapping[str, Any],
    *,
    outages_by_bucket: Mapping[int, Iterable[str]] | None = None,
) -> dict[str, Any]:
    """Simulate multi-region routing, outages, failover, and rolling SLO health.

    ``outages_by_bucket`` maps a zero-based bucket index to region names that
    are unavailable for the whole bucket. Outages exist only inside this model.
    """
    configured_regions = _coerce_regions(regions)
    current_policy = _coerce_policy(policy, configured_regions)
    current_slo = _coerce_slo(slo_definition)
    arrivals = list(arrival_buckets)
    if not arrivals:
        raise ValueError("arrival_buckets must not be empty")
    if any(not isinstance(value, (int, float)) or value < 0 or int(value) != value for value in arrivals):
        raise ValueError("arrival_buckets must contain non-negative whole request counts")
    known_names = {region.name for region in configured_regions}
    normalized_outages = {int(bucket): set(names) for bucket, names in (outages_by_bucket or {}).items()}
    for bucket, names in normalized_outages.items():
        if bucket < 0:
            raise ValueError("outage bucket indices must be non-negative")
        unknown = names - known_names
        if unknown:
            raise ValueError(f"outages reference unknown regions: {sorted(unknown)}")

    monitor = SLOMonitor(current_slo)
    timeline: list[dict[str, Any]] = []
    primary = current_policy.primary_region or configured_regions[0].name

    for bucket, demand_value in enumerate(arrivals):
        demand = int(demand_value)
        unhealthy = normalized_outages.get(bucket, set())
        healthy = [region for region in configured_regions if region.name not in unhealthy]
        if current_policy.mode == "active_active":
            assignments = _allocate_active_active(demand, healthy)
        else:
            assignments = _allocate_active_passive(demand, healthy, primary)
        served = sum(assignments.values())
        unserved = demand - served
        outage_present = bool(unhealthy)
        route_latencies: dict[str, float] = {}
        latency_compliant = 0
        failover_jobs = 0
        for region in healthy:
            jobs = assignments.get(region.name, 0)
            is_failover_route = current_policy.mode == "active_passive" and region.name != primary and jobs > 0
            if current_policy.mode == "active_active" and outage_present and jobs > 0:
                is_failover_route = True
            latency = region.base_latency_ms + (current_policy.failover_latency_penalty_ms if is_failover_route else 0.0)
            route_latencies[region.name] = round(latency, 3)
            if latency <= current_slo.latency_threshold_ms:
                latency_compliant += jobs
            if is_failover_route:
                failover_jobs += jobs
        weighted_latency = (
            sum(assignments[name] * route_latencies[name] for name in assignments) / served if served else None
        )
        good_requests = latency_compliant
        slo_snapshot = monitor.record(
            bucket=bucket,
            total_requests=demand,
            good_requests=good_requests,
            latency_compliant_requests=latency_compliant,
        )
        event = "normal"
        if not healthy:
            event = "global_outage"
        elif unhealthy and failover_jobs:
            event = "failover_routed"
        elif unhealthy:
            event = "degraded_capacity"
        elif unserved:
            event = "capacity_exhausted"
        timeline.append(
            {
                "bucket": bucket,
                "arrivals": demand,
                "healthy_regions": [region.name for region in healthy],
                "unhealthy_regions": sorted(unhealthy),
                "region_assignments": assignments,
                "region_latency_ms": route_latencies,
                "served_requests": served,
                "unserved_requests": unserved,
                "failover_jobs": failover_jobs,
                "estimated_weighted_latency_ms": round(weighted_latency, 3) if weighted_latency is not None else None,
                "event": event,
                "slo": slo_snapshot,
            }
        )

    total_arrivals = sum(item["arrivals"] for item in timeline)
    total_served = sum(item["served_requests"] for item in timeline)
    total_unserved = sum(item["unserved_requests"] for item in timeline)
    failover_events = [item for item in timeline if item["event"] in {"failover_routed", "degraded_capacity", "global_outage"}]
    latencies = [item["estimated_weighted_latency_ms"] for item in timeline if item["estimated_weighted_latency_ms"] is not None]
    return {
        "regions": [asdict(region) for region in configured_regions],
        "policy": asdict(current_policy),
        "slo_definition": asdict(current_slo),
        "summary": {
            "buckets": len(timeline),
            "total_arrivals": total_arrivals,
            "total_served": total_served,
            "total_unserved": total_unserved,
            "served_pct": round(100.0 * total_served / total_arrivals, 4) if total_arrivals else 100.0,
            "failover_event_count": len(failover_events),
            "peak_unserved_requests": max(item["unserved_requests"] for item in timeline),
            "mean_estimated_latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else None,
            "final_slo": monitor.snapshot(),
        },
        "timeline": timeline,
    }
