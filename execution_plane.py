"""Governed local execution plane for QueueCraft.

Provides an in-process scheduler with priority ordering, cancellation,
timeout checks, resource budgets and reproducibility locks. It performs no
external deployment or infrastructure mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import heapq
import json
import time
from typing import Any, Callable


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResourceBudget:
    max_seconds: float = 300.0
    max_items: int = 100_000
    max_memory_mb: int = 2048

    def validate(self) -> None:
        if self.max_seconds <= 0 or self.max_items <= 0 or self.max_memory_mb <= 0:
            raise ValueError("resource budgets must be positive")


@dataclass(order=True)
class _QueuedJob:
    priority: int
    sequence: int
    job_id: str = field(compare=False)


@dataclass
class JobRecord:
    job_id: str
    priority: int
    status: str = "queued"
    submitted_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    runtime_seconds: float | None = None
    cache_key: str | None = None
    result: Any = None
    error: str | None = None
    cancelled: bool = False


class ExecutionPlane:
    """Small deterministic scheduler suitable for desktop/offline execution."""

    def __init__(self, budget: ResourceBudget | None = None) -> None:
        self.budget = budget or ResourceBudget()
        self.budget.validate()
        self._queue: list[_QueuedJob] = []
        self._jobs: dict[str, JobRecord] = {}
        self._functions: dict[str, Callable[[], Any]] = {}
        self._seq = 0
        self._cache: dict[str, Any] = {}

    def submit(self, job_id: str, fn: Callable[[], Any], *, priority: int = 100, cache_key: str | None = None) -> JobRecord:
        if not job_id or job_id in self._jobs:
            raise ValueError("job_id must be unique and non-empty")
        self._jobs[job_id] = JobRecord(job_id=job_id, priority=int(priority), cache_key=cache_key)
        self._functions[job_id] = fn
        heapq.heappush(self._queue, _QueuedJob(int(priority), self._seq, job_id))
        self._seq += 1
        return self._jobs[job_id]

    def cancel(self, job_id: str) -> JobRecord:
        job = self._jobs[job_id]
        if job.status != "queued":
            raise ValueError("only queued jobs can be cancelled")
        job.status = "cancelled"
        job.cancelled = True
        return job

    def run_next(self) -> JobRecord | None:
        while self._queue:
            item = heapq.heappop(self._queue)
            job = self._jobs[item.job_id]
            if job.cancelled:
                continue
            if job.cache_key and job.cache_key in self._cache:
                job.status = "cached"
                job.result = self._cache[job.cache_key]
                job.finished_at = time.time()
                job.runtime_seconds = 0.0
                return job
            job.status = "running"
            job.started_at = time.time()
            try:
                result = self._functions[job.job_id]()
                runtime = time.time() - job.started_at
                job.runtime_seconds = runtime
                if runtime > self.budget.max_seconds:
                    job.status = "timeout"
                    job.error = f"runtime exceeded {self.budget.max_seconds}s budget"
                    job.result = None
                else:
                    job.status = "completed"
                    job.result = result
                    if job.cache_key:
                        self._cache[job.cache_key] = result
            except Exception as error:  # noqa: BLE001 - scheduler must record worker failures
                job.status = "failed"
                job.error = str(error)
            finally:
                job.finished_at = time.time()
            return job
        return None

    def run_all(self) -> list[JobRecord]:
        results: list[JobRecord] = []
        while self._queue:
            job = self.run_next()
            if job is not None:
                results.append(job)
        return results

    def lock(self, *, dataset_fingerprint: str, scenario_fingerprint: str, model_versions: list[str], runtime_version: str, seed: int | None) -> str:
        return fingerprint({"dataset": dataset_fingerprint, "scenario": scenario_fingerprint, "models": model_versions, "runtime": runtime_version, "seed": seed})

    def snapshot(self) -> dict[str, Any]:
        return {
            "queued": sum(job.status == "queued" for job in self._jobs.values()),
            "running": sum(job.status == "running" for job in self._jobs.values()),
            "completed": sum(job.status == "completed" for job in self._jobs.values()),
            "cached": sum(job.status == "cached" for job in self._jobs.values()),
            "failed": sum(job.status == "failed" for job in self._jobs.values()),
            "timeouts": sum(job.status == "timeout" for job in self._jobs.values()),
            "cancelled": sum(job.status == "cancelled" for job in self._jobs.values()),
            "cache_entries": len(self._cache),
            "external_side_effects": False,
        }
