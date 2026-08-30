"""Aggregate enterprise readiness checks without claiming certification."""
from __future__ import annotations
from typing import Any

def readiness_snapshot(*,security_ok:bool,rbac_ok:bool,encrypted_store_ok:bool,replay_ok:bool,lineage_ok:bool,policy_ok:bool,worker_ok:bool)->dict[str,Any]:
    checks={'security':security_ok,'rbac':rbac_ok,'encrypted_store':encrypted_store_ok,'replay':replay_ok,'lineage':lineage_ok,'policy':policy_ok,'worker_execution':worker_ok}
    passed=sum(checks.values())
    return {'checks':checks,'passed':passed,'total':len(checks),'status':'ready_for_review' if passed==len(checks) else 'needs_attention','certified':False}
