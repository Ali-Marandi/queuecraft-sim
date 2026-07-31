import assert from "node:assert/strict";
import test from "node:test";
import { simulateQueue } from "./queuecraft.js";

test("single server builds a deterministic queue", () => {
  const result = simulateQueue([0, 1, 2], [3, 2, 1]);
  assert.deepEqual(result.jobs.map((job) => job.wait), [0, 2, 3]);
  assert.equal(result.averageWait, 5 / 3);
  assert.equal(result.makespan, 6);
});

test("a second server reduces waiting", () => {
  const one = simulateQueue([0, 0, 0], [2, 2, 2], 1);
  const two = simulateQueue([0, 0, 0], [2, 2, 2], 2);
  assert.ok(two.averageWait < one.averageWait);
});
