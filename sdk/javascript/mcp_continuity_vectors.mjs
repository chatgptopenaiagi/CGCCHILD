/** Offline transcript harness; no product transport. */
import {readSync} from 'node:fs';
import {createConformanceClient,MAX_RESPONSE} from './mcp_continuity_client.mjs';
const buffer=Buffer.alloc(12*1024*1024+1);let size=0;
while(size<buffer.length){const n=readSync(0,buffer,size,buffer.length-size,null);if(!n)break;size+=n;}
if(size>12*1024*1024)throw new Error('CORPUS_LIMIT');
const input=JSON.parse(buffer.subarray(0,size).toString('ascii'));
if(!Array.isArray(input.cases)||input.cases.length>100||typeof input.snapshot!=='string'||input.snapshot.length>4202496)throw new Error('CORPUS_LIMIT');
const results=input.cases.map(frames=>{
  const client=createConformanceClient(Buffer.from(input.snapshot,'hex'));let at=0;
  try {
    if(!Array.isArray(frames)||frames.length>68)throw new Error();
    for(;;){
      const next=client.next();if(next===null)break;
      if(next.expectsResponse){
        const hex=frames[at++];
        if(typeof hex!=='string'||hex.length>2*(MAX_RESPONSE+1)||hex.length%2||/^[0-9a-f]*$/.exec(hex)?.[0]!==hex)throw new Error();
        client.accept(Buffer.from(hex,'hex'));
      }
    }
    if(at!==frames.length)throw new Error();
    return {accepted:true,...client.finish()};
  } catch {
    client.invalidate();let terminal=false;
    try{client.next();}catch{terminal=true;}
    return {accepted:false,terminal};
  }
});
console.log(JSON.stringify(results));
