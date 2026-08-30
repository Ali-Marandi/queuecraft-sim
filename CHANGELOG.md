# Changelog

## v3.16.0 — Policy Governance and Human Approval

### Added

- Added deterministic declarative Policy Engine with `allow`, `review`, and `block` outcomes.
- Added rule operators `gte`, `gt`, `lte`, `lt`, `eq`, `neq`, and `in`.
- Added explicit rule precedence: block > review > allow.
- Added Human Approval Workflow with required reviewer role, identity, notes, and terminal decisions.
- Added JSON service contract for policy evaluation and approval transitions.
- Added dedicated policy and approval verification commands and tests.
- Refreshed README and governance documentation for the new control layer.

### Governance

- Policy evaluation is side-effect free and never performs operational changes.
- Approval decisions require an explicit human reviewer role and identity.
- Approved/rejected requests record that no deployment was performed.
- Existing evidence, lineage, replay, drift, and promotion controls remain active.
