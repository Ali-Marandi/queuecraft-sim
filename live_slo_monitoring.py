"""Local live SLO monitoring for the QueueCraft desktop application.

This module stores a bounded in-memory history, accepts explicit local
observations, and returns dashboard snapshots. It does not start a network
listener, open an outbound connection, or export telemetry automatically.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import re
from threading import RLock
from typing import Any, Mapping

from multi_region_failover import SLODefinition, SLOMonitor


_SAFE_LABEL = re.compile(r"^[A-Za-z0-9_.-]{1,48}$")


@dataclass(frozen=True)
class LocalSLOObservation:
    bucket: int
    region: str
    total_requests: int
    successful_requests: int
    latency_compliant_requests: int
    source: str = "approved-adapter"

    def validate(self) -> None:
        if self.bucket < 0:
            raise ValueError("bucket must be non-negative")
        for label_name, value in (("region", self.region), ("source", self.source)):
            if not isinstance(value, str) or not _SAFE_LABEL.fullmatch(value):
                raise ValueError(f"{label_name} must be a low-cardinality label of 1-48 safe characters")
        for field_name, value in (
            ("total_requests", self.total_requests),
            ("successful_requests", self.successful_requests),
            ("latency_compliant_requests", self.latency_compliant_requests),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")
        if self.successful_requests > self.total_requests:
            raise ValueError("successful_requests cannot exceed total_requests")
        if self.latency_compliant_requests > self.total_requests:
            raise ValueError("latency_compliant_requests cannot exceed total_requests")

    @property
    def good_requests(self) -> int:
        """A request must both succeed and satisfy the configured latency SLI."""
        return min(self.successful_requests, self.latency_compliant_requests)


class LiveSLOMonitor:
    """Thread-safe in-memory monitor for the desktop dashboard session."""

    DEMO_SEQUENCE = (
        {"region": "americas-region", "total_requests": 100, "successful_requests": 100, "latency_compliant_requests": 100},
        {"region": "europe-region", "total_requests": 120, "successful_requests": 120, "latency_compliant_requests": 119},
        {"region": "asia-region", "total_requests": 90, "successful_requests": 90, "latency_compliant_requests": 90},
        {"region": "europe-region", "total_requests": 140, "successful_requests": 135, "latency_compliant_requests": 132},
        {"region": "americas-region", "total_requests": 110, "successful_requests": 110, "latency_compliant_requests": 110},
        {"region": "europe-region", "total_requests": 130, "successful_requests": 130, "latency_compliant_requests": 130},
    )

    def __init__(
        self,
        definition: SLODefinition | Mapping[str, Any] | None = None,
        *,
        max_history_points: int = 120,
    ) -> None:
        if not isinstance(max_history_points, int) or max_history_points < 1:
            raise ValueError("max_history_points must be a positive integer")
        self.definition = definition if isinstance(definition, SLODefinition) else SLODefinition(**(definition or {}))
        self.definition.validate()
        self.max_history_points = max_history_points
        self._lock = RLock()
        self._history: deque[dict[str, Any]] = deque(maxlen=max_history_points)
        self._region_totals: dict[str, dict[str, int]] = {}
        self._monitor = SLOMonitor(self.definition)
        self._next_bucket = 0
        self._demo_index = 0

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _coerce(payload: LocalSLOObservation | Mapping[str, Any]) -> LocalSLOObservation:
        if isinstance(payload, LocalSLOObservation):
            observation = payload
        elif isinstance(payload, Mapping):
            observation = LocalSLOObservation(**payload)
        else:
            raise ValueError("observation must be a JSON object")
        observation.validate()
        return observation

    def ingest(self, payload: LocalSLOObservation | Mapping[str, Any]) -> dict[str, Any]:
        """Record one locally supplied observation and return a dashboard snapshot."""
        observation = self._coerce(payload)
        with self._lock:
            if observation.bucket < self._next_bucket:
                raise ValueError("bucket must be monotonic; use the next available local bucket")
            self._next_bucket = observation.bucket + 1
            slo_snapshot = self._monitor.record(
                bucket=observation.bucket,
                total_requests=observation.total_requests,
                good_requests=observation.good_requests,
                latency_compliant_requests=observation.latency_compliant_requests,
            )
            region = self._region_totals.setdefault(
                observation.region,
                {"total_requests": 0, "successful_requests": 0, "latency_compliant_requests": 0, "good_requests": 0},
            )
            region["total_requests"] += observation.total_requests
            region["successful_requests"] += observation.successful_requests
            region["latency_compliant_requests"] += observation.latency_compliant_requests
            region["good_requests"] += observation.good_requests
            self._history.append(
                {
                    "bucket": observation.bucket,
                    "recorded_at_utc": self._utc_now(),
                    "region": observation.region,
                    "source": observation.source,
                    "total_requests": observation.total_requests,
                    "successful_requests": observation.successful_requests,
                    "latency_compliant_requests": observation.latency_compliant_requests,
                    "good_requests": observation.good_requests,
                    "bad_requests": observation.total_requests - observation.good_requests,
                    "slo": slo_snapshot,
                }
            )
            return self.dashboard_snapshot()

    def advance_demo(self) -> dict[str, Any]:
        """Add one fixed illustrative observation. It never accesses external data."""
        with self._lock:
            values = dict(self.DEMO_SEQUENCE[self._demo_index % len(self.DEMO_SEQUENCE)])
            self._demo_index += 1
            values.update({"bucket": self._next_bucket, "source": "local-demo"})
        return self.ingest(values)

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self._history.clear()
            self._region_totals.clear()
            self._monitor = SLOMonitor(self.definition)
            self._next_bucket = 0
            self._demo_index = 0
            return self.dashboard_snapshot()

    def dashboard_snapshot(self, *, history_limit: int | None = None) -> dict[str, Any]:
        with self._lock:
            if history_limit is not None and (not isinstance(history_limit, int) or history_limit < 1):
                raise ValueError("history_limit must be a positive integer")
            history = list(self._history)
            if history_limit is not None:
                history = history[-history_limit:]
            return {
                "mode": "local-in-memory",
                "outbound_telemetry_enabled": False,
                "last_updated_utc": self._utc_now() if history else None,
                "slo": self._monitor.snapshot(),
                "history": history,
                "region_totals": {name: dict(values) for name, values in sorted(self._region_totals.items())},
                "prometheus_text_preview": self.prometheus_text_preview(),
            }

    def prometheus_text_preview(self) -> str:
        """Return a local, bounded Prometheus exposition preview; do not export it."""
        snapshot = self._monitor.snapshot()
        lines = [
            "# HELP queuecraft_slo_availability_ratio Local rolling availability SLI ratio.",
            "# TYPE queuecraft_slo_availability_ratio gauge",
            f"queuecraft_slo_availability_ratio {snapshot['availability_pct'] / 100.0}",
            "# HELP queuecraft_slo_error_budget_remaining_requests Local rolling remaining error budget.",
            "# TYPE queuecraft_slo_error_budget_remaining_requests gauge",
            f"queuecraft_slo_error_budget_remaining_requests {snapshot['remaining_error_budget_requests']}",
            "# HELP queuecraft_slo_burn_rate Local rolling SLO error-budget burn rate.",
            "# TYPE queuecraft_slo_burn_rate gauge",
            f"queuecraft_slo_burn_rate {snapshot['error_budget_burn_rate']}",
            "# HELP queuecraft_observed_requests_total Locally observed dashboard requests by low-cardinality region.",
            "# TYPE queuecraft_observed_requests_total counter",
        ]
        for region, values in sorted(self._region_totals.items()):
            lines.append(f'queuecraft_observed_requests_total{{region="{region}"}} {values["total_requests"]}')
        return "\n".join(lines) + "\n"
