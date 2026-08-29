# QueueCraft 4 — Decision Engine

QueueCraft 4 unifies the existing simulation capabilities into an offline-first operational decision workflow:

`Scenario → Simulation → Benchmark → Stress-test → Optimize → Explain → Approve`

## What is now unified

### Decision Engine
`decision_engine.py` creates a single auditable package containing:
- baseline versus proposed capacity benchmark
- deterministic SLA assessment
- screening risk indicator with an explicit non-probabilistic disclaimer
- capacity cost/wait Pareto frontier
- demand/service-time sensitivity matrix
- constrained recommendation
- SHA-256 package fingerprint
- human approval state

### What-if Lab foundation
The decision package accepts arrival-demand and service-time multiplier grids. Use the sensitivity output to compare combinations such as `0.8x`, `1.0x`, and `1.2x` demand/service time without changing the underlying scenario.

### Risk analysis
Risk is presented as a deterministic screening indicator derived from SLA gap and P95 tail spread. It is intentionally not called a calibrated probability. A future calibration layer can use replication-level outcomes when those are retained.

### Optimizer
The Pareto analysis searches the configured server range and returns non-dominated cost/wait alternatives. The selected recommendation is the least-cost SLA-compliant frontier point when one exists; otherwise it falls back to a balanced knee point.

### AI Analyst
The existing constrained generative advisor may explain already-evaluated candidates. It can only select a verified candidate ID, must return structured JSON, cannot invent metrics, and cannot execute operational changes. LLM mode remains opt-in; offline mode is deterministic.

### Scenario Certificate
The decision package fingerprint acts as the identity of the complete analytical artifact. Store the JSON output as an evidence package together with the source scenario and release metadata.

## CLI

Run a default local analysis:

```bash
python queuecraft_v4.py
```

Run a supplied scenario and save the evidence package:

```bash
python queuecraft_v4.py examples/hospital_ai_monte_carlo.json --output artifacts/hospital-v4-decision.json
```

Explicitly enable the constrained LLM advisor only when a reviewed API key is available:

```bash
python queuecraft_v4.py examples/hospital_ai_monte_carlo.json --llm --model gpt-5-mini
```

No command in this module changes staffing, infrastructure, cloud resources, or operational systems.

## Recommended operator flow

1. Import and validate source data.
2. Run the baseline simulation with a recorded seed and replication count.
3. Review the What-if sensitivity matrix.
4. Compare cost/service-quality alternatives on the Pareto frontier.
5. Read the constrained recommendation and verify the evidence fingerprint.
6. Re-run with approved current data before approval.
7. Treat the generated package as the evidence artifact for the change review.

## Governance boundary

QueueCraft is a decision-support layer. A recommendation is never an approval and `applied` remains false in the generated package. Any production connector should remain read-only by default and require a separately governed approval path.
