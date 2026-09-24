"""Recovery planning never turns imported evidence into an executable repair."""
import copy
import os
import unittest
from unittest.mock import patch
from cgc.experimental import recovery_review as child
from cgc.experimental.orchestration import Action
if os.name=='posix':
    from cgc import reconciliation as rc


class RefusalTests(unittest.TestCase):
    def test_execute_refuses_every_value(self):
        for value in (None,{},True,child.RecoveryReview('{"mutation_authorized":true}')):
            with self.assertRaisesRegex(RuntimeError,'NO_ACCEPTED_EXECUTION_ADAPTER'):child.execute(value)

    def test_platform_refusal(self):
        with patch.object(child.os,'name','nt'):
            with self.assertRaisesRegex(RuntimeError,'UNSUPPORTED_RECOVERY_PLATFORM'):
                child.assess({},Action.REPAIR,expected_project='/x',expected_projection_digest='0'*64)


@unittest.skipUnless(os.name=='posix','Inherited reconciliation requires POSIX')
class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_reconciliation as fixtures
        cls.fixture=fixtures.ReconciliationTests('test_b_staged')
        cls.fixture.setUp();cls.addClassCleanup(cls.fixture.doCleanups)
        cls.fixture.pending('PASSED')
        before=cls.fixture.snapshot()
        cls.projection=rc.reconcile(str(cls.fixture.root),store_dir=str(cls.fixture.store_dir),now=fixtures.STAMP)
        assert before==cls.fixture.snapshot()

    def assess(self,projection=None,action=Action.REPAIR,**kw):
        value=self.projection if projection is None else projection
        args=dict(expected_project=value['evidence']['project'],expected_projection_digest=rc.digest(value))
        args.update(kw)
        return child.assess(value,action,**args)

    def test_actions_pure_and_detached(self):
        before=self.fixture.snapshot()
        for action in Action:
            with patch('subprocess.Popen',side_effect=AssertionError('process')),patch('builtins.open',side_effect=AssertionError('file')):
                result=self.assess(action=action)
            report=result.as_dict()
            self.assertEqual(report['state'],'REVIEW_REQUIRED_NO_EXECUTOR')
            self.assertEqual(report['production_p3'],'UNKNOWN')
            self.assertEqual(report['current_repository_safety'],'UNKNOWN')
            self.assertFalse(report['mutation_authorized'])
            self.assertEqual(report['historical_test_result'],'PASSED')
            self.assertIn('ESTABLISH_TESTED_STATE_BINDING',report['steps'])
            report['mutation_authorized']=True;report['steps'].clear()
            self.assertFalse(result.as_dict()['mutation_authorized'])
            self.assertTrue(result.as_dict()['steps'])
        self.assertEqual(before,self.fixture.snapshot())

    def test_binding_mismatch_is_refusal(self):
        for kw in ({'expected_project':'/different'},{'expected_projection_digest':'0'*64}):
            report=self.assess(**kw).as_dict()
            self.assertEqual(report['state'],'REFUSED_EVIDENCE_BINDING')
            self.assertEqual(report['issues'],[])
            self.assertEqual(len(report['steps']),2)
            self.assertFalse(report['mutation_authorized'])

    def test_invalid_inputs_and_forged_classification(self):
        for digest in ('0'*63,'A'*64,'0'*64+'\n',True,None):
            with self.assertRaises(child.RecoveryError):self.assess(expected_projection_digest=digest)
        for action in ('REPAIR',None,True):
            with self.assertRaises(child.RecoveryError):self.assess(action=action)
        forged=copy.deepcopy(self.projection);forged['safe_to_resume']='YES'
        with self.assertRaises(child.RecoveryError):self.assess(forged)
        with self.assertRaises(child.RecoveryError):child.assess({},Action.REPAIR,expected_project='/x',expected_projection_digest='0'*64)

    def test_fixed_issue_mapping_and_no_historical_command(self):
        # Synthetic mutations are reclassified, never presented as live observations.
        basis=copy.deepcopy(self.projection['evidence'])
        basis['collection_error']='TARGET_CHANGED'
        basis['handoff']['error_code']='TARGET_CHANGED'
        basis['handoff']['last_known_good']['base_branch']='other'
        basis['handoff']['last_known_good']['next_exact_action']='ARBITRARY_HISTORICAL_COMMAND'
        basis['remote_request']=dict(path=str(self.fixture.root.parent/'remote'),identity=dict(device=1,inode=1),ref='refs/heads/main',tracking_ref='refs/remotes/origin/main',expected_commit=self.fixture.head)
        basis['remote_error']='REMOTE_REF_MISSING_OR_AMBIGUOUS'
        projection=rc.classify(basis)
        report=self.assess(projection).as_dict()
        for action in child.STEPS:
            self.assertIn(child.STEPS[action],report['steps'])
        self.assertEqual([i['priority'] for i in report['issues']],sorted(i['priority'] for i in report['issues']))
        self.assertNotIn('ARBITRARY_HISTORICAL_COMMAND',str(report))
        self.assertEqual(report['freshness'],'HISTORICAL_UNVERIFIED')

    def test_empty_issue_set_is_not_permission(self):
        basis=copy.deepcopy(self.projection['evidence'])
        basis['handoff']=dict(generation=None,digest=None,latest_attempt=None,last_known_good=None,previous_known_good=None,error_code=None)
        basis['handoff_last']=dict(generation=None,digest=None,error_code=None)
        projection=rc.classify(basis)
        self.assertEqual(projection['issues'],[])
        report=self.assess(projection).as_dict()
        self.assertEqual(report['state'],'REVIEW_REQUIRED_NO_EXECUTOR')
        self.assertFalse(report['mutation_authorized'])
        self.assertEqual(report['current_repository_safety'],'UNKNOWN')
        self.assertIn('OBTAIN_FRESH_SCOPED_AUTHORITY',report['steps'])


if __name__=='__main__':unittest.main()
