"""Authenticated encrypted local JSON store for QueueCraft."""
from __future__ import annotations
import base64, hashlib, json, os
from pathlib import Path
from typing import Any
try:
    from cryptography.fernet import Fernet, InvalidToken  # type: ignore
except ImportError:  # pragma: no cover
    Fernet=None; InvalidToken=Exception

def derive_key(secret:str,salt:bytes)->bytes:
    if not secret: raise ValueError('secret is required')
    digest=hashlib.pbkdf2_hmac('sha256',secret.encode(),salt,200_000,dklen=32)
    return base64.urlsafe_b64encode(digest)

class EncryptedJsonStore:
    def __init__(self,path:str|Path,secret:str):
        if Fernet is None: raise RuntimeError('cryptography package is required for encrypted storage')
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.secret=secret
    def write(self,value:dict[str,Any])->None:
        salt=os.urandom(16); token=Fernet(derive_key(self.secret,salt)).encrypt(json.dumps(value,ensure_ascii=False,sort_keys=True).encode())
        envelope={'version':'1','salt':base64.b64encode(salt).decode('ascii'),'token':token.decode('ascii')}
        temp=self.path.with_suffix(self.path.suffix+'.tmp'); temp.write_text(json.dumps(envelope,sort_keys=True)+'\n',encoding='utf-8'); temp.replace(self.path)
    def read(self)->dict[str,Any]:
        if not self.path.exists(): raise FileNotFoundError(self.path)
        env=json.loads(self.path.read_text(encoding='utf-8'))
        if env.get('version')!='1': raise ValueError('unsupported encrypted-store version')
        try: raw=Fernet(derive_key(self.secret,base64.b64decode(env['salt']))).decrypt(env['token'].encode('ascii'))
        except InvalidToken as exc: raise ValueError('encrypted store authentication failed') from exc
        value=json.loads(raw.decode('utf-8'))
        if not isinstance(value,dict): raise ValueError('encrypted store root must be an object')
        return value
