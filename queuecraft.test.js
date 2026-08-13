import assert from "node:assert/strict";
import test from "node:test";
import { simulateQueue, generateStochasticData, compareScenarios, simulateMultiTierQueue } from "./queuecraft.js";

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

test("simulateMultiTierQueue correctly chains multiple stages", () => {
  const arrivals = [0, 1, 2, 3, 4];
  const tierConfigs = [
    { name: "Stage 1", servers: 2, avgService: 1.0 },
    { name: "Stage 2", servers: 2, avgService: 1.5 }
  ];
  const result = simulateMultiTierQueue(arrivals, tierConfigs);

  assert.strictEqual(result.tiers.length, 2);
  assert.strictEqual(result.overallSummary.totalTiers, 2);
  assert.strictEqual(result.overallSummary.totalJobs, 5);
  assert.ok(result.overallSummary.overallMakespan > 0);
});
