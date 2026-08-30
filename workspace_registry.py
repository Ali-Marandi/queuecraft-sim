"""Multi-project local workspace registry for QueueCraft."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any
_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")
def _now() -> str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
@dataclass(frozen=True)
class Workspace:
    workspace_id: str; name: str; owner_id: str; created_at: str; updated_at: str; retention_days: int = 90
class WorkspaceRegistry:
    def __init__(self, root: str | Path):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.index=self.root/"workspaces.json"
    def _validate_id(self,v:str)->str:
        v=str(v).strip()
        if not _ID_RE.fullmatch(v): raise ValueError("workspace_id must contain only letters, numbers, dot, underscore, or hyphen")
        return v
    def create(self,workspace_id:str,name:str,owner_id:str,retention_days:int=90)->dict[str,Any]:
        workspace_id=self._validate_id(workspace_id)
        if not name.strip() or not owner_id.strip(): raise ValueError("name and owner_id are required")
        if retention_days<1: raise ValueError("retention_days must be positive")
        current=self._load_index()
        if workspace_id in current: raise ValueError("workspace already exists")
        now=_now(); record=Workspace(workspace_id,name.strip(),owner_id.strip(),now,now,int(retention_days))
        current[workspace_id]=asdict(record); self._save_index(current); (self.root/workspace_id).mkdir(parents=True,exist_ok=True); return asdict(record)
    def get(self,workspace_id:str)->dict[str,Any]:
        workspace_id=self._validate_id(workspace_id); current=self._load_index()
        if workspace_id not in current: raise FileNotFoundError(f"workspace '{workspace_id}' does not exist")
        return dict(current[workspace_id])
    def list(self)->list[dict[str,Any]]: return list(sorted(self._load_index().values(),key=lambda x:x['workspace_id']))
    def touch(self,workspace_id:str)->dict[str,Any]:
        record=self.get(workspace_id); record['updated_at']=_now(); current=self._load_index(); current[workspace_id]=record; self._save_index(current); return record
    def _load_index(self)->dict[str,dict[str,Any]]:
        if not self.index.exists(): return {}
        value=json.loads(self.index.read_text(encoding='utf-8'))
        if not isinstance(value,dict): raise ValueError('workspace index is invalid')
        return value
    def _save_index(self,value:dict[str,dict[str,Any]])->None:
        temp=self.index.with_suffix('.tmp'); temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); temp.replace(self.index)
