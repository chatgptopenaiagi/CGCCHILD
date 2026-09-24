import os
from pathlib import Path
import subprocess
import sys
from html.parser import HTMLParser
import unittest
from unittest.mock import patch
from cgc.experimental import offline_surface as surface,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_chunks import large_state


class Inspector(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))


class ChildSurfaceTests(unittest.TestCase):
    def test_both_profiles_deterministic_and_inert(self):
        for value in (state(),large_state()):
            raw=profiles.encode(value)
            with patch('builtins.open',side_effect=AssertionError('file')),patch('subprocess.Popen',side_effect=AssertionError('process')):
                html=surface.render_html(raw)
            self.assertEqual(html,surface.render_html(raw))
            self.assertLessEqual(len(html),surface.MAX_HTML)
            text=html.decode('utf-8');parser=Inspector();parser.feed(text)
            self.assertTrue(text.startswith('<!doctype html>'))
            self.assertIn(profiles.digest(value),text)
            self.assertIn('HISTORICAL_UNVERIFIED',text)
            self.assertIn('Current safety unknown',text)
            forbidden={'script','iframe','form','input','button','object','embed','link','img','a','base'}
            self.assertFalse(forbidden & {tag for tag,_ in parser.tags})
            self.assertFalse(any(k.startswith('on') or k in ('src','href','action') for _,attrs in parser.tags for k in attrs))
            policy=next(attrs['content'] for tag,attrs in parser.tags if attrs.get('http-equiv')=='Content-Security-Policy')
            self.assertIn("default-src 'none'",policy)
            self.assertIn("form-action 'none'",policy)
            self.assertNotIn("'unsafe-inline'",policy)
            if profiles.kind(value)==profiles.CONTINUITY:self.assertIn('Latest attempt: FAILED',text)

    def test_html_escaping_and_limit(self):
        raw=profiles.encode(state())
        with patch.object(profiles,'render_human',return_value='</pre><script>alert("x")</script>'):
            text=surface.render_html(raw).decode()
            self.assertNotIn('<script>',text)
            self.assertIn('&lt;script&gt;',text)
        with patch.object(profiles,'render_human',return_value='x'*surface.MAX_HTML):
            with self.assertRaisesRegex(ValueError,'SURFACE_LIMIT'):surface.render_html(raw)

    def test_actual_stdio_renderer_and_no_options(self):
        env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
        raw=profiles.encode(state())
        args=[sys.executable,'-B','-m','cgc.experimental.offline_surface']
        result=subprocess.run(args,input=raw,capture_output=True,env=env,timeout=5)
        self.assertEqual(result.returncode,0)
        self.assertEqual(result.stdout,surface.render_html(raw))
        self.assertEqual(result.stderr,b'')
        refused=subprocess.run(args+['--refresh'],input=raw,capture_output=True,env=env,timeout=5)
        self.assertEqual(refused.returncode,2)
        self.assertEqual(refused.stdout,b'')

    def test_invalid_profile_and_authority_refuse(self):
        for raw in (b'{}\n',b'<script>',profiles.encode(state())+b'junk'):
            with self.assertRaises(ValueError):surface.render_html(raw)
        value=state();value['mutation_authorized']=True
        import json
        with self.assertRaises(ValueError):surface.render_html(json.dumps(value).encode())


if __name__=='__main__':unittest.main()
