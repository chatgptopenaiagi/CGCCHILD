"""Node continuity capsule0.2 parity, hostile metadata and detached views."""
import io,json,shutil,stat,subprocess,unittest,zipfile
from pathlib import Path
from cgc.experimental import capsule as cap,continuity as co
import test_child_continuity as fixtures
import test_child_javascript_handoff as handoffs
import test_child_state_protocol as models
ROOT=Path(__file__).resolve().parents[1]
def value():return co.project(fixtures.source_state(),portable_project_id='opaque')
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class ContinuityCapsule(unittest.TestCase):
 def parity(self,cases):
  for start in range(0,len(cases),24):
   group=cases[start:start+24];expected=[]
   for raw in group:
    try:
     view=cap.import_capsule(raw);state=co.encode(view.snapshot()).decode('ascii');expected.append(dict(accepted=True,hex=cap.export_capsule(view.snapshot()).hex(),state=state,integrity=view.integrity,freshness=view.freshness,authority=view.authority))
    except (ValueError,cap.CapsuleError):expected.append(dict(accepted=False))
   p=subprocess.run(['node',str(ROOT/'sdk/javascript/continuity_capsule_conformance.mjs')],input=json.dumps([r.hex() for r in group]).encode(),capture_output=True,timeout=30)
   self.assertEqual((p.returncode,p.stderr),(0,b''));self.assertEqual(json.loads(p.stdout),expected)
 def test_positive_and_large(self):
  states=[value()];s=fixtures.source_state();s['last_known_good']=None;states.append(co.project(s,portable_project_id='empty'))
  s=fixtures.source_state();s['last_known_good']['record']['notes']['complete']=['note '+str(i)+'x'*1800 for i in range(60)];states.append(co.project(handoffs.resign(s),portable_project_id='large'))
  self.parity([cap.export_capsule(s) for s in states])
 def test_hostile_metadata(self):
  raw=cap.export_capsule(value());cases=[]
  for field,v in [('filename','../state.json'),('filename','/state.json'),('external_attr',(stat.S_IFLNK|0o777)<<16),('compress_type',zipfile.ZIP_DEFLATED),('comment',b'extra'),('extra',bytes([1,0,0,0])),('date_time',(2026,1,1,0,0,0))]:
   out=io.BytesIO()
   with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,'w') as target:
    for info in source.infolist():
     data=source.read(info)
     if info.filename=='state.json':setattr(info,field,v)
     target.writestr(info,data)
   cases.append(out.getvalue())
  cases.extend([b'prefix'+raw,raw+b'suffix',raw+raw,cap.export_capsule(models.state())]);self.parity(cases)
 def test_boundaries_and_corruption(self):
  raw=cap.export_capsule(value());cases=[]
  for i in range(0,len(raw),37):
   b=bytearray(raw);b[i]^=128;cases.extend([bytes(b),raw[:i]])
  cases.extend([raw[:i] for i in range(max(0,len(raw)-24),len(raw))]);self.parity(cases)
 def test_crc_consistent_tampering(self):
  raw=cap.export_capsule(value());cases=[]
  for member in cap.NAMES:
   out=io.BytesIO()
   with zipfile.ZipFile(io.BytesIO(raw)) as source,zipfile.ZipFile(out,'w') as target:
    for info in source.infolist():
     data=source.read(info)
     if info.filename==member:data+=b'X'
     target.writestr(info,data)
   cases.append(out.getvalue())
  self.parity(cases)
if __name__=='__main__':unittest.main()
