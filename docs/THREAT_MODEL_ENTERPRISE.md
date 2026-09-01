# QueueCraft Enterprise Threat Model

## Scope

This document covers the desktop application, local analytical runtime, governance artifacts, model lifecycle, execution workers, and optional generative-AI advisor. It does not claim certification or complete coverage of a customer deployment.

## Security objectives

1. Preserve tenant and resource isolation.
2. Prevent unauthorized promotion or external operational side effects.
3. Detect tampering of scenarios, decisions, evidence, and run artifacts.
4. Keep credentials and sensitive evidence out of exported governance packages.
5. Preserve deterministic replay and provenance where the underlying workload is deterministic.
6. Make high-risk operations explicit and reviewable.

## Primary assets

| Asset | Security property | Main control |
|---|---|---|
| Scenario | Integrity / reproducibility | schema validation + fingerprint |
| Dataset manifest | Integrity / provenance | content fingerprint + catalog scope |
| Model record | Integrity / governance | lifecycle gate + approval |
| Experiment/run bundle | Integrity / replayability | deterministic identity + run fingerprint |
| Decision | Integrity / accountability | decision envelope |
| Evidence | Integrity / confidentiality | fingerprint + redaction + optional signature |
| Approval | Authorization / accountability | explicit principal, role, state transition |
| Tenant resource | Isolation | mandatory tenant context and scope key |
| Execution workload | Availability / containment | budgets, bounded workers, cancellation, checkpoint |

## Threats and mitigations

### T1 — Cross-tenant data access

**Threat:** a caller presents an object belonging to another tenant or a persistence layer omits the tenant predicate.

**Mitigation:** `tenant_isolation.py` makes tenant identity explicit, denies mismatches, and provides a tenant-scoped storage-key convention. Production persistence must enforce the same predicate at the query/storage boundary.

### T2 — Unauthorized model promotion

**Threat:** an analyst bypasses validation and promotes a model directly to champion.

**Mitigation:** lifecycle stages are explicit; accepted validation evidence and an approval ID are required for promotion. The promotion gate remains advisory and never deploys.

### T3 — Evidence tampering

**Threat:** decision/evidence content is changed after approval or export.

**Mitigation:** canonical fingerprints detect content changes; `signed_evidence.py` can add an Ed25519 detached signature for stronger authenticity when an appropriate key-management process is available.

### T4 — Secret leakage through evidence exports

**Threat:** API tokens, passwords, cookies, or private keys enter audit packages.

**Mitigation:** recursive redaction is applied at the audit export boundary. Export sanitization must be treated as defense-in-depth; sensitive source files must still be protected by deployment controls.

### T5 — Prompt or model-induced plan fabrication

**Threat:** a generative model invents capacity values or recommends an unverified plan.

**Mitigation:** the advisor receives an evaluated candidate catalog and is allowed to select only an existing candidate ID. Structured output is validated against that catalog. LLM output cannot invoke tools or apply changes.

### T6 — Resource exhaustion

**Threat:** a large replication plan consumes excessive CPU, memory, or runtime.

**Mitigation:** execution budgets, workload estimation, bounded worker pools, chunking, cancellation, and checkpoint/resume. Admission policies should be enforced before accepting untrusted workloads.

### T7 — Stale or drifting inputs

**Threat:** a previously acceptable model is used against materially changed demand or input distributions.

**Mitigation:** streaming drift monitoring, continuous evaluation, protected-metric guardrails, and challenger evaluation triggers. Drift signals are screening controls and require contextual review.

### T8 — Replay overclaim

**Threat:** reproducibility is mistaken for causal validity or business correctness.

**Mitigation:** documentation and governance contracts distinguish execution reproducibility from model validity and causal inference.

### T9 — Supply-chain compromise

**Threat:** a malicious dependency or compromised build environment alters the released artifact.

**Mitigation:** lock dependency versions/ranges appropriately, verify CI on supported runtimes, use release provenance/signing, review dependency changes, and produce checksums for distributable artifacts.

### T10 — Local secret/key compromise

**Threat:** signing keys or API credentials are readable by another local process/user.

**Mitigation:** do not embed private keys in source, evidence, or installers; use OS-backed secret storage or an enterprise KMS/HSM for production deployments; rotate and revoke keys according to the deployment's identity policy.

## Trust boundaries

```text
[User / Operator]
      |
      v
[Desktop UI / Bridge]
      |
      +--> [Validation + Scenario Compiler]
      |
      +--> [Simulation / Execution Plane]
      |
      +--> [Model + Governance Plane]
      |
      +--> [Evidence / Audit Store]
      |
      +--> [Optional External LLM: read-only advisory input]

External operational systems are outside the default trust boundary.
The analytics/governance layers do not have authority to mutate them.
```

## Residual risks

- A compromised host can bypass application-level controls.
- Local persistence can be modified by a user with filesystem-level access; fingerprints detect tampering but do not prevent it.
- Ed25519 signatures authenticate possession of a private key but do not independently establish the legal identity of the signer.
- Tenant isolation helpers cannot substitute for database-level row-level security in a multi-user service.

## Enterprise deployment requirements

For a centralized deployment, add an identity provider, short-lived credentials, server-side authorization, encrypted storage, immutable/append-only audit retention, centralized key management, network egress controls, backup/restore testing, vulnerability scanning, dependency SBOM generation, signed releases, incident response, and independent security review.
