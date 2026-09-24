import copy
import json
import os
import unittest
from unittest.mock import patch
if os.name=='posix':
    from cgc import reconciliation as rc,safe_resume as verifier,verification_capture as bridge
from cgc.experimental import resume_review as child


class ChildResumeRefusalTests(unittest.TestCase):
    def test_unconditional_execution_refusal(self):
        for value in (None,{},True,child.Review('{}','{}','{"safe_to_resume":"YES"}')):
            with self.assertRaisesRegex(RuntimeError,'NO_ACCEPTED_EXECUTION_ADAPTER'):
                child.execute_review(value)

    def test_unsupported_platform_refuses_explicitly(self):
        with patch.object(child.os,'name','nt'):
            with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_VERIFIER_PLATFORM'):child.review({},{})

    @unittest.skipUnless(os.name=='posix','Inherited verifier has POSIX import dependencies')
    def test_malformed_input_has_no_io(self):
        with patch('subprocess.Popen',side_effect=AssertionError('process')), patch('builtins.open',side_effect=AssertionError('file')):
            with self.assertRaises(verifier.VerificationError):child.review({},{})


@unittest.skipUnless(os.name=='posix','Inherited Git capture fixtures accepted on POSIX')
class ChildResumeCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_reconciliation as fixtures
        cls.fixture=fixtures.ReconciliationTests('test_b_staged')
        cls.fixture.setUp();cls.addClassCleanup(cls.fixture.doCleanups)
        cls.fixture.pending('PASSED')
        before=cls.fixture.snapshot()
        cls.capture=bridge.capture(str(cls.fixture.root),store_dir=str(cls.fixture.store_dir),now=fixtures.STAMP)
        assert before==cls.fixture.snapshot()
        cls.projection=cls.capture.projection
        cls.request=verifier.request_for(cls.projection)

    def test_captured_analysis_and_detached_result(self):
        before=self.fixture.snapshot()
        with patch('subprocess.Popen',side_effect=AssertionError('process')), patch('builtins.open',side_effect=AssertionError('file')):
            result=child.review(self.projection,self.request,capture=self.capture)
        self.assertEqual(result.verification['safe_to_resume'],'YES')
        self.assertFalse(result.verification['mutation_allowed'])
        edited=result.verification;edited['mutation_allowed']=True
        self.assertFalse(result.verification['mutation_allowed'])
        self.assertEqual(before,self.fixture.snapshot())

    def test_portable_report_loses_current_capture(self):
        result=child.review(self.projection,self.request,capture=self.capture)
        report=json.loads(json.dumps(result.historical_report()))
        proof=report['verification']
        self.assertEqual(proof['safe_to_resume'],'UNKNOWN')
        self.assertEqual(proof['input']['provenance'],'IMPORTED')
        self.assertEqual(proof['facts']['historical_test_result'],'PASSED')
        verifier.validate_result(proof)
        self.assertFalse(report['mutation_authorized'])
        self.assertEqual(report['current_repository_safety'],'UNKNOWN')

    def test_all_actions_and_levels_have_no_executor(self):
        for action in verifier.ACTIONS:
            for level in verifier.LEVELS:
                request=verifier.request_for(self.projection,action=action,level=level)
                result=child.review(self.projection,request,capture=self.capture)
                proof=result.verification
                with self.subTest(action=action,level=level):
                    self.assertFalse(proof['mutation_allowed'])
                    self.assertFalse(proof['automatic_mutation_authorized'])
                    if action!='READ_ONLY_ANALYSIS':
                        self.assertNotEqual(proof['safe_to_resume'],'YES')
                        self.assertEqual(next(p for p in proof['proof_obligations'] if p['id']=='P3')['status'],'UNKNOWN')
                    with self.assertRaises(RuntimeError):child.execute_review(result)

    def test_replay_forged_binding_and_changed_request(self):
        for capture in (None,bridge.Capture(rc.render_json(self.projection),object())):
            self.assertEqual(child.review(self.projection,self.request,capture=capture).verification['safe_to_resume'],'UNKNOWN')
        request=copy.deepcopy(self.request);request['evidence_digest']='0'*64
        proof=child.review(self.projection,request,capture=self.capture).verification
        self.assertEqual(proof['safe_to_resume'],'NO')
        self.assertFalse(proof['mutation_allowed'])


if __name__=='__main__':unittest.main()
