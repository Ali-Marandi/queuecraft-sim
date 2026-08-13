"""Regression tests for QueueCraft's advanced priority queue model."""

import unittest

from ai_monte_carlo import PriorityQueuePolicy, simulate_priority_queue


class PriorityQueueTests(unittest.TestCase):
    def test_higher_priority_waiting_job_starts_first(self):
        result = simulate_priority_queue(
            [
                {"id": "active", "arrival": 0.0, "service_time": 3.0, "priority": 2},
                {"id": "standard", "arrival": 0.1, "service_time": 1.0, "priority": 2},
                {"id": "urgent", "arrival": 0.2, "service_time": 1.0, "priority": 0},
            ],
            PriorityQueuePolicy(servers=1),
        )
        jobs = {job["id"]: job for job in result["jobs"]}
        self.assertEqual(jobs["urgent"]["start"], 3.0)
        self.assertEqual(jobs["standard"]["start"], 4.0)
        self.assertEqual(result["summary"]["served"], 3)

    def test_patience_causes_abandonment(self):
        result = simulate_priority_queue(
            [
                {"id": "active", "arrival": 0.0, "service_time": 4.0},
                {"id": "leaving", "arrival": 0.1, "service_time": 1.0, "patience": 1.0},
            ],
            PriorityQueuePolicy(servers=1),
        )
        jobs = {job["id"]: job for job in result["jobs"]}
        self.assertEqual(jobs["leaving"]["status"], "abandoned")
        self.assertEqual(result["summary"]["abandoned"], 1)

    def test_capacity_rejects_excess_waiting_jobs(self):
        result = simulate_priority_queue(
            [
                {"id": "active", "arrival": 0.0, "service_time": 4.0},
                {"id": "rejected", "arrival": 0.1, "service_time": 1.0},
            ],
            PriorityQueuePolicy(servers=1, queue_capacity=0),
        )
        jobs = {job["id"]: job for job in result["jobs"]}
        self.assertEqual(jobs["rejected"]["status"], "rejected")
        self.assertEqual(result["summary"]["rejected"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
