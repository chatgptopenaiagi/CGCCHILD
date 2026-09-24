"""Pure historical receipt parity; no filesystem observation."""
import copy, hashlib, json, shutil, subprocess, unittest
from pathlib import Path
from cgc.inspection import validate_inspection, CODES
ROOT=Path(__file__).resolve().parents[1]
def wire(x):return (json.dumps(x,sort_keys=True,ensure_ascii=True)+'\n').encode('ascii')
def receipt(s):return dict(schema_version='cgc-inspection-v3.0-provisional',status='OBSERVED',error_code=None,snapshot=s,inspection_digest=hashlib.sha256(wire(s)[:-1]).hexdigest(),safe_to_resume='UNKNOWN',automatic_mutation_authorized=False)
def sample():return receipt(dict(head='a'*40,branch='main',detached=False,upstream=None,ahead=None,behind=None,changes=[],project_request='/opaque',root='/opaque',repository_identity=dict(device=2**64-1,inode=2**53+1,git_device=1,git_inode=2),observed_at='2026-09-24T01:02:03Z',evidence_basis='LOCAL_OBSERVATION',consistency='REPEATED_OBSERVATION_NOT_ATOMIC',remotes=['origin'],remote_state='NOT_QUERIED',operations=[],linked_worktrees_present=False,submodules=[],submodule_worktrees='NOT_INSPECTED',document_candidates=['AGENTS.md'],instructions='NOT_READ',test_command='UNKNOWN',nested_repositories=[],hidden_index_paths=[]))
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class InspectionParity(unittest.TestCase):
 def rows(self,rows):
  for start in range(0,len(rows),32):
   group=rows[start:start+32];p=subprocess.run(['node',str(ROOT/'sdk/javascript/inspection_conformance.mjs')],input=json.dumps([r.hex() for r,v in group]).encode(),capture_output=True,timeout=15)
   self.assertEqual((p.returncode,p.stderr),(0,b''));self.assertEqual(json.loads(p.stdout),[dict(accepted=True,hex=r.hex()) if v else dict(accepted=False) for r,v in group])
 def oracle(self,values):
  rows=[]
  for v in values:
   try:validate_inspection(v);valid=True
   except (ValueError,TypeError):valid=False
   rows.append((wire(v),valid))
  self.rows(rows)
 def test_positive_and_refusals(self):
  values=[sample()]
  for code in sorted(CODES):
   r=sample();r.update(status='REFUSED',error_code=code,snapshot=None,inspection_digest=None);values.append(r)
  for n in [0,2**53+1,2**64-1,10**4299]:
   s=sample()['snapshot'];s['repository_identity']['inode']=n;values.append(receipt(s))
  self.oracle(values)
 def test_substitutions(self):
  values=[];base=sample()
  for key in base:
   for bad in [None,True,False,0,[],{},'unexpected']:
    r=copy.deepcopy(base);r[key]=bad;values.append(r)
  for key in base['snapshot']:
   for bad in [None,True,False,0,[],{},'unexpected']:
    s=copy.deepcopy(base['snapshot']);s[key]=bad;values.append(receipt(s))
  self.oracle(values)
 def test_paths_dates_and_digest(self):
  values=[]
  for path in ['/absolute','..','a/../b','.git/a','a//b','./x','', 'ordinary/', 'é😀']:
   s=sample()['snapshot'];s['hidden_index_paths']=[path];values.append(receipt(s))
  for stamp in ['0001-01-01T00:00:00Z','2024-02-29T23:59:59.123456Z','2023-02-29T00:00:00Z','2024-01-01T00:00:00.000000Z']:
   s=sample()['snapshot'];s['observed_at']=stamp;values.append(receipt(s))
  r=sample();r['inspection_digest']='0'*64;values.append(r);self.oracle(values)
 def test_corrupt_wire(self):
  raw=wire(sample());rows=[]
  for i in range(0,len(raw),17):
   b=bytearray(raw);b[i]^=128;rows.extend([(bytes(b),False),(raw[:i],False)])
  rows.extend([(raw+b' ',False),(raw.replace(b'9007199254740993',b'9007199254740992'),False)])
  self.rows(rows)
if __name__=='__main__':unittest.main()
