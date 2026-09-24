"""Independent Node chunk consistency, followed by explicit Python capsule acceptance."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from cgc.experimental import capsule,capsule_chunks as chunks,snapshot_profiles as profiles
from test_child_state_protocol import state
from test_child_chunks import large_state

ROOT=Path(__file__).resolve().parents[1]

def wire(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode('ascii')

def case(raw,frames=None):
    if frames is None:frames=[wire(chunks._slice(raw,i)) for i in range(0,len(raw),chunks.CHUNK_BYTES)]
    return dict(expected=dict(total_bytes=len(raw),capsule_sha256=hashlib.sha256(raw).hexdigest()),
                frames=[base64.b64encode(x).decode('ascii') for x in frames])


@unittest.skipUnless(shutil.which('node'),'Node unavailable; independent chunk acceptance not executed')
class JavascriptChunkTests(unittest.TestCase):
    def run_cases(self,cases):
        run=subprocess.run(['node',str(ROOT/'sdk/javascript/chunk_conformance.mjs')],
                           input=json.dumps(cases).encode(),capture_output=True,timeout=15)
        self.assertEqual((run.returncode,run.stderr),(0,b''))
        return json.loads(run.stdout)

    def test_two_profiles_reassemble_then_core_validates(self):
        for value in (state(),large_state()):
            raw=capsule.export_capsule(value);result=self.run_cases([case(raw)])[0]
            self.assertTrue(result['accepted']);self.assertEqual(result['authority'],'NONE')
            self.assertEqual(result['capsule_validation'],'NOT_PERFORMED');self.assertFalse(result['source_authenticated'])
            rebuilt=base64.b64decode(result['raw']);self.assertEqual(rebuilt,raw)
            self.assertEqual(capsule.import_capsule(rebuilt).snapshot(),value)

    def test_transport_consistency_is_not_archive_acceptance(self):
        raw=b'not a capsule: matched bytes confer no authority'
        result=self.run_cases([case(raw)])[0]
        self.assertTrue(result['accepted']);self.assertEqual(result['capsule_validation'],'NOT_PERFORMED')
        with self.assertRaises(capsule.CapsuleError):capsule.import_capsule(base64.b64decode(result['raw']))

    def test_fixed_fields_canonical_bytes_and_anchors(self):
        raw=capsule.export_capsule(state());packet=chunks._slice(raw,0);frame=wire(packet)
        frames=[b'',frame[:-1],frame+b' ',frame.replace(b'"offset":0',b'"offset":0,"offset":0'),b'\xff'+frame]
        for field,value in [('offset',1),('offset',True),('total_bytes',len(raw)+1),('data',packet['data']+' '),
             ('encoding','hex'),('done',False),('done',1),('chunk_sha256','0'*64),('capsule_sha256','0'*64),
             ('data',''),('extra','field')]:
            changed=copy.deepcopy(packet);changed[field]=value;frames.append(wire(changed))
        cases=[case(raw,[x]) for x in frames]
        for change in ({'total_bytes':True},{'total_bytes':capsule.MAX_BYTES+1},{'capsule_sha256':'x'},{'extra':False}):
            item=case(raw);item['expected'].update(change);cases.append(item)
        self.assertEqual(self.run_cases(cases),[{'accepted':False}]*len(cases))

    def test_deterministic_corruption_and_truncation(self):
        raw=capsule.export_capsule(state());frame=wire(chunks._slice(raw,0));frames=[]
        for offset in range(0,len(frame),max(1,len(frame)//120)):
            changed=bytearray(frame);changed[offset]^=1;frames.append(bytes(changed))
            frames.append(frame[:offset])
        for start in range(0,len(frames),64):
            batch=frames[start:start+64]
            self.assertEqual(self.run_cases([case(raw,[x]) for x in batch]),[{'accepted':False}]*len(batch))

    def test_native_bounds_replay_ownership_and_terminal_state(self):
        self.assertEqual(capsule.MAX_BYTES,2117632);self.assertEqual(chunks.CHUNK_BYTES,32768)
        run=subprocess.run(['node',str(ROOT/'sdk/javascript/test_capsule_chunks.mjs')],capture_output=True,timeout=15)
        self.assertEqual((run.returncode,run.stderr),(0,b''));self.assertEqual(json.loads(run.stdout),{'status':'PASS','cases':17})


if __name__=='__main__':unittest.main()
