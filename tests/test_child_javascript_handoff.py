"""Independent Node handoff binding parity against unchanged Python validator."""
import copy,hashlib,json,shutil,subprocess,unittest
from pathlib import Path
from cgc.handoff import validate_state,HandoffError
import test_child_continuity as fixtures
import test_child_javascript_inspection as inspections
ROOT=Path(__file__).resolve().parents[1]
def wire(x):return (json.dumps(x,sort_keys=True,ensure_ascii=True,separators=(',',':'))+'\n').encode('ascii')
def resign(s):
 for key in ['last_known_good','previous_known_good']:
  slot=s[key]
  if slot is not None:slot['digest']=hashlib.sha256(wire({k:v for k,v in slot.items() if k!='digest'})).hexdigest()
 if s['latest_attempt']['status']=='PUBLISHED':s['latest_attempt']['handoff_digest']=s['last_known_good']['digest']
 return s
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class HandoffParity(unittest.TestCase):
 def rows(self,rows):
  for start in range(0,len(rows),24):
   group=rows[start:start+24];p=subprocess.run(['node',str(ROOT/'sdk/javascript/handoff_conformance.mjs')],input=json.dumps([r.hex() for r,v in group]).encode(),capture_output=True,timeout=15)
   self.assertEqual((p.returncode,p.stderr),(0,b''));self.assertEqual(json.loads(p.stdout),[dict(accepted=True,hex=r.hex()) if v else dict(accepted=False) for r,v in group])
 def oracle(self,values):
  rows=[]
  for v in values:
   try:validate_state(v);valid=True
   except (HandoffError,ValueError,TypeError):valid=False
   rows.append((wire(v),valid))
  self.rows(rows)
 def test_slots_and_inspection_identity(self):
  base=fixtures.source_state();values=[base]
  s=copy.deepcopy(base);s['last_known_good']=None;values.append(s)
  s=copy.deepcopy(base);s['generation']=1;s['latest_attempt'].update(status='PUBLISHED',error_code=None,handoff_digest=s['last_known_good']['digest']);values.append(s)
  s=copy.deepcopy(base);s['previous_known_good']=copy.deepcopy(s['last_known_good']);s['generation']=4;s['last_known_good']['generation']=3;values.append(resign(s))
  s=copy.deepcopy(base);snap=inspections.sample()['snapshot'];snap['root']=snap['project_request']=s['project_request'];i=inspections.receipt(snap);s['last_known_good']['inspection']=i;s['last_known_good']['record']['evidence']['inspection_digest']=i['inspection_digest'];values.append(resign(s))
  self.oracle(values)
 def test_all_field_substitutions(self):
  base=fixtures.source_state();values=[]
  for key in base:
   for bad in [None,True,0,[],{},'unexpected']:
    s=copy.deepcopy(base);s[key]=bad;values.append(s)
  for key in base['last_known_good']:
   for bad in [None,True,0,[],{},'unexpected']:
    s=copy.deepcopy(base);s['last_known_good'][key]=bad;values.append(s)
  for key in base['latest_attempt']:
   for bad in [None,True,0,[],{},'unexpected']:
    s=copy.deepcopy(base);s['latest_attempt'][key]=bad;values.append(s)
  self.oracle(values)
 def test_binding_and_time_failures(self):
  values=[];base=fixtures.source_state()
  for path in ['/other','/a/../b','/','/trailing/']:
   s=copy.deepcopy(base);s['project_request']=path;values.append(resign(s))
  for stamp in ['2025-01-01T00:00:00Z','2027-01-01T00:00:00Z','2026-09-24T12:00:00.000001Z','bad']:
   s=copy.deepcopy(base);s['last_known_good']['published_at']=stamp;values.append(resign(s))
  s=copy.deepcopy(base);s['last_known_good']['record']['notes']['mission']='changed without digest';values.append(s)
  self.oracle(values)
 def test_wire_and_authority_refusal(self):
  raw=wire(fixtures.source_state());rows=[]
  for i in range(0,len(raw),47):
   b=bytearray(raw);b[i]^=128;rows.extend([(bytes(b),False),(raw[:i],False)])
  rows.extend([(raw+b' ',False),(raw.replace(b'"generation":2',b'"generation":2,"generation":2'),False),(raw.replace(b'"safe_to_resume":"UNKNOWN"',b'"safe_to_resume":"YES"'),False)])
  self.rows(rows)
if __name__=='__main__':unittest.main()
