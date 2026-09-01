"""Performance and capacity planning helpers for QueueCraft simulation workloads.

These helpers estimate workload size, choose a safe execution mode, and expose
bounded benchmark metadata. They never tune infrastructure or perform network
operations automatically.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from math import ceil
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PerformancePolicy:
    interactive_work_units: int = 10_000
    batch_work_units: int = 500_000
    max_workers: int = 8
    max_in_flight_chunks: int = 32

    def validate(self) -> None:
        if self.interactive_work_units < 1 or self.batch_work_units < self.interactive_work_units:
            raise ValueError("work-unit thresholds are invalid")
        if self.max_workers < 1 or self.max_in_flight_chunks < 1:
            raise ValueError("worker limits must be positive")


def estimate_workload(*, replications: int, horizon: int, stages: int, chunk_size: int = 10) -> dict[str, Any]:
    if min(replications, horizon, stages, chunk_size) < 1:
        raise ValueError("replications, horizon, stages and chunk_size must be positive")
    work_units = replications * horizon * stages
    chunks = ceil(replications / chunk_size)
    return {
        "replications": replications,
        "horizon": horizon,
        "stages": stages,
        "work_units": work_units,
        "chunks": chunks,
        "chunk_size": chunk_size,
    }


def choose_execution_mode(work_units: int, policy: PerformancePolicy | None = None) -> dict[str, Any]:
    p = policy or PerformancePolicy()
    p.validate()
    units = int(work_units)
    if units < 1:
        raise ValueError("work_units must be positive")
    if units <= p.interactive_work_units:
        mode = "interactive"
        workers = 1
    elif units <= p.batch_work_units:
        mode = "batch"
        workers = min(2, p.max_workers)
    else:
        mode = "distributed"
        workers = p.max_workers
    return {"mode": mode, "recommended_workers": workers, "max_workers": p.max_workers, "work_units": units}


def deterministic_replication_seeds(seed: int, replications: int) -> list[int]:
    """Assign a stable seed to each replication independent of worker order."""
    if replications < 1:
        raise ValueError("replications must be positive")
    return [int(seed) + index for index in range(replications)]


def benchmark_envelope(*, workload: Mapping[str, Any], elapsed_seconds: float, completed: int) -> dict[str, Any]:
    if elapsed_seconds < 0 or completed < 0:
        raise ValueError("elapsed_seconds and completed must be non-negative")
    work_units = int(workload.get("work_units", 0))
    throughput = completed / elapsed_seconds if elapsed_seconds > 0 else float(completed > 0)
    return {
        "work_units": work_units,
        "completed": completed,
        "elapsed_seconds": float(elapsed_seconds),
        "replications_per_second": throughput,
        "bounded": True,
        "external_side_effects": False,
    }
