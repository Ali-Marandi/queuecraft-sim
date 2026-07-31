# QueueCraft Sim

A deterministic discrete-event simulator for FIFO queues with one or more
servers. It reports per-job timing, mean waiting time and total makespan.

```js
import { simulateQueue } from "./queuecraft.js";

const result = simulateQueue([0, 1, 2], [3, 2, 1], 1);
```

Run `npm test`. Inputs are explicit arrival and service times, making scenarios
fully reproducible. Stochastic distribution sampling is intentionally separate.
