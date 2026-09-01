"""Tenant and resource-isolation primitives for QueueCraft Enterprise AI.

The module defines an explicit tenant context and resource scope checks. It is
an authorization boundary, not an identity provider or a database ACL layer.
Persistent backends must enforce the same tenant key at query/storage level.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    principal_id: str
    roles: frozenset[str]

    def validate(self) -> None:
        if not self.tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not self.principal_id.strip():
            raise ValueError("principal_id is required")
        if not self.roles:
            raise ValueError("at least one role is required")


def scoped_resource_id(tenant_id: str, resource_id: str) -> str:
    """Build a stable storage key that makes tenant scope explicit."""
    tenant = tenant_id.strip()
    resource = resource_id.strip()
    if not tenant or not resource:
        raise ValueError("tenant_id and resource_id are required")
    if any(ch in tenant + resource for ch in ("/", "\\", "\x00")):
        raise ValueError("tenant/resource identifiers contain forbidden characters")
    return f"tenant:{tenant}:resource:{resource}"


def authorize_tenant(context: TenantContext, resource: Mapping[str, Any]) -> dict[str, Any]:
    """Verify that a resource belongs to the caller's tenant."""
    context.validate()
    if not isinstance(resource, Mapping):
        raise ValueError("resource must be a mapping")
    resource_tenant = str(resource.get("tenant_id", "")).strip()
    allowed = bool(resource_tenant) and resource_tenant == context.tenant_id
    return {
        "allowed": allowed,
        "tenant_id": context.tenant_id,
        "principal_id": context.principal_id,
        "resource_tenant_id": resource_tenant or None,
        "reason": "tenant_match" if allowed else "cross_tenant_access_denied",
    }


def require_tenant_match(context: TenantContext, resource: Mapping[str, Any]) -> None:
    """Raise on cross-tenant access attempts."""
    decision = authorize_tenant(context, resource)
    if not decision["allowed"]:
        raise PermissionError(decision["reason"])


def tag_resource(resource: Mapping[str, Any], context: TenantContext) -> dict[str, Any]:
    """Return a copied resource with mandatory tenant ownership metadata."""
    context.validate()
    result = dict(resource)
    existing = result.get("tenant_id")
    if existing is not None and str(existing) != context.tenant_id:
        raise PermissionError("resource already belongs to another tenant")
    result["tenant_id"] = context.tenant_id
    result["owner_principal_id"] = context.principal_id
    return result
