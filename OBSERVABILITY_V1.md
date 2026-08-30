# QueueCraft Observability & Decision Ledger v1

QueueCraft now includes a local, append-only decision ledger for operational observability.

## What is recorded

The ledger can capture explicit events such as:

- simulation completed
- scenario saved or executed
- drift evaluated
- challenger evaluation requested
- promotion blocked or approved
- evidence generated

Each event stores a canonical payload and a SHA-256 hash linked to the previous event hash.

## Integrity

`DecisionLedger.verify()` walks the chain and detects changed payloads, removed/reordered events, or broken links. This is tamper-evident local storage, not a cryptographic signature or remote immutable archive.

## Storage

The default path is `artifacts/decision-ledger.jsonl`. Records are local and are not transmitted by the ledger itself.

## Trust boundary

Observability records explain what QueueCraft decided or observed. They do not authorize deployment or external operational changes.