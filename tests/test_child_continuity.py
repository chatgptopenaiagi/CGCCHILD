import copy
import hashlib
import json
import unittest
from cgc.handoff import validate_state,SCHEMA_VERSION
from cgc.preservation import new_attempt,advance
from cgc.experimental import continuity as co


STAMP='2026-09-24T12:00:00Z'


def source_state():
    record=new_attempt('/owned-fixture',now=STAMP,mission='synthetic continuity',next_exact_action='Inert guidance, not a command',trigger='SYNTHETIC')
    record=advance(record,'DOCUMENTING',now=STAMP,test_status='FAILED',
                   notes={'known_failures':['synthetic failure'],'tests_run':['inert fixture command'],
                          'test_results':['one synthetic failure']})
    slot=dict(generation=1,published_at=STAMP,content_basis='OPERATOR_CURATED',record=record,inspection=None)
    slot['digest']=hashlib.sha256((json.dumps(slot,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
    return validate_state(dict(schema_version=SCHEMA_VERSION,scope='CONTINUITY_ONLY',project_request='/owned-fixture',generation=2,
        latest_attempt=dict(status='FAILED',at=STAMP,error_code='VERIFICATION_FAILED',handoff_digest=None),
        last_known_good=slot,previous_known_good=None,safe_to_resume='UNKNOWN',automatic_mutation_authorized=False))


class ChildContinuityTests(unittest.TestCase):
    def test_lossless_roundtrip_and_failure_distinctions(self):
        source=source_state();before=copy.deepcopy(source)
        p=co.project(source,portable_project_id='portable-fixture')
        value=co.decode(co.encode(p))
        self.assertEqual(value['source_state'],before)
        self.assertEqual(source,before)
        result=co.summary(value)
        self.assertEqual(result['latest_attempt'],'FAILED')
        self.assertEqual(result['latest_error'],'VERIFICATION_FAILED')
        self.assertEqual(result['last_known_good_generation'],1)
        self.assertIsNone(result['previous_known_good_generation'])
        self.assertEqual(result['current_safe_to_resume'],'UNKNOWN')
        self.assertFalse(result['current_mutation_authorized'])
        self.assertNotIn('project_request',result)

    def test_known_good_slots_both_preserved(self):
        source=source_state();source['previous_known_good']=copy.deepcopy(source['last_known_good'])
        source['generation']=4;source['last_known_good']['generation']=3
        slot=source['last_known_good'];del slot['digest']
        slot['digest']=hashlib.sha256((json.dumps(slot,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
        view=co.project(source,portable_project_id='fixture')
        self.assertEqual(co.summary(view)['previous_known_good_generation'],1)
        self.assertEqual(co.summary(view)['last_known_good_generation'],3)

    def test_tampering_and_promotion_refuse(self):
        original=co.project(source_state(),portable_project_id='fixture')
        for key,value in (('current_safe_to_resume','YES'),('current_mutation_authorized',True),
                          ('freshness','LIVE'),('source_digest','0'*64),('portable_project_id','../live'),('extra','x')):
            v=copy.deepcopy(original);v[key]=value
            with self.assertRaises(co.ContinuityError):co.encode(v)
        v=copy.deepcopy(original);v['source_state']['last_known_good']['record']['notes']['mission']='tamper'
        with self.assertRaises(co.ContinuityError):co.encode(v)

    def test_duplicates_trailing_and_bounds_refuse(self):
        raw=co.encode(co.project(source_state(),portable_project_id='fixture'))
        for data in (raw+b' ',raw.replace(b'"generation":2',b'"generation":2,"generation":2'),raw[:-1],b'x'*(co.MAX_BYTES+1)):
            with self.assertRaises(co.ContinuityError):co.decode(data)

    def test_invalid_source_never_projected(self):
        source=source_state();source['safe_to_resume']='YES'
        with self.assertRaises(co.ContinuityError):co.project(source,portable_project_id='fixture')


if __name__=='__main__':unittest.main()
