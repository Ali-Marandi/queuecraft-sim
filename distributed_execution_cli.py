"""CLI demo for QueueCraft distributed execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from distributed_execution import CheckpointStore, DistributedExecutor, DistributedPlan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--chunk-size", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--checkpoint", default="artifacts/distributed-checkpoint.json")
    args = parser.parse_args()

    plan = DistributedPlan("CLI-DEMO", args.tasks, args.workers, args.chunk_size, args.seed)
    events = []
    executor = DistributedExecutor(plan, CheckpointStore(Path(args.checkpoint)))
    result = executor.run(lambda task_id, task_seed: {"task_id": task_id, "seed": task_seed}, progress=events.append)
    result["last_progress"] = events[-1] if events else None
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
