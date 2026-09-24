import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from cgc.experimental import mcp_stdio as mcp,state_protocol as sp
from test_child_state_protocol import state


def req(method,params=None,identifier=1):
    value={'jsonrpc':'2.0','method':method}
    if identifier is not None:value['id']=identifier
    if params is not None:value['params']=params
    return mcp.wire(value)


def init():return req('initialize',{'protocolVersion':mcp.PROTOCOL,'capabilities':{},'clientInfo':{'name':'owned-test','version':'1'}})


class ChildMCPTests(unittest.TestCase):
    def ready(self):
        a=mcp.MCPAdapter(sp.encode(state()))
        self.assertEqual(json.loads(a.handle(init()))['result']['protocolVersion'],mcp.PROTOCOL)
        self.assertIsNone(a.handle(req('notifications/initialized',identifier=None)))
        return a

    def test_lifecycle_and_all_tools(self):
        a=self.ready();listed=json.loads(a.handle(req('tools/list')))['result']['tools']
        self.assertEqual([x['name'] for x in listed],sorted(mcp.TOOLS))
        for tool in listed:
            self.assertTrue(tool['annotations']['readOnlyHint'])
            arguments={'snapshot_digest':sp.digest(state())}
            if tool['name']=='cgcchild_capsule_chunk':arguments['offset']=0
            result=json.loads(a.handle(req('tools/call',{'name':tool['name'],'arguments':arguments})))['result']
            self.assertFalse(result['isError'])
            self.assertFalse(result['structuredContent']['mutation_authorized'])
            self.assertEqual(json.loads(result['content'][0]['text']),result['structuredContent'])

    def test_no_tools_before_initialized_and_no_reinit(self):
        a=mcp.MCPAdapter(sp.encode(state()))
        self.assertIn('error',json.loads(a.handle(req('tools/list'))))
        a.handle(init())
        self.assertIn('error',json.loads(a.handle(req('tools/list'))))
        self.assertIn('error',json.loads(a.handle(init())))
        a.handle(req('notifications/initialized',identifier=None))
        a.handle(req('notifications/initialized',identifier=None))
        self.assertIn('error',json.loads(a.handle(req('tools/list'))))

    def test_invalid_mutation_and_parameters(self):
        a=self.ready()
        for raw in (req('execute'),req('tools/call',{'name':'shell','arguments':{}}),
                    req('tools/call',{'name':'cgcchild_state','arguments':{'path':'secret'}}),
                    req('tools/list',{'cursor':'unknown'}),req('ping',identifier=True),b'[]\n',b'\xff\n',
                    init().replace(b'"id":',b'"id":2,"id":')):
            self.assertIn('error',json.loads(a.handle(raw)))
        self.assertIsNone(a.handle(req('unknown-notification',identifier=None)))

    def test_stale_digest_is_tool_error(self):
        result=json.loads(self.ready().handle(req('tools/call',{'name':'cgcchild_state','arguments':{'snapshot_digest':'0'*64}})))['result']
        self.assertTrue(result['isError'])
        self.assertEqual(result['structuredContent']['error'],'STALE_SNAPSHOT')

    def test_version_negotiation_and_ping(self):
        a=mcp.MCPAdapter(sp.encode(state()))
        self.assertEqual(json.loads(a.handle(req('ping')))['result'],{})
        value=json.loads(init());value['params']['protocolVersion']='unknown-future'
        self.assertEqual(json.loads(a.handle(mcp.wire(value)))['result']['protocolVersion'],mcp.PROTOCOL)

    def test_actual_stdio_process(self):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        run=subprocess.run([sys.executable,'-B','-m','cgc.experimental.mcp_stdio','--snapshot-hex',sp.encode(state()).hex()],
            input=init()+req('notifications/initialized',identifier=None)+req('tools/list',identifier=2),
            capture_output=True,env=env,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(run.stderr,b'')
        responses=[json.loads(x) for x in run.stdout.splitlines()]
        self.assertEqual(len(responses),2)
        self.assertEqual(responses[1]['id'],2)
        self.assertEqual(len(responses[1]['result']['tools']),len(mcp.TOOLS))

    def test_frame_and_session_bounds(self):
        source=io.BytesIO(init()+req('notifications/initialized',identifier=None)+req('ping')*(mcp.MAX_MESSAGES+8))
        out=io.BytesIO()
        self.assertEqual(mcp.serve(sp.encode(state()),source,out),0)
        self.assertEqual(len(out.getvalue().splitlines()),mcp.MAX_MESSAGES-1)
        self.assertTrue(source.read())
        out=io.BytesIO()
        self.assertEqual(mcp.serve(sp.encode(state()),io.BytesIO(b'x'*8193),out),2)
        self.assertEqual(json.loads(out.getvalue())['error']['code'],-32700)


if __name__=='__main__':unittest.main()
