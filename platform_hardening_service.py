"""Stable JSON service contract for QueueCraft platform-hardening capabilities."""
from __future__ import annotations

import json
from typing import Any

from scenario_compiler import compile_scenario, verify_compiled_scenario
from signed_evidence import sign_artifact, verify_signature
from simulation_performance import choose_execution_mode, estimate_workload
from tenant_isolation import TenantContext, authorize_tenant, scoped_resource_id


def compile_scenario_json(payload_json: str) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        return json.dumps(compile_scenario(payload), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)})


def verify_compiled_scenario_json(payload_json: str) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        return json.dumps(verify_compiled_scenario(payload), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)})


def sign_artifact_json(payload_json: str, *, signer_id: str, private_key_pem: str) -> str:
    try:
        payload = json.loads(payload_json) if payload_json else {}
        if not isinstance(payload, dict):
            raise ValueError("artifact payload must be an object")
        return json.dumps(sign_artifact(payload, signer_id=signer_id, private_key_pem=private_key_pem), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)})


def verify_signature_json(artifact_json: str, envelope_json: str, *, public_key_pem: str) -> str:
    try:
        artifact = json.loads(artifact_json) if artifact_json else {}
        envelope = json.loads(envelope_json) if envelope_json else {}
        return json.dumps(verify_signature(artifact, envelope, public_key_pem=public_key_pem), ensure_ascii=False)
    except (TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        return json.dumps({"error": str(error)})


def performance_plan_json(*, replications: int, horizon: int, stages: int, chunk_size: int = 10, work_unit_override: int | None = None) -> str:
    try:
        workload = estimate_workload(replications=replications, horizon=horizon, stages=stages, chunk_size=chunk_size)
        mode = choose_execution_mode(work_unit_override if work_unit_override is not None else workload["work_units"])
        return json.dumps({"workload": workload, "execution": mode}, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        return json.dumps({"error": str(error)})


def tenant_scope_json(*, tenant_id: str, principal_id: str, roles: list[str], resource_id: str, resource_tenant_id: str | None = None) -> str:
    try:
        context = TenantContext(tenant_id, principal_id, frozenset(roles))
        resource = {"resource_id": resource_id, "tenant_id": resource_tenant_id or tenant_id}
        return json.dumps({
            "resource_key": scoped_resource_id(tenant_id, resource_id),
            "authorization": authorize_tenant(context, resource),
        }, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        return json.dumps({"error": str(error)})
