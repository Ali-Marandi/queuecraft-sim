"""Lightweight request/response contract helpers for local QueueCraft services."""
from __future__ import annotations
from typing import Any, Mapping

def require_fields(payload:Mapping[str,Any],fields:list[str])->None:
    missing=[f for f in fields if f not in payload]
    if missing: raise ValueError('missing required fields: '+', '.join(missing))

def response(ok:bool,*,data:Any=None,error:str|None=None,request_id:str|None=None)->dict[str,Any]:
    if ok and error is not None: raise ValueError('successful responses cannot contain an error')
    return {'ok':ok,'request_id':request_id,'data':data if ok else None,'error':error if not ok else None,'schema_version':'1.0.0'}
