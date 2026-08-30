# QueueCraft Decision Replay v1

QueueCraft can replay an evidence package locally and compare the replayed decision with the stored decision record.

## Guarantees

- Canonical JSON fingerprinting for stable comparisons.
- Nested field-level divergence reporting.
- Explicit seed/model/assumption metadata in replay snapshots when supplied.
- No deployment, scaling, trading, or external operational side effects are performed by the replay helper.

## Contract

`decision_replay.replay_decision(evidence, executor)` requires a deterministic executor that consumes the evidence package and returns a decision object.

The result is one of:

- `identical`: replay matches the stored decision record.
- `diverged`: one or more decision fields differ.

## CLI

```bash
python decision_replay_service.py evidence.json
```

The default CLI executor is an identity executor for integrity inspection. Production replay should provide a domain-specific deterministic executor wired to the relevant model and simulation pipeline.

## Governance boundary

A successful replay proves reproducibility of the supplied execution path; it is not proof that the underlying model is correct or causally valid. Replays remain advisory and do not authorize external actions.
