"""Portable JSON/CSV report export helpers with deterministic manifests."""
from __future__ import annotations
import csv, hashlib, io, json
from typing import Any, Mapping

def canonical(value:Any)->str: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def export_json(decision:Mapping[str,Any])->str: return json.dumps(dict(decision),ensure_ascii=False,indent=2)+'\n'
def export_csv(rows:list[Mapping[str,Any]])->str:
    if not rows: return ''
    fields=sorted({k for row in rows for k in row})
    out=io.StringIO(); writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader()
    for row in rows: writer.writerow({k:row.get(k) for k in fields})
    return out.getvalue()
def build_manifest(*,artifact_type:str,content:str,source_fingerprint:str,version:str='1.0.0')->dict[str,str]:
    return {'manifest_version':version,'artifact_type':artifact_type,'source_fingerprint':source_fingerprint,'content_sha256':hashlib.sha256(content.encode()).hexdigest()}
