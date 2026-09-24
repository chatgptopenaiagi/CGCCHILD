"""A captured analysis YES is never substituted for a mutation-action review."""
import copy
import os
import unittest
from unittest.mock import patch
from cgc.experimental import recovery_review as child
from cgc.experimental.orchestration import Action
if os.name=='posix':
    from cgc import reconciliation as rc,safe_resume as verifier,verification_capture as bridge


class RefusalTests(unittest.TestCase):
    def test_unsupported_platform(self):
        with patch.object(child.os,'name','nt'):
            with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_RECOVERY_PLATFORM'):
                child.review_action({},Action.REPAIR,{},expected_project='/x',expected_projection_digest='0'*64)

    def test_forged_bundle_is_not_executable(self):
        with self.assertRaisesRegex(RuntimeError,'NO_ACCEPTED_EXECUTION_ADAPTER'):
            child.execute(child.ActionReview(None,{'safe_to_resume':'YES'}))


@unittest.skipUnless(os.name=='posix','Inherited verifier/capture requires POSIX')
class BindingTests(unittest.TestCase):
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

    def call(self,action,request,**overrides):
        args=dict(expected_project=self.projection['evidence']['project'],expected_projection_digest=rc.digest(self.projection),capture=self.capture)
        args.update(overrides)
        return child.review_action(self.projection,action,request,**args)

    def test_all_action_level_pairs_preserve_unknown_and_no_io(self):
        before=self.fixture.snapshot()
        for action in Action:
            for level in verifier.LEVELS:
                request=verifier.request_for(self.projection,action=child.PROOF_ACTIONS[action],level=level)
                with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):
                    result=self.call(action,request)
                    report=result.historical_report()
                proof=result.verification
                self.assertNotEqual(proof['safe_to_resume'],'YES')
                self.assertFalse(proof['mutation_allowed'])
                self.assertEqual(proof['input']['request']['action'],child.PROOF_ACTIONS[action])
                self.assertEqual(proof['input']['request']['level'],level)
                self.assertEqual(next(p for p in proof['proof_obligations'] if p['id']=='P3')['status'],'UNKNOWN')
                self.assertEqual(report['proof']['verification']['input']['provenance'],'IMPORTED')
                self.assertFalse(report['mutation_authorized'])
                report['recovery']['mutation_authorized']=True
                self.assertFalse(result.historical_report()['recovery']['mutation_authorized'])
                verifier.validate_result(report['proof']['verification'])
        self.assertEqual(before,self.fixture.snapshot())

    def test_analysis_yes_and_cross_action_substitution_refuse(self):
        analysis=verifier.request_for(self.projection)
        self.assertEqual(verifier.verify(self.projection,analysis,capture=self.capture)['safe_to_resume'],'YES')
        for action in Action:
            for other in verifier.ACTIONS:
                if other==child.PROOF_ACTIONS[action]:continue
                request=verifier.request_for(self.projection,action=other)
                with self.assertRaises(child.RecoveryError):self.call(action,request)

    def test_explicit_binding_and_bad_proof_request(self):
        request=verifier.request_for(self.projection,action='REPAIR_KNOWN_FAILURE')
        for kw in ({'expected_project':'/other'},{'expected_projection_digest':'0'*64}):
            with self.assertRaises(child.RecoveryError):self.call(Action.REPAIR,request,**kw)
        changed=copy.deepcopy(request);changed['evidence_digest']='0'*64
        with self.assertRaises(child.RecoveryError):self.call(Action.REPAIR,changed)
        changed=copy.deepcopy(request);changed['project']='/other'
        with self.assertRaises(child.RecoveryError):self.call(Action.REPAIR,changed)
        changed=copy.deepcopy(request);changed['extra']='YES'
        with self.assertRaises(verifier.VerificationError):self.call(Action.REPAIR,changed)

    def test_input_changes_do_not_rewrite_existing_review(self):
        request=verifier.request_for(self.projection,action='CREATE_CHECKPOINT')
        result=self.call(Action.CHECKPOINT,request)
        original=result.historical_report()
        request['action']='READ_ONLY_ANALYSIS'
        proof=result.verification;proof['safe_to_resume']='YES'
        self.assertEqual(result.historical_report(),original)
        self.assertNotEqual(result.verification['safe_to_resume'],'YES')


if __name__=='__main__':unittest.main()
