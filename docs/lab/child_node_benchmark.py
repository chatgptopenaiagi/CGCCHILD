"""Fixed three-case Node engineering benchmark; no production acceptance."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from cgc.experimental import capsule,continuity
from test_child_continuity import source_state
from test_child_chunks import large_state
from test_child_javascript_handoff import resign
FILES=['tests/test_child_continuity.py','tests/test_child_chunks.py','tests/test_child_javascript_handoff.py','src/cgc/experimental/capsule.py','src/cgc/experimental/continuity.py','src/cgc/experimental/snapshot_profiles.py','docs/lab/child_node_benchmark.py','docs/lab/child_node_benchmark.mjs']+['sdk/javascript/'+n+'.mjs' for n in ['integer_json','preservation','inspection','handoff','continuity','continuity_capsule','continuity_status']]
def cases():
 small=continuity.project(source_state(),portable_project_id='small');source=source_state();slot=source['last_known_good']
 for field in ['complete','partial']:slot['record']['notes'][field]=['synthetic-'+str(i)+'-'+'x'*1800 for i in range(60)]
 source['previous_known_good']=copy.deepcopy(slot);slot['generation']=3;source['generation']=4
 return [('small',small),('medium',large_state()),('two_large_slots',continuity.project(resign(source),portable_project_id='two-slots'))]
def main():
 out={'production_accepted':False,'source_digest_basis':'UTF8_LF_NORMALIZED','source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in FILES},'cases':{}}
 for name,value in cases():
  raw=capsule.export_capsule(value);p=subprocess.run(['node',str(ROOT/'docs/lab/child_node_benchmark.mjs')],input=raw,capture_output=True,timeout=30,check=True)
  if p.stderr:raise RuntimeError('BENCHMARK_STDERR')
  row=json.loads(p.stdout);assert row['input_sha256']==hashlib.sha256(raw).hexdigest();out['cases'][name]=row
 print(json.dumps(out,sort_keys=True,indent=2))
if __name__=='__main__':main()
