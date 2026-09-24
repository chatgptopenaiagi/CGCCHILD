import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createAssembler,AssemblyError,CHUNK_BYTES,MAX_BYTES} from './capsule_chunks.mjs';
const hash=x=>createHash('sha256').update(x).digest('hex');
const wire=value=>Buffer.from(JSON.stringify(Object.fromEntries(Object.keys(value).sort().map(k=>[k,value[k]])))+'\n');
const packet=(raw,offset)=>wire({offset,total_bytes:raw.length,capsule_sha256:hash(raw),chunk_sha256:hash(raw.subarray(offset,offset+CHUNK_BYTES)),
 data:raw.subarray(offset,offset+CHUNK_BYTES).toString('base64'),encoding:'base64',done:offset+CHUNK_BYTES>=raw.length});
const setup=raw=>createAssembler({total_bytes:raw.length,capsule_sha256:hash(raw)});
let cases=0;
for(const size of [1,CHUNK_BYTES-1,CHUNK_BYTES,CHUNK_BYTES+1,MAX_BYTES]){
 const raw=Buffer.alloc(size,42),receiver=setup(raw);
 for(let offset=0;offset<size;offset+=CHUNK_BYTES)receiver.accept(packet(raw,offset));
 const view=receiver.finish();assert.deepEqual(view.bytes(),raw);assert.equal(view.capsule_validation,'NOT_PERFORMED');
 const copy=view.bytes();copy[0]=0;assert.deepEqual(view.bytes(),raw);
 assert.throws(()=>receiver.finish(),AssemblyError);cases++;
}
const raw=Buffer.alloc(CHUNK_BYTES+1,42);
for(const kind of ['early_finish','repeat','reorder','invalidate','after_complete','mutated_anchor']){
 const receiver=setup(raw);
 if(kind==='early_finish')assert.throws(()=>receiver.finish(),AssemblyError);
 if(kind==='repeat'){receiver.accept(packet(raw,0));assert.throws(()=>receiver.accept(packet(raw,0)),AssemblyError);}
 if(kind==='reorder')assert.throws(()=>receiver.accept(packet(raw,CHUNK_BYTES)),AssemblyError);
 if(kind==='invalidate'){receiver.invalidate();assert.throws(()=>receiver.accept(packet(raw,0)),AssemblyError);}
 if(kind==='after_complete'){receiver.accept(packet(raw,0));receiver.accept(packet(raw,CHUNK_BYTES));assert.throws(()=>receiver.accept(packet(raw,0)),AssemblyError);}
 if(kind==='mutated_anchor'){
  const expected={total_bytes:1,capsule_sha256:hash(Buffer.from('a'))};const r=createAssembler(expected);expected.capsule_sha256=hash(Buffer.from('b'));
  assert.throws(()=>r.accept(packet(Buffer.from('b'),0)),AssemblyError);cases++;continue;
 }
 assert.throws(()=>receiver.accept(packet(raw,0)),AssemblyError);cases++;
}
for(const expected of [null,{},[],{total_bytes:0,capsule_sha256:'0'.repeat(64)},
 {total_bytes:MAX_BYTES+1,capsule_sha256:'0'.repeat(64)},{total_bytes:true,capsule_sha256:'0'.repeat(64)}]){
 assert.throws(()=>createAssembler(expected),AssemblyError);cases++;
}
process.stdout.write(JSON.stringify({status:'PASS',cases})+'\n');
