"""Granted continuity transfer: independent Node byte, semantic and journal layers."""
import base64,copy,hashlib,json,shutil,subprocess,unittest
from pathlib import Path
from cgc.experimental import read_capabilities as cap,read_journal as journal,capsule,capsule_chunks as chunks,snapshot_profiles as profiles
import test_child_chunks as fixtures
ROOT=Path(__file__).resolve().parents[1]
def wire(x):return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class NodeContinuityTransfer(unittest.TestCase):
 def node(self,name,payload):
  p=subprocess.run(['node',str(ROOT/'sdk/javascript'/name)],input=json.dumps(payload).encode(),capture_output=True,timeout=20)
  self.assertEqual((p.returncode,p.stderr),(0,b''));return json.loads(p.stdout)[0]
 def setup_transfer(self):
  value=fixtures.large_state();digest=profiles.digest(value);archive=capsule.export_capsule(value);lab=cap.ReadCapabilityLab(profiles.encode(value));handle=lab.issue('owned',('capsule.chunk',),now_ns=0,expires_ns=1000);packets=[]
  for offset in range(0,len(archive),chunks.CHUNK_BYTES):packets.append(json.loads(lab.read_chunk(handle,'owned',offset,now_ns=len(packets)+1,snapshot_digest=digest))['result'])
  lab.invalidate(now_ns=len(packets)+2)
  expected=dict(total_bytes=len(archive),capsule_sha256=hashlib.sha256(archive).hexdigest())
  return value,digest,archive,lab,packets,expected
 def assemble(self,packets,expected):return self.node('chunk_conformance.mjs',[dict(expected=expected,frames=[base64.b64encode(wire(p)).decode() for p in packets])])
 def semantics(self,raw):return self.node('continuity_capsule_conformance.mjs',[raw.hex()])
 def audit(self,lab,digest,bad=False):
  events=lab.events();raw=journal.encode(events,snapshot_digest=digest);expected=dict(expected_snapshot_digest=digest,expected_count=len(events),expected_tip='0'*64 if bad else events[-1]['digest'])
  return self.node('journal_conformance.mjs',[dict(hex=raw.hex(),expected=expected)])
 def test_complete_independent_pipeline(self):
  value,digest,archive,lab,packets,expected=self.setup_transfer();assembled=self.assemble(packets,expected)
  self.assertTrue(assembled['accepted']);self.assertEqual(assembled['capsule_validation'],'NOT_PERFORMED')
  raw=base64.b64decode(assembled['raw']);self.assertEqual(raw,archive);semantic=self.semantics(raw)
  self.assertTrue(semantic['accepted']);self.assertEqual(semantic['state'].encode(),profiles.encode(value));self.assertEqual(semantic['authority'],'NONE')
  audit=self.audit(lab,digest);self.assertTrue(audit['accepted']);self.assertEqual(audit['completeness'],'EXPECTED_PREFIX_ONLY');self.assertEqual(audit['authority'],'NONE')
 def test_partial_and_wrong_chunk_never_semantic_success(self):
  value,digest,archive,lab,packets,expected=self.setup_transfer();self.assertGreater(len(packets),1)
  self.assertFalse(self.assemble(packets[:-1],expected)['accepted']);changed=copy.deepcopy(packets);changed[0]['data']='AAAA';self.assertFalse(self.assemble(changed,expected)['accepted']);self.assertTrue(self.audit(lab,digest)['accepted'])
 def test_consistent_bytes_cannot_bypass_semantic_validation(self):
  value,digest,archive,lab,packets,expected=self.setup_transfer();raw=b'not a capsule';sha=hashlib.sha256(raw).hexdigest()
  packet=dict(offset=0,total_bytes=len(raw),capsule_sha256=sha,chunk_sha256=sha,data=base64.b64encode(raw).decode(),done=True)
  # Use the actual fixed chunk schema; no grant claimed for this synthetic packet.
  packet['encoding']='base64'
  assembled=self.assemble([packet],dict(total_bytes=len(raw),capsule_sha256=sha))
  self.assertTrue(assembled['accepted']);self.assertFalse(self.semantics(base64.b64decode(assembled['raw']))['accepted']);self.assertTrue(self.audit(lab,digest)['accepted'])
 def test_semantics_do_not_override_journal_anchor(self):
  value,digest,archive,lab,packets,expected=self.setup_transfer();self.assertTrue(self.semantics(archive)['accepted']);self.assertFalse(self.audit(lab,digest,bad=True)['accepted'])
if __name__=='__main__':unittest.main()
