"""Enterprise security primitives for QueueCraft control-plane decisions.

Dependency-free, deterministic helpers for threat-aware input validation,
role/permission checks, and safe operation classification. This module does
not authenticate identities or contact external systems.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, FrozenSet


RISK_LEVELS = ("low", "medium", "high", "critical")


@dataclass(frozen=True)
class Principal:
    principal_id: str
    roles: FrozenSet[str]
    permissions: FrozenSet[str] = frozenset()

    def validate(self) -> None:
        if not self.principal_id.strip():
            raise ValueError("principal_id is required")
        if not self.roles:
            raise ValueError("at least one role is required")


def authorize(principal: Principal, permission: str, *, required_role: str | None = None) -> dict[str, Any]:
    principal.validate()
    if not permission.strip():
        raise ValueError("permission is required")
    role_ok = required_role is None or required_role in principal.roles
    permission_ok = permission in principal.permissions
    return {
        "principal_id": principal.principal_id,
        "permission": permission,
        "required_role": required_role,
        "role_satisfied": role_ok,
        "permission_satisfied": permission_ok,
        "allowed": role_ok and permission_ok,
        "deny_by_default": True,
    }


def validate_operation_request(request: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request, Mapping):
        raise ValueError("operation request must be a mapping")
    operation = str(request.get("operation", "")).strip()
    if not operation:
        raise ValueError("operation is required")
    risk = str(request.get("risk_level", "medium")).lower().strip()
    if risk not in RISK_LEVELS:
        raise ValueError("risk_level must be low, medium, high, or critical")
    external = bool(request.get("external_side_effect", False))
    auto_execute = bool(request.get("automatic_execution", False))
    if external and auto_execute:
        return {"valid": False, "status": "blocked", "reason": "automatic external side effects are prohibited"}
    return {"valid": True, "status": "review_required" if risk in {"high", "critical"} else "accepted", "operation": operation, "risk_level": risk, "external_side_effect": external}
