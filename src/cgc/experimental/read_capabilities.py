"""In-process read-capability laboratory, not an authenticated agent fabric.

Only owner-created opaque handles can read one historical snapshot through the
existing core. No serialization/import of grants and no mutation adapter exist.
The caller supplies an already-authenticated principal in any future integration;
this module does not authenticate a principal label or protect hostile Python code.
"""
from dataclasses import dataclass
import hashlib
import json
import re
from .readonly_service import ReadOnlyCore,METHODS
from . import snapshot_profiles as sp
from .capsule_chunks import CHUNK_BYTES
from .capsule import MAX_BYTES as MAX_CAPSULE_BYTES

MAX_GRANTS=16
MAX_EVENTS=64
MAX_TTL_NS=60_000_000_000
READ_METHODS=tuple(METHODS)


class ReadDenied(RuntimeError):
    def __init__(self):super().__init__('READ_DENIED')


class GrantHandle:
    __slots__=()


@dataclass(frozen=True)
class _Grant:
    principal: str
    methods: tuple
    issued_ns: int
    expires_ns: int


def _clock(value):
    if type(value) is not int or not 0<=value<1<<63:raise ReadDenied()


def _principal(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value):raise ReadDenied()


class ReadCapabilityLab:
    def __init__(self,snapshot_bytes):
        self._core=ReadOnlyCore(snapshot_bytes)
        self._digest=sp.digest(sp.decode(snapshot_bytes))
        self._grants={}
        self._events=[]
        self._closed=False
        self._last_ns=None

    def _at(self,now_ns):
        _clock(now_ns)
        if self._closed or len(self._events)>=MAX_EVENTS:raise ReadDenied()
        if self._last_ns is not None and now_ns<self._last_ns:
            self._closed=True;self._grants.clear();raise ReadDenied()
        self._last_ns=now_ns

    def _event(self,kind,now_ns):
        previous=self._events[-1]['digest'] if self._events else '0'*64
        event=dict(version='cgcchild-read-events-0.1',sequence=len(self._events)+1,
                   kind=kind,observed_ns=str(now_ns),snapshot_digest=self._digest,previous=previous)
        digest=hashlib.sha256(json.dumps(event,sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()
        self._events.append(dict(event,digest=digest))

    def issue(self,principal,methods,*,now_ns,expires_ns):
        """Explicit local owner operation; not exposed by service, MCP or plugin."""
        self._at(now_ns);_clock(expires_ns);_principal(principal)
        if (type(methods) is not tuple or not methods or len(methods)>len(READ_METHODS)
                or any(type(x) is not str or x not in READ_METHODS for x in methods)
                or len(set(methods))!=len(methods) or len(self._grants)>=MAX_GRANTS
                or not now_ns<expires_ns<=now_ns+MAX_TTL_NS):raise ReadDenied()
        handle=GrantHandle()
        self._grants[handle]=_Grant(principal,tuple(sorted(methods)),now_ns,expires_ns)
        self._event('LOCAL_READ_HANDLE_ISSUED',now_ns)
        return handle

    def read(self,handle,principal,method,*,now_ns,snapshot_digest):
        return self._read(handle,principal,method,now_ns=now_ns,snapshot_digest=snapshot_digest,offset=None)

    def read_chunk(self,handle,principal,offset,*,now_ns,snapshot_digest):
        """One explicit bounded offset; each call consumes the existing event budget."""
        return self._read(handle,principal,'capsule.chunk',now_ns=now_ns,snapshot_digest=snapshot_digest,offset=offset)

    def _read(self,handle,principal,method,*,now_ns,snapshot_digest,offset):
        self._at(now_ns)
        grant=self._grants.get(handle) if type(handle) is GrantHandle else None
        if (grant is None or type(principal) is not str or type(method) is not str
                or type(snapshot_digest) is not str or principal!=grant.principal or method not in grant.methods
                or not grant.issued_ns<=now_ns<grant.expires_ns or snapshot_digest!=self._digest):
            self._event('READ_DENIED',now_ns);raise ReadDenied()
        # Only the fixed chunk operation accepts one bounded scalar offset.
        if method=='capsule.chunk' and (type(offset) is not int or not 0<=offset<MAX_CAPSULE_BYTES or offset%CHUNK_BYTES):
            self._event('READ_DENIED',now_ns);raise ReadDenied()
        request=dict(id='capability',method=method,snapshot_digest=self._digest)
        if method=='capsule.chunk':request['offset']=offset
        response=self._core.dispatch((json.dumps(request,separators=(',',':'))+'\n').encode('ascii'))
        self._event('CORE_REFUSED' if 'error' in json.loads(response) else 'READ_COMPLETE',now_ns)
        return response

    def revoke(self,handle,*,now_ns):
        self._at(now_ns)
        if type(handle) is not GrantHandle or handle not in self._grants:raise ReadDenied()
        del self._grants[handle]
        self._event('LOCAL_READ_HANDLE_REVOKED',now_ns)

    def invalidate(self,*,now_ns):
        self._at(now_ns)
        self._grants.clear();self._closed=True
        self._event('SNAPSHOT_INVALIDATED',now_ns)

    def events(self):
        # Independent copies, no grant identifier or authentication material.
        return tuple(dict(event) for event in self._events)
