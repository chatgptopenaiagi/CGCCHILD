"""Independent continuity bytes, projection and summary parity."""
import copy,json,shutil,subprocess,unittest
from pathlib import Path
from cgc.experimental import continuity as co
import test_child_continuity as fixtures
import test_child_javascript_handoff as handoffs
import test_child_javascript_inspection as inspections
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class ContinuityParity(unittest.TestCase):
 def check(self,rows):
  for start in range(0,len(rows),16):
   group=rows[start:start+16];p=subprocess.run(['node',str(ROOT/'sdk/javascript/continuity_conformance.mjs')],input=json.dumps([raw.hex() for raw,expected in group]).encode(),capture_output=True,timeout=20)
   self.assertEqual((p.returncode,p.stderr),(0,b''));self.assertEqual(json.loads(p.stdout),[e for r,e in group])
 def oracle(self,raws):
  rows=[]
  for raw in raws:
   try:v=co.decode(raw);expected=dict(accepted=True,hex=co.encode(v).hex(),summary=co.summary(v))
   except co.ContinuityError:expected=dict(accepted=False)
   rows.append((raw,expected))
  self.check(rows)
 def test_projection_summary_and_exact_integer_bytes(self):
  states=[fixtures.source_state()]
  s=fixtures.source_state();s['last_known_good']=None;states.append(s)
  s=fixtures.source_state();s['previous_known_good']=copy.deepcopy(s['last_known_good']);s['generation']=4;s['last_known_good']['generation']=3;states.append(handoffs.resign(s))
  s=fixtures.source_state();snap=inspections.sample()['snapshot'];snap['root']=snap['project_request']=s['project_request'];i=inspections.receipt(snap);s['last_known_good']['inspection']=i;s['last_known_good']['record']['evidence']['inspection_digest']=i['inspection_digest'];states.append(handoffs.resign(s))
  self.oracle([co.encode(co.project(s,portable_project_id='opaque-project')) for s in states])
 def test_envelope_substitutions(self):
  base=co.project(fixtures.source_state(),portable_project_id='opaque');raws=[]
  for k in base:
   for bad in [None,True,0,[],{},'unexpected']:
    v=copy.deepcopy(base);v[k]=bad;raws.append(handoffs.wire(v))
  for name in ['a'*128,'a'*129,'x\r','x\n','../path','é']:
   v=copy.deepcopy(base);v['portable_project_id']=name;raws.append(handoffs.wire(v))
  self.oracle(raws)
 def test_corrupt_and_duplicate_bytes(self):
  raw=co.encode(co.project(fixtures.source_state(),portable_project_id='opaque'));raws=[]
  for i in range(0,len(raw),53):
   b=bytearray(raw);b[i]^=128;raws.extend([bytes(b),raw[:i]])
  raws.extend([raw+b' ',raw.replace(b'"generation":2',b'"generation":2,"generation":2'),raw.replace(b'"current_safe_to_resume":"UNKNOWN"',b'"current_safe_to_resume":"YES"')]);self.oracle(raws)
 def test_large_curated_record(self):
  s=fixtures.source_state();s['last_known_good']['record']['notes']['complete']=['bounded historical note '+str(i)+'x'*1800 for i in range(60)];s=handoffs.resign(s)
  raw=co.encode(co.project(s,portable_project_id='large'));self.assertGreater(len(raw),96000);self.oracle([raw])
if __name__=='__main__':unittest.main()
