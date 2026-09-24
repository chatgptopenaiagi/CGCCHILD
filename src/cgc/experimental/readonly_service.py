"""Bounded read-only core dispatcher and private stdio reference transport.

Not MCP/JSON-RPC, not a daemon. No sockets, paths, commands or mutation methods.
First stdin line is a canonical state snapshot; subsequent lines are requests.
"""
import base64
import json
import re
import sys
from . import snapshot_profiles as sp
from .capsule import export_capsule
from .capsule_chunks import chunk,ChunkError

METHODS = ('capabilities.get','state.get','status.get','capsule.export','capsule.chunk')
MAX_REQUEST = 1024
MAX_RESPONSE = 96*1024
MAX_REQUESTS = 128


def _wire(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')


def _error(code):
    return _wire({'version':'cgcchild-readonly-0.1','error':code,'mutation_authorized':False})


class ReadOnlyCore:
    def __init__(self, snapshot_bytes):
        state=sp.decode(snapshot_bytes)
        self._bytes=sp.encode(state)
        self._digest=sp.digest(state)

    def dispatch(self, raw):
        def pairs(items):
            out={}
            for k,v in items:
                if k in out:raise ValueError()
                out[k]=v
            return out
        try:
            if type(raw) is not bytes or not 1<=len(raw)<=MAX_REQUEST or not raw.endswith(b'\n'):
                raise ValueError()
            request=json.loads(raw.decode('ascii'),object_pairs_hook=pairs)
            if type(request) is not dict:
                raise ValueError()
            expected={'id','method','snapshot_digest'}
            if request.get('method')=='capsule.chunk':expected.add('offset')
            if set(request)!=expected:
                raise ValueError()
            if type(request['id']) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}',request['id']):
                raise ValueError()
            if type(request['method']) is not str or request['method'] not in METHODS:
                raise ValueError()
            if type(request['snapshot_digest']) is not str or not re.fullmatch(r'[0-9a-f]{64}',request['snapshot_digest']):
                raise ValueError()
        except (ValueError,UnicodeError,RecursionError):
            return _error('INVALID_REQUEST')
        if request['snapshot_digest']!=self._digest:
            return _error('STALE_SNAPSHOT')
        method=request['method']
        state=sp.decode(self._bytes)
        if method=='capabilities.get':
            result={'methods':list(METHODS),'profile':sp.kind(state),'network':False,
                    'freshness':'HISTORICAL_UNVERIFIED','max_requests':MAX_REQUESTS}
        elif method=='state.get':result=state
        elif method=='status.get':result={'text':sp.render_human(state)}
        elif method=='capsule.export':result={'encoding':'base64','capsule':base64.b64encode(export_capsule(state)).decode('ascii')}
        else:
            try:result=chunk(state,request['offset'])
            except ChunkError:return _error('CHUNK_RANGE')
        response=_wire({'version':'cgcchild-readonly-0.1','id':request['id'],
                        'snapshot_digest':self._digest,'result':result,'mutation_authorized':False})
        if len(response)>MAX_RESPONSE:return _error('RESPONSE_LIMIT')
        return response


def serve(source, destination):
    """Binary streams only. Bounded records, no reopen/rebind or filesystem APIs.

    The caller owns wall-clock timeout and pipe lifecycle; no timeout guarantee is
    implied by a blocking stream read. EOF ends this foreground process.
    """
    raw=source.readline(sp.MAX_BYTES+1)
    try:core=ReadOnlyCore(raw)
    except sp.ProfileError:
        destination.write(_error('INVALID_SNAPSHOT'));destination.flush();return 2
    for _ in range(MAX_REQUESTS):
        line=source.readline(MAX_REQUEST+1)
        if not line:return 0
        response=core.dispatch(line)
        destination.write(response);destination.flush()
        if len(line)>MAX_REQUEST or not line.endswith(b'\n'):return 2
    return 0


def main():
    if len(sys.argv)!=1:return 2
    try:return serve(sys.stdin.buffer,sys.stdout.buffer)
    except (BrokenPipeError,OSError):return 2


if __name__=='__main__':raise SystemExit(main())
