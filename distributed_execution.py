"""Deterministic parallel execution primitives for QueueCraft Monte Carlo workloads.

This module partitions independent replication indices into reproducible shards,
executes them through a bounded local worker pool, emits progress snapshots, and
supports checkpoint/resume without external infrastructure side effects.
"""
from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Callable, Iterable, Mapping


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DistributedPlan:
    run_id: str
    total_tasks: int
    worker_count: int = 2
    chunk_size: int = 10
    seed: int = 42

    def validate(self) -> None:
        if not self.run_id or self.total_tasks < 1 or self.worker_count < 1 or self.chunk_size < 1:
            raise ValueError("run_id, task count, worker count and chunk size must be positive")


@dataclass(frozen=True)
class Checkpoint:
    run_id: str
    plan_fingerprint: str
    completed_tasks: tuple[int, ...]
    results: tuple[tuple[int, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CheckpointStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def save(self, checkpoint: Checkpoint) -> None:
        payload = checkpoint.to_dict()
        with self._lock:
            self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def load(self) -> Checkpoint | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return Checkpoint(
            run_id=str(payload["run_id"]),
            plan_fingerprint=str(payload["plan_fingerprint"]),
            completed_tasks=tuple(int(item) for item in payload.get("completed_tasks", [])),
            results=tuple((int(item[0]), item[1]) for item in payload.get("results", [])),
        )


class DistributedExecutor:
    """Bounded local executor with deterministic task identity and resumability."""

    def __init__(self, plan: DistributedPlan, checkpoint_store: CheckpointStore | None = None) -> None:
        plan.validate()
        self.plan = plan
        self.store = checkpoint_store
        self.plan_fingerprint = fingerprint(asdict(plan))
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def _shards(self, task_ids: Iterable[int]) -> list[list[int]]:
        tasks = list(task_ids)
        return [tasks[index:index + self.plan.chunk_size] for index in range(0, len(tasks), self.plan.chunk_size)]

    def run(
        self,
        worker: Callable[[int, int], Any],
        *,
        progress: Callable[[dict[str, Any]], None] | None = None,
        resume: bool = True,
    ) -> dict[str, Any]:
        task_ids = list(range(self.plan.total_tasks))
        completed: set[int] = set()
        results: dict[int, Any] = {}
        if resume and self.store:
            checkpoint = self.store.load()
            if checkpoint:
                if checkpoint.run_id != self.plan.run_id or checkpoint.plan_fingerprint != self.plan_fingerprint:
                    raise ValueError("checkpoint does not match execution plan")
                completed.update(checkpoint.completed_tasks)
                results.update(dict(checkpoint.results))

        pending = [task_id for task_id in task_ids if task_id not in completed]
        total = len(task_ids)
        if progress:
            progress({"status": "started", "completed": len(completed), "total": total, "progress": len(completed) / total})
        if not pending:
            return {"status": "completed", "run_id": self.plan.run_id, "completed": total, "total": total, "results": results, "resumed": True}

        shards = self._shards(pending)

        def run_shard(shard: list[int]) -> list[tuple[int, Any]]:
            if self._cancel.is_set():
                return []
            output: list[tuple[int, Any]] = []
            for task_id in shard:
                if self._cancel.is_set():
                    break
                seed = self.plan.seed + task_id
                output.append((task_id, worker(task_id, seed)))
            return output

        with ThreadPoolExecutor(max_workers=self.plan.worker_count) as executor:
            futures: list[Future[list[tuple[int, Any]]]] = [executor.submit(run_shard, shard) for shard in shards]
            for future in as_completed(futures):
                for task_id, value in future.result():
                    results[task_id] = value
                    completed.add(task_id)
                if self.store:
                    checkpoint = Checkpoint(self.plan.run_id, self.plan_fingerprint, tuple(sorted(completed)), tuple(sorted(results.items())))
                    self.store.save(checkpoint)
                if progress:
                    progress({"status": "cancelled" if self._cancel.is_set() else "running", "completed": len(completed), "total": total, "progress": len(completed) / total})
                if self._cancel.is_set():
                    break

        status = "cancelled" if self._cancel.is_set() and len(completed) < total else "completed"
        return {"status": status, "run_id": self.plan.run_id, "completed": len(completed), "total": total, "results": results, "resumed": bool(self.store and self.store.load())}
