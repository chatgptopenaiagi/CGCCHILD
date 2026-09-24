/** Owned-process conformance harness only; Python executable is supplied by the test owner. */
import {spawn} from 'node:child_process';
import {readSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createConformanceClient,MAX_RESPONSE} from './mcp_conformance_client.mjs';
const storage=Buffer.alloc(16385);let size=0;
while(size<storage.length){const n=readSync(0,storage,size,storage.length-size,null);if(!n)break;size+=n;}
const client=createConformanceClient(storage.subarray(0,size));
const mode=process.argv[3]??'ADAPTER';
const modes=['ADAPTER','MALFORMED','OVERSIZE','TRUNCATED','STDERR','SILENT','EXTRA_FRAME','EARLY_EXIT'];
if(![3,4].includes(process.argv.length)||!modes.includes(mode))throw new Error('FIXED_TEST_SELECTOR_REQUIRED');
const root=fileURLToPath(new URL('../../',import.meta.url));
const argv=mode==='ADAPTER'?['-B','-m','cgc.experimental.mcp_stdio','--snapshot-stdin','--snapshot-digest',client.snapshotDigest]:
  ['-B',root+'tests/helpers/child_mcp_fault_peer.py',mode];
const child=spawn(process.argv[2],argv,
  {cwd:root,env:{...process.env,PYTHONPATH:root+'src'},stdio:['pipe','pipe','pipe'],windowsHide:true,shell:false});
let buffer=Buffer.alloc(0),waiting=null,failed=false,stderr=0,total=0,reason=null;
const closed=new Promise(resolve=>child.once('close',(code,signal)=>{if(waiting)fail('EARLY_CLOSE');resolve({code,signal});}));
function fail(cause){
  if(failed)return;
  reason=cause;failed=true;client.invalidate();
  if(waiting){waiting.reject(new Error('OWNED_TRANSPORT_REFUSED'));waiting=null;}
  child.stdin.destroy();child.kill();
}
const timer=setTimeout(()=>fail('TIMEOUT'),5000);
child.on('error',()=>fail('PROCESS_ERROR'));child.stdin.on('error',()=>fail('INPUT_ERROR'));
child.stderr.on('data',data=>{stderr+=data.length;fail('STDERR');});
child.stdout.on('data',data=>{
  total+=data.length;
  if(failed)return;
  if(!waiting){fail('UNEXPECTED_DATA');return;}
  if(total>5*MAX_RESPONSE||data.length>MAX_RESPONSE-buffer.length){fail('FRAME_LIMIT');return;}
  buffer=Buffer.concat([buffer,data]);const at=buffer.indexOf(10);
  if(at!==-1){
    if(at!==buffer.length-1){fail('FRAME_EXTRA');return;}
    const frame=buffer;buffer=Buffer.alloc(0);const waiter=waiting;waiting=null;waiter.resolve(frame);
  }
});
child.stdout.on('end',()=>{if(waiting||buffer.length)fail('EOF');});
try {
  child.stdin.write(client.snapshot());let requests=0;
  for(;;){
    const next=client.next();if(next===null)break;requests++;
    const pending=next.expectsResponse?new Promise((resolve,reject)=>{waiting={resolve,reject};}):null;
    child.stdin.write(next.bytes);
    if(pending)client.accept(await pending);
  }
  child.stdin.end();const result=await closed;
  if(failed||result.code!==0||result.signal!==null||stderr||buffer.length)throw new Error('OWNED_TRANSPORT_REFUSED');
  const report=client.finish();clearTimeout(timer);
  console.log(JSON.stringify({...report,requests,owned_process_exit:0}));
} catch {
  fail('PROTOCOL');await closed;clearTimeout(timer);
  console.log(JSON.stringify({status:'OWNED_TRANSPORT_REFUSED',reason,mode,owned_process_closed:true,authority:'NONE'}));
  process.exitCode=2;
}
