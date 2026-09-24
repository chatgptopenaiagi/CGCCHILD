"""Experimental, version-pinned read-only MCP adapter. No host integrations.

Only the 2025-11-25 initialize/tools/ping subset is implemented. The state is an
explicit startup byte string, never a path, live collector or reusable grant.
"""
import json
import sys
from . import snapshot_profiles as sp
from .readonly_service import ReadOnlyCore

PROTOCOL = '2025-11-25'
MAX_FRAME = 8192
MAX_MESSAGES = 64
MAX_RESPONSE = 96*1024
TOOLS = {'cgcchild_capabilities':'capabilities.get','cgcchild_state':'state.get',
         'cgcchild_status':'status.get','cgcchild_capsule':'capsule.export'}


def wire(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\n').encode('ascii')


def error(identifier,code,message):
    return wire({'jsonrpc':'2.0','id':identifier,'error':{'code':code,'message':message}})


class MCPAdapter:
    def __init__(self, snapshot_bytes):
        self.core=ReadOnlyCore(snapshot_bytes)
        self.digest=sp.digest(sp.decode(snapshot_bytes))
        self.phase='NEW'

    def handle(self,raw):
        def pairs(items):
            out={}
            for k,v in items:
                if k in out:raise ValueError()
                out[k]=v
            return out
        try:
            if type(raw) is not bytes or not 1<=len(raw)<=MAX_FRAME or not raw.endswith(b'\n'):
                raise ValueError()
            r=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        except (ValueError,UnicodeError,RecursionError):return error(None,-32700,'Parse error')
        if type(r) is not dict or r.get('jsonrpc')!='2.0' or type(r.get('method')) is not str or set(r)-{'jsonrpc','id','method','params'}:
            return error(None,-32600,'Invalid Request')
        method=r['method'];params=r.get('params',{})
        if 'id' not in r:
            if method=='notifications/initialized' and self.phase=='INITIALIZING' and params=={}:
                self.phase='READY'
            elif method=='notifications/initialized':self.phase='INVALIDATED'
            # Notifications never receive replies. Unknown notifications cannot
            # grant capabilities, bind a snapshot or change core data.
            return None
        identifier=r['id']
        if not (type(identifier) is int and -(2**53-1)<=identifier<=2**53-1 or
                type(identifier) is str and 1<=len(identifier)<=64 and identifier.isascii()
                and all(32<=ord(c)<127 for c in identifier)):
            return error(None,-32600,'Invalid Request')
        if type(params) is not dict:return error(identifier,-32602,'Invalid params')
        result=None
        if method=='ping' and params=={}:result={}
        elif method=='initialize':
            if self.phase!='NEW':return error(identifier,-32600,'Already initialized')
            if set(params)!={'protocolVersion','capabilities','clientInfo'}:
                return error(identifier,-32602,'Invalid params')
            info=params['clientInfo']
            if (type(params['protocolVersion']) is not str or len(params['protocolVersion'])>32
                    or type(params['capabilities']) is not dict or type(info) is not dict
                    or any(type(info.get(k)) is not str or not 1<=len(info[k])<=128 for k in ('name','version'))):
                return error(identifier,-32602,'Invalid params')
            self.phase='INITIALIZING'
            result={'protocolVersion':PROTOCOL,'capabilities':{'tools':{'listChanged':False}},
                    'serverInfo':{'name':'cgcchild-experimental-readonly','version':'0.1.0'}}
        elif self.phase!='READY':return error(identifier,-32600,'Not initialized')
        elif method=='tools/list':
            if params:return error(identifier,-32602,'Invalid params')
            result={'tools':[{'name':name,'description':'Historical snapshot; no live proof or mutation authority.',
                'inputSchema':{'type':'object','properties':{'snapshot_digest':{'type':'string','const':self.digest}},
                               'required':['snapshot_digest'],'additionalProperties':False},
                'annotations':{'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}}
                for name in sorted(TOOLS)]}
        elif method=='tools/call':
            if set(params)!={'name','arguments'} or type(params['name']) is not str or params['name'] not in TOOLS:
                return error(identifier,-32602,'Invalid params')
            arguments=params['arguments']
            if type(arguments) is not dict or set(arguments)!={'snapshot_digest'}:
                return error(identifier,-32602,'Invalid params')
            raw_result=self.core.dispatch(wire({'id':'mcp','method':TOOLS[params['name']],
                                               'snapshot_digest':arguments['snapshot_digest']}))
            value=json.loads(raw_result)
            result={'content':[{'type':'text','text':raw_result.decode('ascii').rstrip('\n')}],
                    'structuredContent':value,'isError':'error' in value}
        else:return error(identifier,-32601,'Method not found')
        response=wire({'jsonrpc':'2.0','id':identifier,'result':result})
        if len(response)>MAX_RESPONSE:return error(identifier,-32603,'Response limit')
        return response


def serve(snapshot_bytes,source,destination):
    adapter=MCPAdapter(snapshot_bytes)
    for _ in range(MAX_MESSAGES):
        raw=source.readline(MAX_FRAME+1)
        if not raw:return 0
        result=adapter.handle(raw)
        if result is not None:destination.write(result);destination.flush()
        if len(raw)>MAX_FRAME or not raw.endswith(b'\n'):return 2
    return 0


def main():
    # Hex carries only an already-reviewed inert model snapshot. No file opening,
    # environment lookup, command execution or arbitrary startup selector.
    if len(sys.argv)!=3 or sys.argv[1]!='--snapshot-hex' or len(sys.argv[2])>sp.MAX_BYTES*2:return 2
    try:
        data=bytes.fromhex(sys.argv[2])
        return serve(data,sys.stdin.buffer,sys.stdout.buffer)
    except (ValueError,OSError):return 2


if __name__=='__main__':raise SystemExit(main())
