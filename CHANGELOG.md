# Changelog

## v3.22.0 — Integrated Model Governance

### Added

- Added `model_governance.py` as the cross-layer contract for walk-forward validation, candidate comparison, continuous evaluation, and promotion gating.
- Added `model_governance_service.py` as a local JSON service adapter with a restricted deterministic built-in model catalog.
- Added integration tests covering fail-closed promotion behavior, registry posture, service validation, and the non-deployment boundary.
- Added `npm run test:model-governance` and included the integrated governance suite in enterprise verification.
- Strengthened CI so the model-governance path is executed alongside the complete Python test suite.

### Governance

- Validation, drift state, protected metrics, evidence identity, and promotion eligibility are now represented together in one report.
- Automatic promotion and external deployment remain prohibited by contract.
- Human approval remains required at the operational decision boundary.

## v3.18.0 — Enterprise Data Plane

### Added

- Added versioned dataset schema primitives and compatibility metadata.
- Added declarative validation profiles for required and non-negative fields.
- Added deterministic dataset manifests with content fingerprints and quality metadata.
- Added reproducible cache-key generation from dataset, scenario, model, and runtime identity.
- Added reproducible run bundles carrying dataset, scenario, model, seed, and outputs.
- Added `data_plane_cli.py` for local validation and run-bundle generation.
- Added `npm run test:data-plane` and included the new tests in the enterprise/AI verification suites.

### Governance

- Dataset identity is explicit and fingerprinted before it participates in a run bundle.
- Run bundles preserve enough metadata to support replay, evidence, and lineage integration.
- Validation remains local and side-effect free.
- No new external telemetry or operational mutation was introduced.
