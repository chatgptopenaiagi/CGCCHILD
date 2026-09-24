"""Imported report consistency never restores private capture or execution."""
import copy,hashlib,json,os,unittest
from unittest.mock import patch
from cgc.experimental import session_report as reports,review_session as sessions
class ReportRefusal(unittest.TestCase):
 def test_platform_and_execution_refuse(self):
  with patch.object(reports.os,'name','nt'):
   with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_REPORT_VERIFIER_PLATFORM'):reports.validate({})
  for value in [None,{},True]:
   with self.assertRaises(RuntimeError):reports.execute(value)
   with self.assertRaises(reports.ReportError):reports.from_review(value)
@unittest.skipUnless(os.name=='posix','Inherited proof dependencies require POSIX')
class ReportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_reconciliation as fixtures
  cls.fixture=fixtures.ReconciliationTests('test_b_staged');cls.fixture.setUp();cls.addClassCleanup(cls.fixture.doCleanups);cls.fixture.pending('PASSED')
  session=sessions.prepare(str(cls.fixture.root),store_dir=str(cls.fixture.store_dir),now=fixtures.STAMP);cls.review=session.review(session.request_template());cls.report=reports.from_review(cls.review);cls.value=cls.report.as_dict()
 def test_roundtrip_pure_and_detached(self):
  self.assertEqual(self.review.verification['safe_to_resume'],'YES');before=self.fixture.snapshot()
  with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):
   value=reports.decode(self.report.bytes());self.assertEqual(reports.encode(value),self.report.bytes())
  self.assertEqual(value['verification']['safe_to_resume'],'UNKNOWN');self.assertEqual(value['verification']['input']['provenance'],'IMPORTED');value['authority']='changed';self.assertEqual(self.report.as_dict()['authority'],'NONE');self.assertEqual(before,self.fixture.snapshot())
 def test_outer_substitutions(self):
  for key in self.value:
   for bad in [None,True,0,[],{},'unexpected']:
    value=copy.deepcopy(self.value);value[key]=bad
    with self.assertRaises(reports.ReportError):reports.encode(value)
 def test_forged_current_proof_and_resealed_verdict(self):
  value=copy.deepcopy(self.value);value['verification']=self.review.verification
  value['verification_sha256']=hashlib.sha256(reports._bytes(value['verification'])).hexdigest()
  with self.assertRaises(reports.ReportError):reports.encode(value)
  for key,bad in [('safe_to_resume','YES'),('mutation_allowed',True),('automatic_mutation_authorized',True)]:
   value=copy.deepcopy(self.value);value['verification'][key]=bad;value['verification_sha256']=hashlib.sha256(reports._bytes(value['verification'])).hexdigest()
   with self.assertRaises(reports.ReportError):reports.encode(value)
 def test_wire_bounds_duplicates_and_truncation(self):
  raw=self.report.bytes()
  for bad in [raw[:-1],raw+b' ',raw.replace(b'"authority":"NONE"',b'"authority":"NONE","authority":"NONE"'),b'X'*(reports.MAX_BYTES+1),b'NaN\n',b'\xff\n']:
   with self.assertRaises(reports.ReportError):reports.decode(bad)
if __name__=='__main__':unittest.main()
