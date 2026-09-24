/** Offline bounded corpus adapter only; not a product transport. */
import {importCapsule,exportCapsule} from './continuity_capsule.mjs';
import {encodeContinuity as encodeState} from './continuity.mjs';
import {readSync} from 'node:fs';
const storage=Buffer.alloc(8*1024*1024+1);let size=0;
while(size<storage.length){const n=readSync(0,storage,size,storage.length-size,null);if(!n)break;size+=n;}
if(size>8*1024*1024)throw new Error('CORPUS_LIMIT');
const input=storage.subarray(0,size);
const cases=JSON.parse(input.toString('ascii'));
if(!Array.isArray(cases)||cases.length>5000)throw new Error('CORPUS_LIMIT');
const result=cases.map(text=>{
  if(typeof text!=='string'||text.length>4235264||text.length%2||/^[0-9a-f]*$/.exec(text)?.[0]!==text)return {accepted:false};
  try {
    const input=Buffer.from(text,'hex'),view=importCapsule(input),state=view.snapshot();input.fill(0);const detached=view.snapshot();detached.current_safe_to_resume='YES';if(!Object.isFrozen(view)||view.snapshot().current_safe_to_resume!=='UNKNOWN')throw Error();
    return {accepted:true,hex:exportCapsule(state).toString('hex'),state:encodeState(state).toString('ascii'),
      integrity:view.integrity,freshness:view.freshness,authority:view.authority};
  }catch{return {accepted:false};}
});
process.stdout.write(JSON.stringify(result));
