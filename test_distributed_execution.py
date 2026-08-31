import tempfile
import time
import unittest
from pathlib import Path

from distributed_execution import CheckpointStore, DistributedExecutor, DistributedPlan


class DistributedExecutionTests(unittest.TestCase):
    def test_deterministic_parallel_results_and_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = DistributedPlan(run_id="r1", total_tasks=8, worker_count=2, chunk_size=2, seed=100)
            events = []
            executor = DistributedExecutor(plan, CheckpointStore(Path(tmp) / "cp.json"))
            result = executor.run(lambda task_id, seed: task_id + seed, progress=events.append)
            expected = {i: i + 100 + i for i in range(8)}
            self.assertEqual(result["status"], "completed")
            self.assertEqual(result["results"], expected)
            self.assertEqual(events[-1]["progress"], 1.0)

    def test_resume_uses_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cp.json"
            plan = DistributedPlan(run_id="r2", total_tasks=4, worker_count=1, chunk_size=1, seed=7)
            store = CheckpointStore(path)
            original = DistributedExecutor(plan, store)
            original.cancel()
            partial = original.run(lambda task_id, seed: task_id + seed)
            self.assertEqual(partial["status"], "cancelled")
            resumed = DistributedExecutor(plan, store).run(lambda task_id, seed: task_id + seed)
            self.assertEqual(resumed["status"], "completed")
            self.assertEqual(resumed["completed"], 4)

    def test_checkpoint_plan_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(Path(tmp) / "cp.json")
            plan = DistributedPlan(run_id="a", total_tasks=2)
            DistributedExecutor(plan, store).run(lambda task_id, seed: seed)
            mismatched = DistributedPlan(run_id="b", total_tasks=2)
            with self.assertRaises(ValueError):
                DistributedExecutor(mismatched, store).run(lambda task_id, seed: seed)

    def test_cancel_does_not_report_completed(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = DistributedPlan(run_id="r3", total_tasks=6, worker_count=1, chunk_size=1)
            executor = DistributedExecutor(plan)
            def slow(task_id, seed):
                if task_id == 0:
                    executor.cancel()
                time.sleep(0.002)
                return seed
            result = executor.run(slow)
            self.assertEqual(result["status"], "cancelled")
            self.assertLess(result["completed"], result["total"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
