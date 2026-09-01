# Changelog

## v3.23.0 — Enterprise Platform Hardening

### Added

- Added `signed_evidence.py` with Ed25519 detached signatures and artifact fingerprints for stronger evidence authenticity.
- Added `tenant_isolation.py` with explicit tenant context, scoped resource identifiers, tenant-match authorization, and cross-tenant overwrite protection.
- Added `scenario_compiler.py` to validate, normalize, fingerprint, and classify scenarios into interactive/batch/distributed execution plans before execution.
- Added `simulation_performance.py` with workload estimation, safe execution-mode selection, stable per-replication seeds, and bounded benchmark metadata.
- Added `platform_hardening_service.py` as the stable JSON contract for scenario compilation, signature verification, performance planning, and tenant authorization.
- Added `test_enterprise_platform_hardening.py` and `test_platform_hardening_service.py` covering cryptographic verification, tenant isolation, scenario compilation, workload classification, deterministic seed assignment, and service contracts.
- Added `docs/THREAT_MODEL_ENTERPRISE.md` documenting trust boundaries, primary assets, threats, mitigations, residual risks, and centralized-deployment requirements.
- Expanded CI quality gates to execute the platform-hardening suites on supported Python versions.

### Security / Governance

- Evidence can now be authenticated cryptographically when an enterprise key-management process supplies the signing keys.
- Tenant ownership is explicit at the application boundary; centralized deployments must enforce the same tenant predicate in persistent storage and queries.
- Scenario execution can be admitted based on estimated workload size rather than blindly submitting arbitrarily large simulations.
- Existing human-approval and no-automatic-deployment invariants remain unchanged.

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
