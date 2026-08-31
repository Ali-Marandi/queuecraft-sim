# Distributed Execution V1

QueueCraft's distributed execution layer partitions independent simulation tasks into deterministic shards and runs them through a bounded local worker pool.

## Guarantees

- Task identity is the replication index.
- Per-task seed is `plan.seed + task_id`.
- Checkpoints contain the plan fingerprint, completed task ids, and task results.
- A checkpoint from a different plan is rejected.
- Resume never changes completed task results.
- Cancellation stops new task work and returns a partial result set with `cancelled` status.
- Progress callbacks expose started/running/cancelled state and completion ratio.
- No cloud, network, deployment, or infrastructure mutation is performed.

## CLI

```bash
python distributed_execution_cli.py --tasks 100 --workers 4 --chunk-size 10
```

The checkpoint file can be reused for resume.

## Scope boundary

V1 uses threads for bounded local parallelism. It is not a remote cluster scheduler and does not promise CPU isolation, hard memory limits, or process-level fault containment. Those capabilities belong to a future compute service.
