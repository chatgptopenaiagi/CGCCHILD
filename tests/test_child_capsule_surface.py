"""Hostile imported archives remain inert historical status, never extracted."""
import io
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest
from unittest.mock import patch
import zipfile
from cgc.experimental import capsule,offline_surface as surface,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_chunks import large_state
import test_child_capsule as capsule_tests


class ChildCapsuleSurfaceTests(unittest.TestCase):
    def invoke(self,raw,args=('--capsule-stdin',)):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        return subprocess.run([sys.executable,'-B','-m','cgc.experimental.offline_surface',*args],
            input=raw,capture_output=True,env=env,timeout=5)

    def test_both_profiles_identical_surface_without_effects(self):
        for value in (state(),large_state()):
            raw=capsule.export_capsule(value)
            expected=surface.render_html(profiles.encode(value))
            with patch('builtins.open',side_effect=AssertionError('path access')),\
                 patch('zipfile.ZipFile.extract',side_effect=AssertionError('extraction')),\
                 patch('zipfile.ZipFile.extractall',side_effect=AssertionError('extraction')),\
                 patch('subprocess.Popen',side_effect=AssertionError('execution')):
                html=surface.render_capsule(raw)
            self.assertEqual(html,expected)
            self.assertIn(b'Mutation authority<strong>NONE',html)
            self.assertIn(b'Filesystem / P3<strong>UNKNOWN',html)
            self.assertIn(b'HISTORICAL_UNVERIFIED',html)
            run=self.invoke(raw)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(0,expected,b''))

    def test_hostile_archive_never_reaches_renderer(self):
        raw=capsule.export_capsule(state())
        cases=[b'',b'prefix'+raw,raw+b'trailer',raw[:-1],b'x'*(capsule.MAX_BYTES+1)]
        def altered(field,value):
            def change(info,data):
                if info.filename=='state.json':setattr(info,field,value)
                return info,data
            return capsule_tests.ChildCapsuleTests().rewrite(change)
        cases.extend([altered('filename','../state.json'),altered('filename','C:\\owned.txt'),
                      altered('external_attr',(stat.S_IFLNK|0o777)<<16),
                      altered('compress_type',zipfile.ZIP_DEFLATED)])
        def human_markup(info,data):
            return info,b'<script>owned</script>' if info.filename=='HUMAN-STATUS.txt' else data
        cases.append(capsule_tests.ChildCapsuleTests().rewrite(human_markup))
        for raw in cases:
            with self.subTest(length=len(raw)),patch.object(surface,'render_html') as render:
                with self.assertRaises(capsule.CapsuleError):surface.render_capsule(raw)
                render.assert_not_called()
        for raw in cases[1:4]+cases[5:]:
            run=self.invoke(raw)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(2,b'',b''))

    def test_explicit_mode_no_sniffing_paths_or_extra_options(self):
        state_bytes=profiles.encode(state());raw=capsule.export_capsule(state())
        for data,args in ((raw,()),(state_bytes,('--capsule-stdin',)),
                          (raw,('--capsule-stdin','file.zip')),
                          (raw,('--capsule-stdin','--refresh'))):
            run=self.invoke(data,args)
            self.assertEqual((run.returncode,run.stdout,run.stderr),(2,b'',b''))

    def test_read_bound_and_no_partial_output_on_refusal(self):
        source=io.BytesIO(b'x'*(capsule.MAX_BYTES+2));destination=io.BytesIO()
        class Stream:
            def __init__(self,buffer):self.buffer=buffer
        with patch.object(sys,'argv',['surface','--capsule-stdin']),\
             patch.object(sys,'stdin',Stream(source)),patch.object(sys,'stdout',Stream(destination)):
            self.assertEqual(surface.main(),2)
        self.assertEqual(source.tell(),capsule.MAX_BYTES+1)
        self.assertEqual(destination.getvalue(),b'')


if __name__=='__main__':unittest.main()
