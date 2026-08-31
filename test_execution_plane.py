import time
import unittest

from execution_plane import ExecutionPlane, ResourceBudget


class ExecutionPlaneTests(unittest.TestCase):
    def test_priority_order(self):
        plane = ExecutionPlane()
        order = []
        plane.submit("low", lambda: order.append("low"), priority=50)
        plane.submit("high", lambda: order.append("high"), priority=10)
        plane.run_all()
        self.assertEqual(order, ["high", "low"])

    def test_cancel_queued_job(self):
        plane = ExecutionPlane()
        plane.submit("job", lambda: 1)
        job = plane.cancel("job")
        self.assertEqual(job.status, "cancelled")
        self.assertIsNone(plane.run_next())

    def test_cache_hit(self):
        plane = ExecutionPlane()
        calls = []
        plane.submit("first", lambda: calls.append(1) or {"x": 1}, cache_key="k")
        plane.run_next()
        plane.submit("second", lambda: calls.append(2) or {"x": 2}, cache_key="k")
        job = plane.run_next()
        self.assertEqual(job.status, "cached")
        self.assertEqual(job.result, {"x": 1})
        self.assertEqual(calls, [1])

    def test_timeout_budget(self):
        plane = ExecutionPlane(ResourceBudget(max_seconds=0.001))
        plane.submit("slow", lambda: (time.sleep(0.01), "done")[1])
        job = plane.run_next()
        self.assertEqual(job.status, "timeout")

    def test_reproducibility_lock_is_stable(self):
        plane = ExecutionPlane()
        a = plane.lock(dataset_fingerprint="d", scenario_fingerprint="s", model_versions=["m1"], runtime_version="3.20", seed=42)
        b = plane.lock(dataset_fingerprint="d", scenario_fingerprint="s", model_versions=["m1"], runtime_version="3.20", seed=42)
        c = plane.lock(dataset_fingerprint="d", scenario_fingerprint="s", model_versions=["m1"], runtime_version="3.20", seed=43)
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)


if __name__ == "__main__":
    unittest.main()
