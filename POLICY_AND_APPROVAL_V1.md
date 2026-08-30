# QueueCraft Policy and Approval Workflow v1

QueueCraft 3.16 adds a declarative policy engine and a human approval workflow around the existing decision, evidence, replay, and lineage layers.

## Policy engine

`policy_engine.py` evaluates a `PolicySet` against a decision object. Rules support `gte`, `gt`, `lte`, `lt`, `eq`, `neq`, and `in`. Each matching rule emits `allow`, `review`, or `block`. The strongest matching action wins: `block` > `review` > `allow`.

Missing fields are reported as `not_evaluable`; the engine does not fabricate values.

## Approval workflow

`approval_workflow.py` models the lifecycle `pending → approved|rejected` with explicit reviewer identity and required role. Non-pending requests cannot be transitioned again.

Every approved or rejected request records a reviewer and note and explicitly states that no deployment was performed.

## Service contract

`approval_workflow_service.py` exposes JSON operations:

- `evaluate_policy`
- `create_approval`
- `transition_approval`
- `workflow_summary`

## Governance boundary

Policies and approvals govern QueueCraft recommendations. They do not perform infrastructure changes, trading, scaling, or external mutations. Integrations must preserve the same human-approval boundary.
