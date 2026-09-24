import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from cgc.experimental import read_journal as journal,read_capabilities as grants,snapshot_profiles as profiles
from test_child_state_protocol import state


def records():
    value=state();digest=profiles.digest(value)
    lab=grants.ReadCapabilityLab(profiles.encode(value))
    handle=lab.issue('fixture',('status.get',),now_ns=1,expires_ns=100)
    lab.read(handle,'fixture','status.get',now_ns=2,snapshot_digest=digest)
    try:lab.read(handle,'other','status.get',now_ns=3,snapshot_digest=digest)
    except grants.ReadDenied:pass
    lab.revoke(handle,now_ns=4);lab.invalidate(now_ns=5)
    return lab.events(),digest


def anchor(events,digest):
    return dict(expected_snapshot_digest=digest,expected_tip=events[-1]['digest'] if events else journal.ZERO,
                expected_count=len(events))


def rehash(events):
    previous=journal.ZERO
    for event in events:
        event['previous']=previous
        body={k:v for k,v in event.items() if k!='digest'}
        event['digest']=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        previous=event['digest']


class ChildReadJournalTests(unittest.TestCase):
    def test_pinned_vector_and_schema_shape_contract(self):
        root=Path(__file__).resolve().parents[1]
        vector=json.loads((root/'docs/lab/child_read_journal_vectors.json').read_text(encoding='utf-8'))
        events,digest=records();raw=journal.encode(events,snapshot_digest=digest)
        self.assertEqual(raw,vector['journal_ascii'].encode('ascii'))
        self.assertEqual(hashlib.sha256(raw).hexdigest(),vector['journal_sha256'])
        self.assertEqual(journal.decode(raw,**vector['expected']).events(),events)
        schema=json.loads((root/'docs/child-schemas/read-journal-0.1.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(set(schema['required']),journal.ENVELOPE)
        self.assertEqual(set(schema['properties']['events']['items']['required']),journal.FIELDS)
        self.assertEqual(set(schema['properties']['events']['items']['properties']['kind']['enum']),set(journal.KINDS))
        self.assertEqual(schema['properties']['events']['maxItems'],journal.MAX_EVENTS)

    def test_actual_events_canonical_roundtrip_and_detached_view(self):
        events,digest=records();raw=journal.encode(events,snapshot_digest=digest)
        with patch('builtins.open',side_effect=AssertionError('no path')),\
             patch.object(grants.ReadCapabilityLab,'issue',side_effect=AssertionError('no imported grant')):
            view=journal.decode(raw,**anchor(events,digest))
        self.assertEqual(view.events(),events)
        self.assertEqual(journal.encode(view.events(),snapshot_digest=digest),raw)
        self.assertEqual(view.authority,'NONE');self.assertEqual(view.freshness,'HISTORICAL_UNVERIFIED')
        self.assertEqual(view.integrity,'CONSISTENT_UNSIGNED_BYTES')
        changed=view.events();changed[0]['kind']='tamper'
        self.assertEqual(view.events(),events)
        self.assertNotIn(b'fixture',raw)
        self.assertNotIn(b'principal',raw)

    def test_expected_anchor_detects_changed_prefix_but_not_unseen_tail(self):
        events,digest=records();raw=journal.encode(events,snapshot_digest=digest)
        for key,value in (('expected_tip','0'*64),('expected_count',len(events)-1),
                          ('expected_snapshot_digest','f'*64),('expected_count',True),
                          ('expected_count',65),('expected_tip','A'*64)):
            args=anchor(events,digest);args[key]=value
            with self.subTest(key=key),self.assertRaises(journal.JournalError):journal.decode(raw,**args)
        prefix=events[:-1];prefix_raw=journal.encode(prefix,snapshot_digest=digest)
        with self.assertRaises(journal.JournalError):journal.decode(prefix_raw,**anchor(events,digest))
        accepted=journal.decode(prefix_raw,**anchor(prefix,digest))
        self.assertEqual(json.loads(accepted.journal_bytes)['completeness'],'EXPECTED_PREFIX_ONLY')
        self.assertEqual(accepted.authority,'NONE')

    def test_empty_and_maximum_journal(self):
        value=state();digest=profiles.digest(value)
        raw=journal.encode((),snapshot_digest=digest)
        self.assertEqual(journal.decode(raw,**anchor((),digest)).events(),())
        lab=grants.ReadCapabilityLab(profiles.encode(value))
        handle=lab.issue('fixture',('status.get',),now_ns=0,expires_ns=100)
        for now in range(1,64):lab.read(handle,'fixture','status.get',now_ns=now,snapshot_digest=digest)
        events=lab.events();raw=journal.encode(events,snapshot_digest=digest)
        self.assertLessEqual(len(raw),journal.MAX_BYTES)
        self.assertEqual(journal.decode(raw,**anchor(events,digest)).events(),events)
        with self.assertRaises(journal.JournalError):journal.encode(events+(events[-1],),snapshot_digest=digest)

    def test_semantics_even_with_recomputed_hashes(self):
        original,digest=records()
        cases=[]
        for key,value in (('sequence',True),('sequence',0),('sequence',1.0),('observed_ns','01'),
                          ('observed_ns',str(1<<63)),('observed_ns',1),('kind','ARBITRARY_EXEC'),
                          ('kind',[]),('snapshot_digest','f'*64),('version','other'),('extra','x')):
            events=copy.deepcopy(list(original));events[1][key]=value;rehash(events);cases.append(events)
        events=copy.deepcopy(list(original));events[1]['observed_ns']='0';rehash(events);cases.append(events)
        events=copy.deepcopy(list(original));events[0]['kind']='SNAPSHOT_INVALIDATED';rehash(events);cases.append(events)
        events=copy.deepcopy(list(original));del events[0]['kind'];rehash(events);cases.append(events)
        cases.extend([list(reversed(original)),[original[0],original[0]],list(original[1:])])
        for events in cases:
            with self.subTest(events=events),self.assertRaises(journal.JournalError):
                journal.encode(events,snapshot_digest=digest)

    def test_exact_bytes_and_hash_chain_rejections(self):
        events,digest=records();raw=journal.encode(events,snapshot_digest=digest);args=anchor(events,digest)
        for bad in (raw[:-1],raw+b' ',b' '+raw,raw.replace(b'"authority":"NONE"',b'"authority":"YES"'),
                    raw.replace(b'"authority":"NONE"',b'"authority":"NONE","authority":"NONE"'),
                    raw.replace(b'"sequence":1',b'"sequence":1,"sequence":1',1),
                    raw.replace(b'"sequence":1',b'"sequence":NaN',1),b'\xff',
                    raw.replace(b'HISTORICAL_UNVERIFIED',b'LIVE_VERIFIED'),
                    raw.replace(b'SOURCE_MONOTONIC_NOT_PORTABLE',b'CURRENT_LOCAL_CLOCK'),
                    raw.replace(events[0]['digest'].encode(),b'f'*64,1),b'['*10000+b'0'+b']'*10000,
                    b'x'*(journal.MAX_BYTES+1)):
            with self.subTest(size=len(bad)),self.assertRaises(journal.JournalError):journal.decode(bad,**args)
        obj=json.loads(raw);obj['events'][1]['previous']='f'*64
        with self.assertRaises(journal.JournalError):journal.decode((json.dumps(obj)+'\n').encode(),**args)

    def test_import_does_not_replay_or_create_local_handle(self):
        events,digest=records();view=journal.decode(journal.encode(events,snapshot_digest=digest),**anchor(events,digest))
        other=grants.ReadCapabilityLab(profiles.encode(state()))
        for handle in (view,view.events()[0],view.journal_bytes):
            with self.assertRaises(grants.ReadDenied):other.read(handle,'fixture','status.get',now_ns=10,snapshot_digest=digest)
        self.assertTrue(all(e['kind']=='READ_DENIED' for e in other.events()))


if __name__=='__main__':unittest.main()
