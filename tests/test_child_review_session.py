"""Two-step owned-fixture capture stays analysis-only and single-use."""
import copy,os,unittest
from unittest.mock import patch
from cgc.experimental import review_session as sessions
class RefusalTests(unittest.TestCase):
 def test_platform_and_execution_refusal(self):
  with patch.object(sessions.os,'name','nt'):
   with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_REVIEW_SESSION_PLATFORM'):sessions.prepare('/opaque',store_dir='/store',now='2026-09-24T00:00:00Z')
  for value in [None,{},True]:
   with self.assertRaisesRegex(RuntimeError,'NO_ACCEPTED_EXECUTION_ADAPTER'):sessions.execute(value)
@unittest.skipUnless(os.name=='posix','Inherited capture dependencies require POSIX')
class CaptureSessionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  import test_reconciliation as fixtures
  cls.fixture=fixtures.ReconciliationTests('test_b_staged');cls.fixture.setUp();cls.addClassCleanup(cls.fixture.doCleanups);cls.fixture.pending('PASSED');cls.stamp=fixtures.STAMP
 def prepare(self):return sessions.prepare(str(self.fixture.root),store_dir=str(self.fixture.store_dir),now=self.stamp)
 def test_explicit_review_and_historical_demotion(self):
  before=self.fixture.snapshot();session=self.prepare();self.assertEqual(session.state,'PREPARED');request=session.request_template();projection=session.projection();projection['safe_to_resume']='YES';self.assertNotEqual(session.projection().get('safe_to_resume'),'YES')
  with patch('subprocess.Popen',side_effect=AssertionError('unexpected process')),patch('builtins.open',side_effect=AssertionError('unexpected open')):review=session.review(request)
  self.assertEqual(review.verification['safe_to_resume'],'YES');self.assertFalse(review.verification['mutation_allowed']);self.assertEqual(review.historical_report()['verification']['safe_to_resume'],'UNKNOWN');self.assertEqual(before,self.fixture.snapshot());self.assertEqual(session.state,'CLOSED')
  with self.assertRaises(sessions.SessionError):session.review(request)
  with self.assertRaises(sessions.SessionError):session.request_template()
 def test_scope_escalations_consume_capture(self):
  for key,value in [('action','CREATE_CHECKPOINT'),('level','REMOTE_VERIFIED'),('test_policy','REQUIRE_CURRENT_PASS')]:
   session=self.prepare();request=session.request_template();request[key]=value
   with self.assertRaises(sessions.SessionError):session.review(request)
   self.assertEqual(session.state,'CLOSED')
   with self.assertRaises(sessions.SessionError):session.projection()
 def test_changed_expectation_no_and_close(self):
  session=self.prepare();request=session.request_template();request['evidence_digest']='0'*64;review=session.review(request);self.assertEqual(review.verification['safe_to_resume'],'NO');self.assertFalse(review.verification['mutation_allowed'])
  session=self.prepare();session.close();session.close()
  with self.assertRaises(sessions.SessionError):session.review({})
 def test_prepare_has_only_fixed_local_arguments(self):
  before=self.fixture.snapshot()
  with self.assertRaises(TypeError):sessions.prepare(str(self.fixture.root),store_dir=str(self.fixture.store_dir),now=self.stamp,remote={'path':'/unrequested'})
  self.assertEqual(before,self.fixture.snapshot())
if __name__=='__main__':unittest.main()
