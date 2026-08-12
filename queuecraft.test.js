import assert from "node:assert/strict";
import test from "node:test";
import { simulateQueue, generateStochasticData, compareScenarios } from "./queuecraft.js";

test("single server builds a deterministic queue", () => {
  const result = simulateQueue([0, 1, 2], [3, 2, 1]);
  assert.deepEqual(result.jobs.map((job) => job.wait), [0, 2, 3]);
  assert.equal(result.summary.averageWait, 1.67);
  assert.equal(result.summary.makespan, 6);
});

test("a second server reduces waiting", () => {
  const one = simulateQueue([0, 0, 0], [2, 2, 2], 1);
  const two = simulateQueue([0, 0, 0], [2, 2, 2], 2);
  assert.ok(two.summary.averageWait < one.summary.averageWait);
});

test("generateStochasticData creates correct array sizes", () => {
  const { arrivals, serviceTimes } = generateStochasticData(20, 2.0, 3.0);
  assert.strictEqual(arrivals.length, 20);
  assert.strictEqual(serviceTimes.length, 20);
});

test("compareScenarios returns results for multiple server counts", () => {
  const arrivals = [0, 1, 2, 3, 4];
  const serviceTimes = [2, 2, 2, 2, 2];
  const comparison = compareScenarios(arrivals, serviceTimes, [1, 2, 4]);
  
  assert.strictEqual(comparison.length, 3);
  assert.strictEqual(comparison[0].servers, 1);
  assert.strictEqual(comparison[2].servers, 4);
});
