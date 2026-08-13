/**
 * QueueCraft Enterprise Simulation Engine v2.2
 * Supports deterministic, stochastic, and multi-tier queue simulations.
 */

export function simulateQueue(arrivals, serviceTimes, servers = 1) {
  if (arrivals.length !== serviceTimes.length || arrivals.length === 0 || servers < 1) {
    throw new RangeError("equal non-empty arrays and at least one server are required");
  }
  if (arrivals.some((x, i) => !Number.isFinite(x) || x < 0 || (i && x < arrivals[i - 1])) ||
      serviceTimes.some((x) => !Number.isFinite(x) || x < 0)) {
    throw new RangeError("invalid arrival or service data");
  }

  const available = Array(servers).fill(0);
  const serverLoad = Array(servers).fill(0);

  const jobs = arrivals.map((arrival, index) => {
    let server = 0;
    for (let i = 1; i < servers; i += 1) {
      if (available[i] < available[server]) {
        server = i;
      }
    }
    const start = Math.max(arrival, available[server]);
    const serviceTime = serviceTimes[index];
    const end = start + serviceTime;

    serverLoad[server] += serviceTime;
    available[server] = end;

    return {
      id: index + 1,
      arrival,
      start,
      end,
      wait: start - arrival,
      service: serviceTime,
      server: server + 1
    };
  });

  const makespan = Math.max(...available);
  const totalWait = jobs.reduce((sum, job) => sum + job.wait, 0);
  const averageWait = totalWait / jobs.length;
  const maxWait = Math.max(...jobs.map(j => j.wait));

  const serverUtilizations = serverLoad.map((load, idx) => ({
    server: idx + 1,
    busyTime: load,
    utilization: makespan > 0 ? Number(((load / makespan) * 100).toFixed(2)) : 0
  }));

  const averageUtilization = serverUtilizations.reduce((sum, s) => sum + s.utilization, 0) / servers;

  return {
    jobs,
    summary: {
      totalJobs: jobs.length,
      averageWait: Number(averageWait.toFixed(2)),
      maxWait: Number(maxWait.toFixed(2)),
      makespan: Number(makespan.toFixed(2)),
      averageUtilization: Number(averageUtilization.toFixed(2)),
      serverUtilizations
    }
  };
}

/**
 * Multi-Tier Queue Simulation (e.g., Stage 1: Reception, Stage 2: Processing, Stage 3: Quality Check/Checkout)
 */
export function simulateMultiTierQueue(arrivals, tierConfigs) {
  // tierConfigs is an array of objects: [{ name: 'Reception', servers: 2, serviceMultiplier: 1.0 }, ...]
  if (!tierConfigs || tierConfigs.length === 0) {
    throw new Error("At least one tier configuration is required");
  }

  let currentArrivals = arrivals;
  let tierResults = [];

  tierConfigs.forEach((tier, idx) => {
    // Generate service times for this tier based on count
    const serviceTimes = currentArrivals.map(() => {
      // Exponential service distribution default
      const base = -Math.log(1 - Math.random()) * (tier.avgService || 2.0);
      return Math.max(0.2, Number((base * (tier.serviceMultiplier || 1.0)).toFixed(2)));
    });

    const result = simulateQueue(currentArrivals, serviceTimes, tier.servers || 1);
    tierResults.push({
      tierName: tier.name || `Tier ${idx + 1}`,
      servers: tier.servers,
      summary: result.summary,
      jobs: result.jobs
    });

    // Completion order, not original job order, determines arrivals at the next tier.
    // Multi-server stages may finish jobs out of order; the next queue requires
    // chronologically sorted arrival times.
    currentArrivals = result.jobs.map(j => j.end).sort((a, b) => a - b);
  });

  const overallMakespan = tierResults[tierResults.length - 1].summary.makespan;
  const totalAvgWait = Number((tierResults.reduce((sum, t) => sum + t.summary.averageWait, 0)).toFixed(2));

  return {
    tiers: tierResults,
    overallSummary: {
      totalTiers: tierConfigs.length,
      totalJobs: arrivals.length,
      totalAvgWait,
      overallMakespan
    }
  };
}

export function generateStochasticData(count = 50, arrivalRate = 2.0, serviceRate = 3.0) {
  const arrivals = [];
  let currentArrival = 0;
  for (let i = 0; i < count; i++) {
    const interArrival = -Math.log(1 - Math.random()) / arrivalRate;
    currentArrival += interArrival;
    arrivals.push(Number(currentArrival.toFixed(2)));
  }

  const serviceTimes = [];
  for (let i = 0; i < count; i++) {
    const service = -Math.log(1 - Math.random()) / serviceRate;
    serviceTimes.push(Math.max(0.1, Number(service.toFixed(2))));
  }

  return { arrivals, serviceTimes };
}

export function compareScenarios(arrivals, serviceTimes, serverCounts = [1, 2, 3, 4, 5]) {
  return serverCounts.map(servers => {
    try {
      const result = simulateQueue(arrivals, serviceTimes, servers);
      return {
        servers,
        averageWait: result.summary.averageWait,
        maxWait: result.summary.maxWait,
        makespan: result.summary.makespan,
        averageUtilization: result.summary.averageUtilization
      };
    } catch (e) {
      return { servers, error: e.message };
    }
  });
}
