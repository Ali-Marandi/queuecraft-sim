# Changelog

## v3.3.0 — Commercial Workspace

### Added

- Added an integrity-verified local Workspace for browsing saved scenarios.
- Added one-click execution of saved scenarios with explicit SLA status and fingerprint display.
- Added portable audit-ready JSON report export containing assumptions, simulation output, timestamps, and SLA assessment.
- Added safe operator-scoped deletion for local scenarios.
- Added `COMMERCIAL_PRODUCT_SPEC_V4.md` with enterprise acceptance criteria and the advanced commercial roadmap.

### Quality

- Added regression coverage for load, export, fingerprint preservation, and deletion behavior.
- Python suite: 38 tests passing.
- JavaScript suite: 7 tests passing.

### Security and privacy

- Workspace data remains local by default.
- The local simulation path does not send telemetry or mutate infrastructure.
- No GitHub token or signing secret is included in source or release artifacts.
