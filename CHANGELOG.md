# Changelog

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
