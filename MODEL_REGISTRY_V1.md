# QueueCraft Governed Model Registry v1

QueueCraft now includes a local model registry that separates model identity and lifecycle state from scenario inputs.

## Lifecycle

`development -> candidate -> champion -> retired`

Moving a model into `candidate` requires an explicit validation status and evidence fingerprint. Promotion to `champion` requires accepted validation plus a human approval identifier. Retirement also requires an explicit approval identifier.

## Governance guarantees

- Automatic promotion is disabled.
- Registry actions do not deploy models or modify production endpoints.
- Model limitations and validation evidence remain attached to the registry record.
- Registry snapshots summarize stage distribution and current champions.

## Example

```python
from model_registry import RegistryRecord, review_candidate, promote_to_champion

record = RegistryRecord("forecast-v2", "arrival_forecast", "2.0.0")
review_candidate(record, validation_status="validated", evidence_fingerprint="...")
promote_to_champion(record, approval_id="APR-2026-001")
```

The registry is intentionally offline-first. Deployment adapters and centralized catalogues remain separate concerns.
