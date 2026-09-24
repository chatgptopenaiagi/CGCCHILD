"""Fixed Node continuity transcript against owned Python adapter only."""
import json,shutil,subprocess,sys,unittest
from pathlib import Path
from cgc.experimental import continuity as co,snapshot_profiles as profiles,capsule,mcp_stdio as mcp
from test_child_mcp import init,req
import test_child_continuity as small
import test_child_chunks as large
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('node'),'Node unavailable')
class ContinuityClient(unittest.TestCase):
 def run_node(self,value,mode=None):
  args=['node',str(ROOT/'sdk/javascript/mcp_continuity_owned_process.mjs'),sys.executable]
  if mode:args.append(mode)
  return subprocess.run(args,input=profiles.encode(value),capture_output=True,timeout=25)
 def test_small_large_owned_sessions(self):
  for value in [co.project(small.source_state(),portable_project_id='small'),large.large_state()]:
   count=(len(capsule.export_capsule(value))+32767)//32768
   p=self.run_node(value);self.assertEqual((p.returncode,p.stderr),(0,b''));self.assertEqual(json.loads(p.stdout),dict(status='PAIRED_TRANSCRIPT_MATCH',responses=count+2,authority='NONE',snapshot_digest=profiles.digest(value),freshness='HISTORICAL_UNVERIFIED',requests=count+3,owned_process_exit=0))
 def test_owned_protocol_faults_close(self):
  value=co.project(small.source_state(),portable_project_id='small')
  for mode in ['MALFORMED','OVERSIZE','TRUNCATED','STDERR','EXTRA_FRAME','EARLY_EXIT']:
   p=self.run_node(value,mode);self.assertEqual((p.returncode,p.stderr),(2,b''));r=json.loads(p.stdout);self.assertEqual(r['status'],'OWNED_TRANSPORT_REFUSED');self.assertTrue(r['owned_process_closed']);self.assertEqual(r['authority'],'NONE')
 def test_silent_owned_peer_times_out(self):
  value=co.project(small.source_state(),portable_project_id='small');p=self.run_node(value,'SILENT');self.assertEqual((p.returncode,p.stderr),(2,b''));r=json.loads(p.stdout);self.assertEqual(r['reason'],'TIMEOUT');self.assertTrue(r['owned_process_closed'])
 def test_transcript_substitution_is_terminal(self):
  value=co.project(small.source_state(),portable_project_id='small');adapter=mcp.MCPAdapter(profiles.encode(value));digest=profiles.digest(value);frames=[adapter.handle(init())];adapter.handle(req('notifications/initialized',identifier=None))
  frames.append(adapter.handle(req('tools/call',{'name':'cgcchild_capabilities','arguments':{'snapshot_digest':digest}},identifier=2)))
  for index,offset in enumerate(range(0,len(capsule.export_capsule(value)),32768),3):frames.append(adapter.handle(req('tools/call',{'name':'cgcchild_capsule_chunk','arguments':{'snapshot_digest':digest,'offset':offset}},identifier=index)))
  cases=[frames]
  for i,frame in enumerate(frames):
   for bad in [frame[:-1],b' '+frame,frame+b'X',frame+frame,b'{}\n',frame.replace(b'"id":',b'"id":999,"id":',1)]:
    row=frames.copy();row[i]=bad;cases.append(row)
  row=frames.copy();obj=json.loads(row[-1]);obj['result']['structuredContent']['mutation_authorized']=True;row[-1]=mcp.wire(obj);cases.append(row)
  cases.extend([frames[:-1],frames+[frames[-1]]])
  payload=dict(snapshot=profiles.encode(value).hex(),cases=[[f.hex() for f in row] for row in cases]);p=subprocess.run(['node',str(ROOT/'sdk/javascript/mcp_continuity_vectors.mjs')],input=json.dumps(payload).encode(),capture_output=True,timeout=20)
  self.assertEqual((p.returncode,p.stderr),(0,b''));rows=json.loads(p.stdout);self.assertTrue(rows[0]['accepted']);self.assertEqual(rows[0]['authority'],'NONE');self.assertTrue(all(r==dict(accepted=False,terminal=True) for r in rows[1:]))
if __name__=='__main__':unittest.main()
