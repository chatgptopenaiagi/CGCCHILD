"""Actual bounded Node pipe presentation; no archive extraction or path disclosure."""
import hashlib,json,shutil,subprocess,unittest
from pathlib import Path
from cgc.experimental import capsule,continuity as co,snapshot_profiles as profiles
import test_child_continuity as fixtures
import test_child_chunks as large
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class NodeStatus(unittest.TestCase):
 def run_node(self,raw,args):return subprocess.run(['node',str(ROOT/'sdk/javascript/continuity_status_stdio.mjs'),*args],input=raw,capture_output=True,timeout=20)
 def test_exact_json_summary_and_no_notes(self):
  for value in [co.project(fixtures.source_state(),portable_project_id='opaque'),large.large_state()]:
   raw=capsule.export_capsule(value);p=self.run_node(raw,['json']);self.assertEqual((p.returncode,p.stderr),(0,b''));expected=dict(version='cgcchild-continuity-status-0.1-experimental',**co.summary(value),capsule_sha256=hashlib.sha256(raw).hexdigest(),snapshot_sha256=profiles.digest(value),integrity='CONSISTENT_UNSIGNED_BYTES',authority='NONE',source_authenticated=False)
   self.assertEqual(p.stdout,(json.dumps(expected,sort_keys=True,separators=(',',':'))+'\n').encode());self.assertLessEqual(len(p.stdout),4096);self.assertNotIn(value['source_state']['project_request'].encode(),p.stdout)
 def test_human_historical_labels(self):
  value=co.project(fixtures.source_state(),portable_project_id='opaque');p=self.run_node(capsule.export_capsule(value),['text']);self.assertEqual((p.returncode,p.stderr),(0,b''))
  for text in [b'Saved latest attempt: FAILED',b'HISTORICAL_UNVERIFIED',b'Current safe to resume: UNKNOWN',b'authority: NONE',b'NOT CHECKED']:self.assertIn(text,p.stdout)
  self.assertNotIn(b'/owned-fixture',p.stdout);self.assertNotIn(b'synthetic failure',p.stdout)
 def test_invalid_input_and_arguments_never_output_success(self):
  raw=capsule.export_capsule(co.project(fixtures.source_state(),portable_project_id='opaque'))
  for data,args in [(raw,[]),(raw,['json','extra']),(raw,['unknown']),(raw[:-1],['json']),(raw+b'X',['text']),(b'bad',['json']),(b'',['text'])]:
   p=self.run_node(data,args);self.assertEqual((p.returncode,p.stdout,p.stderr),(2,b'',b'CGCCHILD_CONTINUITY_STATUS_REFUSED\n'))
 def test_maximum_input_bound(self):
  p=self.run_node(b'X'*(capsule.MAX_BYTES+1),['json']);self.assertEqual((p.returncode,p.stdout,p.stderr),(2,b'',b'CGCCHILD_CONTINUITY_STATUS_REFUSED\n'))
if __name__=='__main__':unittest.main()
