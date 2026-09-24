"""Independent fixed Node client against the owned Python MCP adapter."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from cgc.experimental import state_protocol as sp,mcp_stdio as mcp
from test_child_state_protocol import state
from test_child_mcp import init,req


@unittest.skipUnless(shutil.which('node'),'Node absent; paired client interoperability unavailable')
class ChildMCPClientTests(unittest.TestCase):
    def test_owned_node_python_sessions(self):
        root=Path(__file__).resolve().parents[1]
        values=[state(),state()];values[1]['model']['project']='independent-node-model'
        for value in values:
            run=subprocess.run(['node',str(root/'sdk/javascript/mcp_owned_process.mjs'),sys.executable],
                               input=sp.encode(value),capture_output=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(run.stderr,b'')
            self.assertEqual(json.loads(run.stdout),dict(status='PAIRED_TRANSCRIPT_MATCH',responses=5,
                authority='NONE',snapshot_digest=sp.digest(value),freshness='HISTORICAL_UNVERIFIED',
                requests=6,owned_process_exit=0))

    def test_node_lifecycle_bounds_and_ownership(self):
        root=Path(__file__).resolve().parents[1]
        run=subprocess.run(['node',str(root/'sdk/javascript/test_mcp_conformance_client.mjs')],capture_output=True,timeout=10)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout),dict(status='PASS',cases=19))

    def test_fixed_fault_responders_close_owned_process(self):
        root=Path(__file__).resolve().parents[1]
        expected={
            'MALFORMED':{'PROTOCOL'},'OVERSIZE':{'FRAME_LIMIT'},
            'TRUNCATED':{'EOF','EARLY_CLOSE'},'STDERR':{'STDERR','EOF','EARLY_CLOSE'},
            'SILENT':{'TIMEOUT'},'EXTRA_FRAME':{'FRAME_EXTRA','PROTOCOL','UNEXPECTED_DATA'},
            'EARLY_EXIT':{'EOF','EARLY_CLOSE'}}
        for mode,reasons in expected.items():
            with self.subTest(mode=mode):
                run=subprocess.run(['node',str(root/'sdk/javascript/mcp_owned_process.mjs'),sys.executable,mode],
                    input=sp.encode(state()),capture_output=True,timeout=15)
                self.assertEqual(run.returncode,2,run.stderr);self.assertEqual(run.stderr,b'')
                report=json.loads(run.stdout)
                self.assertEqual(set(report),{'status','reason','mode','owned_process_closed','authority'})
                self.assertEqual(report['status'],'OWNED_TRANSPORT_REFUSED')
                self.assertEqual(report['mode'],mode);self.assertIn(report['reason'],reasons)
                self.assertTrue(report['owned_process_closed']);self.assertEqual(report['authority'],'NONE')

    def transcript(self):
        value=state();adapter=mcp.MCPAdapter(sp.encode(value));frames=[adapter.handle(init())]
        adapter.handle(req('notifications/initialized',identifier=None))
        for number,name in enumerate(('cgcchild_capabilities','cgcchild_state','cgcchild_status','cgcchild_capsule'),2):
            frames.append(adapter.handle(req('tools/call',{'name':name,'arguments':{'snapshot_digest':sp.digest(value)}},identifier=number)))
        return frames

    def test_response_mutations_and_terminal_refusal(self):
        frames=self.transcript();cases=[frames]
        for index,frame in enumerate(frames):
            for changed in (frame[:-1],b' '+frame,frame+b'x',frame+frame,b'{}\n',b'\xff\n',
                            frame.replace(b'"id":',b'"id":999,"id":',1)):
                row=frames.copy();row[index]=changed;cases.append(row)
        def changed(index,transform):
            row=frames.copy();obj=json.loads(row[index]);transform(obj);row[index]=mcp.wire(obj);cases.append(row)
        changed(0,lambda o:o['result'].update(protocolVersion='unknown'))
        changed(0,lambda o:o['result']['capabilities']['tools'].update(listChanged=True))
        changed(1,lambda o:o['result']['structuredContent'].update(mutation_authorized=True))
        changed(1,lambda o:o['result']['content'][0].update(text='different'))
        changed(2,lambda o:o.update(id=1))
        changed(3,lambda o:o['result'].update(isError=True))
        cases.extend([frames[:-1],frames+[frames[-1]],[mcp.error(1,-32603,'Error')]+frames[1:]])
        root=Path(__file__).resolve().parents[1]
        payload=json.dumps(dict(snapshot=sp.encode(state()).hex(),cases=[[f.hex() for f in row] for row in cases])).encode()
        self.assertLessEqual(len(payload),2*1024*1024)
        run=subprocess.run(['node',str(root/'sdk/javascript/mcp_client_vectors.mjs')],input=payload,capture_output=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stderr,b'')
        rows=json.loads(run.stdout);self.assertTrue(rows[0]['accepted'])
        self.assertEqual(rows[0]['authority'],'NONE')
        self.assertEqual(len(rows),45)
        self.assertTrue(all(r==dict(accepted=False,terminal=True) for r in rows[1:]))


if __name__=='__main__':unittest.main()
