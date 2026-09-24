"""Bounded imported-proof status pipe and explicit platform refusal."""
import io,json,os,subprocess,sys,unittest
from unittest.mock import patch
from cgc.experimental import session_report_stdio as pipe,session_report as reports,review_session as sessions
class RefusalTests(unittest.TestCase):
 def test_malformed_and_platform_distinction(self):
  output=io.BytesIO();self.assertEqual(pipe.serve(io.BytesIO(b'bad'),output,'json'),2);self.assertEqual(output.getvalue(),b'')
  with patch.object(reports.os,'name','nt'):
   output=io.BytesIO();self.assertEqual(pipe.serve(io.BytesIO(b'{}\n'),output,'json'),3);self.assertEqual(output.getvalue(),b'')
 def test_input_bound_and_arguments(self):
  output=io.BytesIO();self.assertEqual(pipe.serve(io.BytesIO(b'X'*(reports.MAX_BYTES+1)),output,'json'),2);self.assertEqual(output.getvalue(),b'')
  p=subprocess.run([sys.executable,'-B','-m','cgc.experimental.session_report_stdio','json','extra'],input=b'',capture_output=True,timeout=10);self.assertEqual((p.returncode,p.stdout,p.stderr),(2,b'',b'CGCCHILD_REPORT_STATUS_REFUSED\n'))
@unittest.skipUnless(os.name=='posix','Inherited report verifier requires POSIX')
class ReportPipeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_reconciliation as fixtures
  cls.fixture=fixtures.ReconciliationTests('test_b_staged');cls.fixture.setUp();cls.addClassCleanup(cls.fixture.doCleanups);cls.fixture.pending('PASSED');s=sessions.prepare(str(cls.fixture.root),store_dir=str(cls.fixture.store_dir),now=fixtures.STAMP);cls.raw=reports.from_review(s.review(s.request_template())).bytes()
 def test_json_text_owned_process_and_no_paths(self):
  before=self.fixture.snapshot()
  for mode in ['json','text']:
   p=subprocess.run([sys.executable,'-B','-m','cgc.experimental.session_report_stdio',mode],input=self.raw,capture_output=True,timeout=10);self.assertEqual((p.returncode,p.stderr),(0,b''));self.assertEqual(p.stdout,pipe.transform(self.raw,mode));self.assertLessEqual(len(p.stdout),pipe.MAX_OUTPUT);self.assertNotIn(str(self.fixture.root).encode(),p.stdout)
  result=json.loads(pipe.transform(self.raw,'json'));self.assertEqual(result['imported_verdict'],'UNKNOWN');self.assertEqual(result['current_repository_safety'],'UNKNOWN');self.assertFalse(result['mutation_authorized']);self.assertEqual(len(result['obligations']),12);self.assertEqual(before,self.fixture.snapshot())
 def test_pure_transform_and_short_write_refusal(self):
  with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):self.assertIn(b'UNKNOWN',pipe.transform(self.raw,'text'))
  class Short(io.BytesIO):
   def write(self,data):super().write(data[:1]);return 1
  self.assertEqual(pipe.serve(io.BytesIO(self.raw),Short(),'json'),2)
 def test_tampered_verdict_no_output(self):
  raw=self.raw.replace(b'"safe_to_resume":"UNKNOWN"',b'"safe_to_resume":"YES"');self.assertNotEqual(raw,self.raw);output=io.BytesIO();self.assertEqual(pipe.serve(io.BytesIO(raw),output,'json'),2);self.assertEqual(output.getvalue(),b'')
if __name__=='__main__':unittest.main()
