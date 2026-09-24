"""Explicit stdin snapshot bootstrap: no path lookup, argv-sized payload or rebind."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock,patch
from cgc.experimental import startup_snapshot as startup,snapshot_profiles as profiles,capsule,capsule_chunks as chunks
from test_child_state_protocol import state
from test_child_chunks import large_state
from test_child_mcp import init,req


class ChildStreamStartupTests(unittest.TestCase):
    def invoke(self,raw,digest,protocol=b''):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        return subprocess.run([sys.executable,'-B','-m','cgc.experimental.mcp_stdio',
            '--snapshot-stdin','--snapshot-digest',digest],input=raw+protocol,
            capture_output=True,env=env,timeout=10)

    def test_one_bounded_line_leaves_protocol(self):
        raw=profiles.encode(state());source=io.BytesIO(raw+b'next\n')
        with patch('builtins.open',side_effect=AssertionError('no path allowed')):
            self.assertEqual(startup.read_snapshot_line(source,hashlib.sha256(raw).hexdigest()),raw)
        self.assertEqual(source.read(),b'next\n')
        self.assertFalse(source.closed)

    def test_invalid_digest_does_not_consume_input(self):
        for digest in (None,True,'A'*64,'x'*64,'0'*63,'0'*64+'\n'):
            source=Mock()
            with self.subTest(digest=digest),self.assertRaises(startup.StartupError):
                startup.read_snapshot_line(source,digest)
            source.readline.assert_not_called()

    def test_content_bounds_canonicality_and_read_failure(self):
        raw=profiles.encode(state())
        for data in (b'',raw[:-1],raw[:-1]+b' \n',b'{}\n',b'\xff\n',b'x'*(profiles.MAX_BYTES+1)):
            source=Mock();source.readline.return_value=data
            with self.subTest(size=len(data)),self.assertRaises(startup.StartupError):
                startup.read_snapshot_line(source,hashlib.sha256(data).hexdigest())
            source.readline.assert_called_once_with(profiles.MAX_BYTES+1)
        source=io.BytesIO(raw)
        with self.assertRaises(startup.StartupError):startup.read_snapshot_line(source,'0'*64)
        self.assertFalse(source.closed)
        for side_effect,result in [(OSError('owned synthetic error'),None),(None,'not bytes')]:
            source=Mock();source.readline.side_effect=side_effect;source.readline.return_value=result
            with self.assertRaises(startup.StartupError):startup.read_snapshot_line(source,'0'*64)

    def test_large_actual_process_and_lossless_chunks(self):
        value=large_state();raw=profiles.encode(value);digest=profiles.digest(value)
        self.assertGreater(len(raw),100000)
        archive=capsule.export_capsule(value)
        protocol=init()+req('notifications/initialized',identifier=None)
        for i,offset in enumerate(range(0,len(archive),chunks.CHUNK_BYTES)):
            protocol+=req('tools/call',{'name':'cgcchild_capsule_chunk',
                          'arguments':{'snapshot_digest':digest,'offset':offset}},identifier=i+2)
        run=self.invoke(raw,digest,protocol)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(run.stderr,b'')
        responses=[json.loads(line) for line in run.stdout.splitlines()]
        receiver=chunks.Receiver(digest)
        for response in responses[1:]:
            self.assertFalse(response['result']['isError'])
            receiver.accept(response['result']['structuredContent']['result'])
        view=receiver.finish()
        self.assertEqual(view.snapshot(),value)
        self.assertEqual(view.authority,'NONE')

    def test_invalid_startup_emits_no_snapshot_or_protocol(self):
        raw=profiles.encode(state())
        for data,digest in ((raw,'0'*64),(b'{}\n',hashlib.sha256(b'{}\n').hexdigest()),
                            (raw[:-1],hashlib.sha256(raw[:-1]).hexdigest())):
            run=self.invoke(data,digest,init())
            self.assertEqual(run.returncode,2,run.stderr)
            self.assertEqual(run.stdout,b'');self.assertEqual(run.stderr,b'')

    def test_later_snapshot_cannot_rebind(self):
        value=state();raw=profiles.encode(value);digest=profiles.digest(value)
        other=state();other['model']['project']='different'
        protocol=init()+req('notifications/initialized',identifier=None)+profiles.encode(other)
        protocol+=req('tools/call',{'name':'cgcchild_state','arguments':{'snapshot_digest':digest}},identifier=2)
        run=self.invoke(raw,digest,protocol)
        self.assertEqual(run.returncode,0,run.stderr)
        responses=[json.loads(line) for line in run.stdout.splitlines()]
        self.assertIn('error',responses[1])
        self.assertEqual(responses[-1]['result']['structuredContent']['result'],value)


if __name__=='__main__':unittest.main()
