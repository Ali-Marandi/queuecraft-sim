"""Bounded background execution contract for expensive QueueCraft jobs."""
from __future__ import annotations
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable
@dataclass(frozen=True)
class JobResult:
    status:str; elapsed_seconds:float; value:Any=None; error:str|None=None
class BoundedWorker:
    def __init__(self,max_workers:int=2):
        if max_workers<1: raise ValueError('max_workers must be positive')
        self._pool=ThreadPoolExecutor(max_workers=max_workers,thread_name_prefix='queuecraft-worker')
    def submit(self,fn:Callable[...,Any],*args:Any,**kwargs:Any)->Future[JobResult]:
        start=monotonic()
        def run()->JobResult:
            try: return JobResult('completed',monotonic()-start,value=fn(*args,**kwargs))
            except Exception as exc: return JobResult('failed',monotonic()-start,error=f'{type(exc).__name__}: {exc}')
        return self._pool.submit(run)
    def shutdown(self,wait:bool=True)->None: self._pool.shutdown(wait=wait)
