"""Bounded trusted-process read router, not authentication or remote agent fabric.

Owner registration/issuance are direct local operations. Serialized route labels never
carry grants. No listener, callback, target path, executor or grant import exists.
"""
import json
import re
from .read_capabilities import ReadCapabilityLab,ReadDenied
from .snapshot_profiles import MAX_BYTES as MAX_SNAPSHOT_BYTES
VERSION='cgcchild-read-route-0.1-experimental'
MAX_ROUTES=8
MAX_HANDLES=128
MAX_CALLS=256
MAX_REQUEST=1024


class RouteDenied(RuntimeError):
    def __init__(self):super().__init__('READ_ROUTE_DENIED')


class RoutedGrant:
    __slots__=()


def _name(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}',value):raise RouteDenied()


def _wire(value):return (json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False)+'\n').encode('ascii')


def _request(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=MAX_REQUEST:raise RouteDenied()
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise RouteDenied()
            out[k]=v
        return out
    def invalid(_):raise RouteDenied()
    try:
        value=json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=invalid)
        if type(value) is not dict:raise RouteDenied()
        fields={'version','route','method','snapshot_digest'}
        if value.get('method')=='capsule.chunk':fields.add('offset')
        if set(value)!=fields or value['version']!=VERSION or _wire(value)!=raw:raise RouteDenied()
        _name(value['route'])
        if type(value['method']) is not str or type(value['snapshot_digest']) is not str:raise RouteDenied()
        return value
    except (ValueError,UnicodeError,TypeError,RecursionError,OverflowError):raise RouteDenied() from None


class ReadRouter:
    def __init__(self):
        self._routes={};self._handles={};self._closed=False;self._calls=0;self._last_ns=None

    def _at(self,now_ns):
        if self._closed or self._calls>=MAX_CALLS:raise RouteDenied()
        self._calls+=1
        if type(now_ns) is not int or not 0<=now_ns<1<<63:raise RouteDenied()
        if self._last_ns is not None and now_ns<self._last_ns:
            self.close();raise RouteDenied()
        self._last_ns=now_ns

    def register(self,route,snapshot_bytes,*,now_ns):
        self._at(now_ns);_name(route)
        if route in self._routes or len(self._routes)>=MAX_ROUTES:raise RouteDenied()
        if type(snapshot_bytes) is not bytes or not 1<=len(snapshot_bytes)<=MAX_SNAPSHOT_BYTES:raise RouteDenied()
        try:lab=ReadCapabilityLab(snapshot_bytes)
        except (ValueError,RuntimeError):raise RouteDenied() from None
        self._routes[route]=lab

    def issue(self,route,principal,methods,*,now_ns,expires_ns):
        self._at(now_ns);_name(route)
        if route not in self._routes or len(self._handles)>=MAX_HANDLES:raise RouteDenied()
        try:grant=self._routes[route].issue(principal,methods,now_ns=now_ns,expires_ns=expires_ns)
        except ReadDenied:raise RouteDenied() from None
        handle=RoutedGrant();self._handles[handle]=(route,grant);return handle

    def dispatch(self,handle,principal,raw,*,now_ns):
        self._at(now_ns)
        binding=self._handles.get(handle) if type(handle) is RoutedGrant else None
        if binding is None:raise RouteDenied()
        request=_request(raw);route,grant=binding
        if request['route']!=route:raise RouteDenied()
        lab=self._routes.get(route)
        if lab is None:raise RouteDenied()
        try:
            if request['method']=='capsule.chunk':return lab.read_chunk(grant,principal,request['offset'],now_ns=now_ns,snapshot_digest=request['snapshot_digest'])
            return lab.read(grant,principal,request['method'],now_ns=now_ns,snapshot_digest=request['snapshot_digest'])
        except ReadDenied:raise RouteDenied() from None

    def revoke(self,handle,*,now_ns):
        self._at(now_ns)
        binding=self._handles.pop(handle,None) if type(handle) is RoutedGrant else None
        if binding is None:raise RouteDenied()
        route,grant=binding
        try:self._routes[route].revoke(grant,now_ns=now_ns)
        except ReadDenied:raise RouteDenied() from None

    def events(self,route):
        _name(route)
        if self._closed or route not in self._routes:raise RouteDenied()
        return self._routes[route].events()

    def close(self):
        self._closed=True;self._handles.clear();self._routes.clear()
