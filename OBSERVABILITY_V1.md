# QueueCraft Observability & Decision Ledger v1

QueueCraft includes a local append-only decision ledger and queryable decision timeline.

## Ledger

`decision_ledger.py` stores explicit events in JSONL and links each event to the previous one with a SHA-256 hash. `verify()` detects changed payloads and broken chains.

## Timeline

`decision_timeline.py` filters recent events by type and returns event-type counts together with ledger integrity status.

## Example

```python
from decision_timeline import query_ledger
print(query_ledger(event_type="promotion_blocked"))
```

The observability layer is local and advisory. It does not authorize deployment or external operational changes.