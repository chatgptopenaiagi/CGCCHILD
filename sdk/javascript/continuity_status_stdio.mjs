/** Explicit stdin/stdout consumer. No filenames, network, extraction or child launch. */
import {readSync,writeSync} from 'node:fs';
import {MAX_CAPSULE_BYTES} from './continuity_capsule.mjs';
import {capsuleStatus} from './continuity_status.mjs';
try{
 if(process.argv.length!==3||!['json','text'].includes(process.argv[2]))throw Error();
 const buffer=Buffer.alloc(MAX_CAPSULE_BYTES+1);let size=0;
 while(size<buffer.length){const n=readSync(0,buffer,size,buffer.length-size,null);if(n===0)break;size+=n;}
 if(size>MAX_CAPSULE_BYTES)throw Error();const output=capsuleStatus(buffer.subarray(0,size),process.argv[2]);
 let at=0;while(at<output.length){const n=writeSync(1,output,at,output.length-at);if(n<=0)throw Error();at+=n;}
}catch{try{writeSync(2,Buffer.from('CGCCHILD_CONTINUITY_STATUS_REFUSED\n'));}catch{}process.exitCode=2;}
