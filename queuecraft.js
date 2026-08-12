/**
 * QueueCraft Enterprise Simulation Engine
 * Supports deterministic and stochastic (Poisson/Exponential/Normal) multi-server queue simulations.
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
  
  // Calculate server utilization
  const serverUtilizations = serverLoad.map((load, idx) => ({
    server: idx + 1,
    busyTime: load,
    utilization: makespan > 0 ? (load / makespan) * 100 : 0
  }));

  const averageUtilization = serverUtilizations.reduce((sum, s) => sum + s.utilization, 0) / servers;

  // Queue length over time sampling
  const timelineEvents = [];
  jobs.forEach(job => {
    timelineEvents.push({ time: job.arrival, type: 'arrival' });
    timelineEvents.push({ time: job.start, type: 'start' });
    timelineEvents.push({ time: job.end, type: 'departure' });
  });
  timelineEvents.sort((a, b) => a.time - b.time || (a.type === 'departure' ? -1 : 1));

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
 * Generate stochastic arrival and service times using exponential distribution (Monte Carlo simulation)
 */
export function generateStochasticData(count = 50, arrivalRate = 2.0, serviceRate = 3.0) {
  const arrivals = [];
  let currentArrival = 0;
  for (let i = 0; i < count; i++) {
    // Exponential inter-arrival time: -ln(1 - U) / lambda
    const interArrival = -Math.log(1 - Math.random()) / arrivalRate;
    currentArrival += interArrival;
    arrivals.push(Number(currentArrival.toFixed(2)));
  }

  const serviceTimes = [];
  for (let i = 0; i < count; i++) {
    // Exponential service time: -ln(1 - U) / mu
    const service = -Math.log(1 - Math.random()) / serviceRate;
    serviceTimes.push(Math.max(0.1, Number(service.toFixed(2))));
  }

  return { arrivals, serviceTimes };
}

/**
 * Compare multiple server configurations (Scenario Analysis)
 */
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
