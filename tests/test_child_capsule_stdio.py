"""Binary pipe operations delegate to the existing inert core on Windows and Linux."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from cgc.experimental import capsule_stdio as cli,capsule,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_chunks import large_state


class CapsuleStdioTests(unittest.TestCase):
    def invoke(self,mode,raw,*extra):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        return subprocess.run([sys.executable,'-B','-m','cgc.experimental.capsule_stdio',mode,*extra],
                              input=raw,capture_output=True,env=env,timeout=5)

    def test_both_profiles_owned_process_roundtrip(self):
        for value in (state(),large_state()):
            raw=profiles.encode(value);archive=capsule.export_capsule(value)
            exported=self.invoke('export',raw)
            self.assertEqual((exported.returncode,exported.stdout,exported.stderr),(0,archive,b''))
            imported=self.invoke('import',archive)
            self.assertEqual((imported.returncode,imported.stdout,imported.stderr),(0,raw,b''))
            inspected=self.invoke('inspect',archive)
            self.assertEqual((inspected.returncode,inspected.stderr),(0,b''))
            report=json.loads(inspected.stdout)
            self.assertEqual(report['capsule_sha256'],hashlib.sha256(archive).hexdigest())
            self.assertEqual(report['snapshot_digest'],profiles.digest(value))
            self.assertEqual(report['profile'],profiles.kind(value))
            self.assertEqual(report['authority'],'NONE')
            self.assertEqual(report['freshness'],'HISTORICAL_UNVERIFIED')
            self.assertEqual(report['current_safe_to_resume'],'UNKNOWN')
            for key in ('mutation_authorized','source_authenticated','extraction_performed'):self.assertIs(report[key],False)
            self.assertNotIn('source_state',report)

    def test_no_paths_extraction_or_execution(self):
        raw=profiles.encode(state());archive=capsule.export_capsule(state())
        with patch('builtins.open',side_effect=AssertionError('path')),patch('subprocess.Popen',side_effect=AssertionError('execute')),\
             patch('zipfile.ZipFile.extract',side_effect=AssertionError('extract')),patch('zipfile.ZipFile.extractall',side_effect=AssertionError('extract')):
            self.assertEqual(cli.transform('export',raw),archive)
            self.assertEqual(cli.transform('import',archive),raw)
            self.assertIn(b'"authority":"NONE"',cli.transform('inspect',archive))

    def test_invalid_archive_and_snapshot_no_output(self):
        archive=capsule.export_capsule(state());raw=profiles.encode(state())
        cases=[('import',b''),('inspect',b'prefix'+archive),('import',archive+b'trailer'),
               ('inspect',archive[:-1]),('export',raw+b' '),('export',raw.replace(b'"version":',b'"version":0,"version":')),
               ('export',archive),('import',raw),('inspect',b'PRIVATE_INPUT_SENTINEL')]
        for mode,data in cases:
            out=io.BytesIO();self.assertEqual(cli.serve(mode,io.BytesIO(data),out),2);self.assertEqual(out.getvalue(),b'')
            run=self.invoke(mode,data)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(2,b'',cli.ERROR))

    def test_fixed_modes_and_argument_refusal(self):
        for mode,extra in [('execute',()),('export',('target.zip',)),('import',('--extract',)),('../path',())]:
            run=self.invoke(mode,b'PRIVATE_INPUT_SENTINEL',*extra)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(2,b'',cli.ERROR))
        class NoRead:
            def read(self,_):raise AssertionError('read invalid mode')
        self.assertEqual(cli.serve('execute',NoRead(),io.BytesIO()),2)

    def test_bounds_and_short_output_refusal(self):
        for mode in cli.MODES:
            bound=profiles.MAX_BYTES if mode=='export' else capsule.MAX_BYTES
            source=io.BytesIO(b'x'*(bound+2));out=io.BytesIO()
            self.assertEqual(cli.serve(mode,source,out),2)
            self.assertEqual(source.tell(),bound+1);self.assertEqual(out.getvalue(),b'')
        class Short:
            def write(self,raw):return len(raw)-1
            def flush(self):raise AssertionError('flush incomplete output')
        self.assertEqual(cli.serve('export',io.BytesIO(profiles.encode(state())),Short()),2)
        class Failed:
            def read(self,_):raise OSError('PRIVATE_IO_DETAIL')
        self.assertEqual(cli.serve('export',Failed(),io.BytesIO()),2)


if __name__=='__main__':unittest.main()
