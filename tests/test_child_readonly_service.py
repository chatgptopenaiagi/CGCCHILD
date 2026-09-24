import base64
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from cgc.experimental import readonly_service as svc,state_protocol as sp,capsule
from test_child_state_protocol import state


def request(method='state.get',**changes):
    value=dict(id='req-1',method=method,snapshot_digest=sp.digest(state()))
    value.update(changes)
    return (json.dumps(value,separators=(',',':'))+'\n').encode('ascii')


class ChildReadOnlyServiceTests(unittest.TestCase):
    def test_core_all_methods_same_snapshot(self):
        core=svc.ReadOnlyCore(sp.encode(state()))
        outputs={m:json.loads(core.dispatch(request(m))) for m in svc.METHODS}
        for out in outputs.values():
            self.assertEqual(out['snapshot_digest'],sp.digest(state()))
            self.assertFalse(out['mutation_authorized'])
        self.assertEqual(outputs['state.get']['result'],state())
        self.assertEqual(outputs['status.get']['result']['text'],sp.render_human(state()))
        raw=base64.b64decode(outputs['capsule.export']['result']['capsule'],validate=True)
        self.assertEqual(capsule.import_capsule(raw).snapshot(),state())

    def test_unknown_methods_params_and_replay_refuse(self):
        core=svc.ReadOnlyCore(sp.encode(state()))
        for changes in ({'method':'execute'},{'method':'shell'},{'path':'/etc/shadow'},
                        {'id':True},{'method':['state.get']},{'snapshot_digest':'YES'}):
            self.assertEqual(json.loads(core.dispatch(request(**changes)))['error'],'INVALID_REQUEST')
        self.assertEqual(json.loads(core.dispatch(request(snapshot_digest='0'*64)))['error'],'STALE_SNAPSHOT')

    def test_malformed_duplicate_oversize_and_unicode(self):
        core=svc.ReadOnlyCore(sp.encode(state()))
        for raw in (b'{}',b'x'*1025,b'\xff\n',request().replace(b'"id":',b'"id":"evil","id":'),b'['*1000+b'\n'):
            self.assertEqual(json.loads(core.dispatch(raw))['error'],'INVALID_REQUEST')

    def test_stream_limits_and_no_rebind(self):
        out=io.BytesIO()
        source=io.BytesIO(sp.encode(state())+request()*40)
        self.assertEqual(svc.serve(source,out),0)
        self.assertEqual(len(out.getvalue().splitlines()),32)
        self.assertTrue(source.read())
        out=io.BytesIO()
        self.assertEqual(svc.serve(io.BytesIO(b'bad\n'+request()),out),2)
        self.assertEqual(len(out.getvalue().splitlines()),1)
        self.assertNotIn(b'bad',out.getvalue())

    def test_process_stdio_only(self):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        run=subprocess.run([sys.executable,'-B','-m','cgc.experimental.readonly_service'],
                           input=sp.encode(state())+request('status.get'),capture_output=True,env=env,timeout=5)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(run.stderr,b'')
        self.assertIn('UNKNOWN',json.loads(run.stdout)['result']['text'])


if __name__=='__main__':unittest.main()
