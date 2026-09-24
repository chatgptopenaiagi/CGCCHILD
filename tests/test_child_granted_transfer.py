"""Granted data, independent assembly and journal consistency stay separate proof layers."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from cgc.experimental import read_capabilities as cap,read_journal as journal,capsule,capsule_chunks as chunks,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_chunks import large_state

ROOT=Path(__file__).resolve().parents[1]
def wire(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


@unittest.skipUnless(shutil.which('node'),'Node absent; cross-language composition not executed')
class GrantedTransferTests(unittest.TestCase):
    def node(self,name,payload):
        run=subprocess.run(['node',str(ROOT/'sdk/javascript'/name)],input=json.dumps(payload).encode(),capture_output=True,timeout=15)
        self.assertEqual((run.returncode,run.stderr),(0,b''));return json.loads(run.stdout)

    def assembly(self,value,packets,anchor_override=None):
        # Anchor is independently derived from this test owner's validated immutable source.
        archive=capsule.export_capsule(value)
        expected=dict(total_bytes=len(archive),capsule_sha256=hashlib.sha256(archive).hexdigest())
        if anchor_override:expected.update(anchor_override)
        return self.node('chunk_conformance.mjs',[dict(expected=expected,frames=[base64.b64encode(wire(p)).decode() for p in packets])])[0]

    def journal(self,lab,digest):
        events=lab.events();raw=journal.encode(events,snapshot_digest=digest)
        expected=dict(expected_snapshot_digest=digest,expected_count=len(events),expected_tip=events[-1]['digest'])
        view=journal.decode(raw,**expected)
        result=self.node('journal_conformance.mjs',[dict(hex=raw.hex(),expected=expected)])[0]
        self.assertTrue(result['accepted']);self.assertEqual(result['hex'],raw.hex())
        self.assertEqual(result['authority'],'NONE');self.assertEqual(result['completeness'],'EXPECTED_PREFIX_ONLY')
        self.assertEqual(view.events(),events)
        return raw,expected

    def transfer(self,value):
        digest=profiles.digest(value);lab=cap.ReadCapabilityLab(profiles.encode(value))
        h=lab.issue('owned-consumer',('capsule.chunk',),now_ns=0,expires_ns=1000)
        packets=[];offset=0
        while True:
            reply=json.loads(lab.read_chunk(h,'owned-consumer',offset,now_ns=len(packets)+1,snapshot_digest=digest))
            self.assertFalse(reply['mutation_authorized']);packets.append(reply['result'])
            if packets[-1]['done']:break
            offset+=chunks.CHUNK_BYTES
        lab.invalidate(now_ns=len(packets)+2)
        return lab,digest,packets

    def test_complete_both_profiles_and_terminal_historical_journal(self):
        for value in (state(),large_state()):
            lab,digest,packets=self.transfer(value);assembled=self.assembly(value,packets)
            self.assertTrue(assembled['accepted']);self.assertEqual(assembled['capsule_validation'],'NOT_PERFORMED')
            view=capsule.import_capsule(base64.b64decode(assembled['raw']))
            self.assertEqual(view.snapshot(),value);self.assertEqual(view.authority,'NONE')
            raw,expected=self.journal(lab,digest)
            self.assertEqual(lab.events()[-1]['kind'],'SNAPSHOT_INVALIDATED')
            self.assertEqual(expected['expected_count'],len(packets)+2)
            self.assertNotIn(b'owned-consumer',raw)

    def test_expired_partial_transfer_never_becomes_importable(self):
        value=large_state();digest=profiles.digest(value);lab=cap.ReadCapabilityLab(profiles.encode(value))
        h=lab.issue('owned-consumer',('capsule.chunk',),now_ns=0,expires_ns=2)
        packet=json.loads(lab.read_chunk(h,'owned-consumer',0,now_ns=1,snapshot_digest=digest))['result']
        self.assertFalse(packet['done'])
        with self.assertRaises(cap.ReadDenied):lab.read_chunk(h,'owned-consumer',chunks.CHUNK_BYTES,now_ns=2,snapshot_digest=digest)
        self.assertEqual(self.assembly(value,[packet]),{'accepted':False})
        self.journal(lab,digest);self.assertEqual(lab.events()[-1]['kind'],'READ_DENIED')

    def test_consistent_journal_does_not_override_bad_data(self):
        value=large_state();lab,digest,packets=self.transfer(value)
        self.journal(lab,digest)
        self.assertEqual(self.assembly(value,packets,{'capsule_sha256':'0'*64}),{'accepted':False})
        changed=[dict(p) for p in packets];changed[0]['data']='AAAA'
        self.assertEqual(self.assembly(value,changed),{'accepted':False})

    def test_complete_data_does_not_override_wrong_journal_anchor(self):
        value=state();lab,digest,packets=self.transfer(value)
        self.assertTrue(self.assembly(value,packets)['accepted'])
        raw,expected=self.journal(lab,digest);expected['expected_tip']='0'*64
        with self.assertRaises(journal.JournalError):journal.decode(raw,**expected)
        self.assertEqual(self.node('journal_conformance.mjs',[dict(hex=raw.hex(),expected=expected)]),[{'accepted':False}])


if __name__=='__main__':unittest.main()
