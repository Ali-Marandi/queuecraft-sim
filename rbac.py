"""Deny-by-default application RBAC for QueueCraft workspaces."""
from __future__ import annotations
from dataclasses import dataclass
ROLES={"viewer","analyst","reviewer","admin"}
PERMISSIONS={"scenario:read","scenario:write","scenario:delete","decision:run","decision:export","approval:review","policy:manage","workspace:admin","model:promote"}
ROLE_PERMISSIONS={"viewer":{"scenario:read"},"analyst":{"scenario:read","scenario:write","decision:run","decision:export"},"reviewer":{"scenario:read","decision:run","decision:export","approval:review","model:promote"},"admin":PERMISSIONS}
@dataclass(frozen=True)
class Principal:
    principal_id:str; role:str
    def validate(self)->None:
        if not self.principal_id.strip(): raise ValueError('principal_id is required')
        if self.role not in ROLES: raise ValueError('unsupported role')
def authorize(principal:Principal,permission:str,*,resource_owner_id:str|None=None)->dict[str,object]:
    principal.validate()
    if permission not in PERMISSIONS: raise ValueError('unsupported permission')
    allowed=permission in ROLE_PERMISSIONS[principal.role]
    if resource_owner_id is not None and principal.role!='admin' and permission in {'scenario:write','scenario:delete'}:
        allowed=allowed and principal.principal_id==resource_owner_id
    return {'allowed':allowed,'principal_id':principal.principal_id,'role':principal.role,'permission':permission,'reason':'granted' if allowed else 'denied_by_default_or_scope'}
