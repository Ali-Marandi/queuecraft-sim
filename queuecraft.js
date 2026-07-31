export function simulateQueue(arrivals, serviceTimes, servers = 1) {
  if (arrivals.length !== serviceTimes.length || arrivals.length === 0 || servers < 1) {
    throw new RangeError("equal non-empty arrays and at least one server are required");
  }
  if (arrivals.some((x, i) => !Number.isFinite(x) || x < 0 || (i && x < arrivals[i - 1])) ||
      serviceTimes.some((x) => !Number.isFinite(x) || x < 0)) {
    throw new RangeError("invalid arrival or service data");
  }
  const available = Array(servers).fill(0);
  const jobs = arrivals.map((arrival, index) => {
    let server = 0;
    for (let i = 1; i < servers; i += 1) if (available[i] < available[server]) server = i;
    const start = Math.max(arrival, available[server]);
    const end = start + serviceTimes[index];
    available[server] = end;
    return { arrival, start, end, wait: start - arrival, server };
  });
  const averageWait = jobs.reduce((sum, job) => sum + job.wait, 0) / jobs.length;
  return { jobs, averageWait, makespan: Math.max(...available) };
}
