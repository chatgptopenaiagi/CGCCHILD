/** Inert byte assembly only. Never validates capsule semantics or authenticates a source. */
import {createHash} from 'node:crypto';
export const CHUNK_BYTES=32768,MAX_BYTES=2117632,MAX_FRAME=65536;
export class AssemblyError extends Error {constructor(){super('CAPSULE_ASSEMBLY_REFUSED');this.name='AssemblyError';}}
const fail=()=>{throw new AssemblyError();};
const hash=b=>createHash('sha256').update(b).digest('hex');
const fields=['capsule_sha256','chunk_sha256','data','done','encoding','offset','total_bytes'];
const digest=x=>typeof x==='string'&&/^[0-9a-f]{64}$/.test(x);
const wire=x=>Buffer.from(JSON.stringify(Object.fromEntries(fields.map(k=>[k,x[k]])))+'\n','ascii');
export function createAssembler(expected) {
  if(expected===null||typeof expected!=='object'||Array.isArray(expected)||
     Object.keys(expected).sort().join(',')!=='capsule_sha256,total_bytes'||
     !Number.isSafeInteger(expected.total_bytes)||expected.total_bytes<1||expected.total_bytes>MAX_BYTES||!digest(expected.capsule_sha256))fail();
  const total=expected.total_bytes,anchor=expected.capsule_sha256;
  let phase='OPEN',offset=0,pieces=[];
  const refuse=()=>{pieces=[];phase='INVALIDATED';fail();};
  return Object.freeze({
    accept:raw=>{
      try {
        if(phase!=='OPEN'||!(raw instanceof Uint8Array)||raw.byteLength<1||raw.byteLength>MAX_FRAME)fail();
        const bytes=Buffer.from(raw);
        if(bytes.some(x=>x>127))fail();
        const value=JSON.parse(bytes.toString('ascii'));
        if(value===null||typeof value!=='object'||Array.isArray(value)||Object.keys(value).sort().join(',')!==fields.join(','))fail();
        if(!wire(value).equals(bytes)||!Number.isSafeInteger(value.offset)||value.offset!==offset||
           !Number.isSafeInteger(value.total_bytes)||value.total_bytes!==total||value.capsule_sha256!==anchor||
           !digest(value.chunk_sha256)||typeof value.data!=='string'||value.data.length>4*Math.ceil(CHUNK_BYTES/3)||
           value.encoding!=='base64'||typeof value.done!=='boolean')fail();
        const piece=Buffer.from(value.data,'base64'),size=Math.min(CHUNK_BYTES,total-offset);
        if(piece.toString('base64')!==value.data||piece.length!==size||hash(piece)!==value.chunk_sha256||
           value.done!==(offset+size===total)||pieces.length>=Math.ceil(MAX_BYTES/CHUNK_BYTES))fail();
        pieces.push(piece);offset+=size;if(value.done)phase='COMPLETE';
        return Object.freeze({accepted_bytes:offset,done:value.done,authority:'NONE'});
      } catch {return refuse();}
    },
    finish:()=>{
      if(phase!=='COMPLETE')return refuse();
      const raw=Buffer.concat(pieces,total);
      if(raw.length!==total||hash(raw)!==anchor)return refuse();
      pieces=[];phase='CLOSED';
      return Object.freeze({bytes:()=>Buffer.from(raw),total_bytes:total,capsule_sha256:anchor,
        integrity:'EXPECTED_BYTES_MATCH',capsule_validation:'NOT_PERFORMED',source_authenticated:false,
        authority:'NONE',current_safe_to_resume:'UNKNOWN',mutation_authorized:false});
    },
    invalidate:()=>{pieces=[];phase='INVALIDATED';}
  });
}
