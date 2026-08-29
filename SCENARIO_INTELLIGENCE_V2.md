# QueueCraft Scenario Intelligence 2.0

## Purpose

Scenario Intelligence 2.0 connects QueueCraft's operational decision engine with the market-intelligence layer. It is a decision-support layer, not a trading system.

## Scenario Graph

The graph represents operator-specified scenario relationships such as:

`rates -> liquidity -> market volatility -> operational demand -> queue SLA risk`

Each edge has an explicit weight. Propagation is bounded and deterministic. The result is a ranked list of scenario drivers.

Important: the graph is not a causal inference engine. Edge weights are assumptions supplied by the scenario designer.

## Counterfactual Lab

The counterfactual layer produces an equivalent-load stress path from historical arrivals:

`equivalent load = historical arrivals × demand multiplier × service-time multiplier`

This supports transparent what-if comparisons while avoiding an unsupported claim that market variables causally determine queue arrivals.

## Governance Manifest

Every integrated run records:

- model families used
- assumptions
- input keys
- whether AI was enabled
- human approval requirement
- external-operation status
- outbound telemetry default
- restriction of decisions to evaluated candidate sets
- SHA-256 manifest and scenario fingerprints

## Research Boundaries

DSGE, causal ML, topological data analysis, diffusion models, quantum methods, federated learning, and ANFIS remain research-only in the current implementation.

This conservative boundary is deliberate. The FSB's current work highlights model risk, data quality, third-party dependency, correlations, cyber risk and governance as important AI-related vulnerabilities in finance. citeturn411486search1turn411486search4

The BIS likewise highlights the potential for common models/data to increase behavioural correlation and amplify contagion, while stressing governance, data governance and model-risk controls. citeturn411486search2turn411486search3

## Run

```bash
python scenario_intelligence_cli.py examples/integrated_scenario_intelligence.json \
  --output artifacts/integrated-scenario.json
```

The output is deterministic for a fixed scenario and seed, and it never applies infrastructure or trading changes.
