/** Fixed inert engineering benchmark; no acceptance threshold. */
import {readSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {importCapsule,exportCapsule,MAX_CAPSULE_BYTES} from '../../sdk/javascript/continuity_capsule.mjs';
import {capsuleStatus} from '../../sdk/javascript/continuity_status.mjs';
const buffer=Buffer.alloc(MAX_CAPSULE_BYTES+1);let size=0;
while(size<buffer.length){const n=readSync(0,buffer,size,buffer.length-size,null);if(!n)break;size+=n;}
if(size>MAX_CAPSULE_BYTES)throw Error('INPUT_BOUND');const raw=buffer.subarray(0,size),hash=x=>createHash('sha256').update(x).digest('hex');
function measure(fn){const samples=[];let expected=null;const before=process.memoryUsage().heapUsed;
 for(let i=0;i<3;i++){const start=performance.now(),out=fn();samples.push(performance.now()-start);const digest=hash(out);if(expected!==null&&expected!==digest)throw Error('NONDETERMINISTIC');expected=digest;}
 return {samples_ms:samples,min_ms:Math.min(...samples),max_ms:Math.max(...samples),median_ms:[...samples].sort((a,b)=>a-b)[1],output_sha256:expected,heap_before_bytes:before,heap_after_bytes:process.memoryUsage().heapUsed};}
const roundtrip=measure(()=>exportCapsule(importCapsule(raw).snapshot()));if(roundtrip.output_sha256!==hash(raw))throw Error('BYTE_MISMATCH');
const status=measure(()=>capsuleStatus(raw,'json'));
console.log(JSON.stringify({node:process.version,platform:process.platform,arch:process.arch,input_bytes:size,input_sha256:hash(raw),roundtrip,status,production_accepted:false,scope:'SYNTHETIC_ENGINEERING_MEASUREMENT',heap_measurement:'CURRENT_SAMPLES_NOT_PEAK'}));
