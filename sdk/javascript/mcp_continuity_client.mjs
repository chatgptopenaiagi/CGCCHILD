/** Fixed paired-adapter conformance client. No transport or generic method API. */
import {decodeContinuity as decodeState,encodeContinuity as encodeState} from './continuity.mjs';
import {createHash} from 'node:crypto';
const hash=x=>createHash('sha256').update(x).digest('hex');
import {exportCapsule} from './continuity_capsule.mjs';
export const PROTOCOL='2025-11-25';
export const MAX_RESPONSE=96*1024;
export class ClientError extends Error {constructor(){super('MCP_CONFORMANCE_REFUSED');this.name='ClientError';}}
const fail=()=>{throw new ClientError();};
function canonical(value) {
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value!==null&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  return JSON.stringify(value);
}
const wire=value=>Buffer.from(canonical(value)+'\n','ascii');
export function createConformanceClient(snapshotBytes) {
  const state=decodeState(snapshotBytes),snapshot=encodeState(state),digest=hash(snapshot);
  const steps=[{
    request:wire({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:PROTOCOL,
      capabilities:{},clientInfo:{name:'cgcchild-node-conformance',version:'0.1.0'}}}),
    expected:wire({jsonrpc:'2.0',id:1,result:{protocolVersion:PROTOCOL,
      capabilities:{tools:{listChanged:false}},serverInfo:{name:'cgcchild-experimental-readonly',version:'0.1.0'}}})},
    {request:wire({jsonrpc:'2.0',method:'notifications/initialized'}),expected:null}];
  const archive=exportCapsule(state),archiveDigest=hash(archive);
  const outputs=[['cgcchild_capabilities',{methods:['capabilities.get','state.get','status.get','capsule.export','capsule.chunk'],profile:'V3_CONTINUITY_HISTORICAL',network:false,freshness:'HISTORICAL_UNVERIFIED',max_requests:128},null]];
  for(let offset=0;offset<archive.length;offset+=32768){
    const piece=archive.subarray(offset,offset+32768);
    outputs.push(['cgcchild_capsule_chunk',{offset,total_bytes:archive.length,capsule_sha256:archiveDigest,chunk_sha256:hash(piece),encoding:'base64',data:piece.toString('base64'),done:offset+piece.length===archive.length},offset]);
  }
  const expectedResponses=outputs.length+1;
  for(let i=0;i<outputs.length;i++) {
    const [name,result,offset]=outputs[i],id=i+2;
    const args=offset===null?{snapshot_digest:digest}:{snapshot_digest:digest,offset};
    const core={version:'cgcchild-readonly-0.1',id:'mcp',snapshot_digest:digest,result,mutation_authorized:false};
    steps.push({request:wire({jsonrpc:'2.0',id,method:'tools/call',params:{name,arguments:args}}),
      expected:wire({jsonrpc:'2.0',id,result:{content:[{type:'text',text:canonical(core)}],structuredContent:core,isError:false}})});
  }
  if(steps.some(x=>x.request.length>8192||(x.expected&&x.expected.length>MAX_RESPONSE)))fail();
  let index=0,pending=null,phase='OPEN',accepted=0;
  const invalidate=()=>{phase='INVALIDATED';pending=null;};
  const refusal=()=>{invalidate();fail();};
  return Object.freeze({
    snapshot:()=>Buffer.from(snapshot),snapshotDigest:digest,
    next:()=>{
      if(phase!=='OPEN'||pending!==null)return refusal();
      if(index===steps.length){phase='DONE';return null;}
      const step=steps[index++];if(step.expected)pending=step.expected;
      return Object.freeze({bytes:Buffer.from(step.request),expectsResponse:step.expected!==null});
    },
    accept:bytes=>{
      if(phase!=='OPEN'||pending===null||!(bytes instanceof Uint8Array)||bytes.byteLength<1||bytes.byteLength>MAX_RESPONSE)return refusal();
      if(!Buffer.from(bytes).equals(pending))return refusal();
      pending=null;accepted++;return Object.freeze({accepted:true,authority:'NONE',freshness:'HISTORICAL_UNVERIFIED'});
    },
    finish:()=>{
      if(phase!=='DONE'||accepted!==expectedResponses||pending!==null)return refusal();
      phase='CLOSED';return Object.freeze({status:'PAIRED_TRANSCRIPT_MATCH',responses:accepted,authority:'NONE',
        snapshot_digest:digest,freshness:'HISTORICAL_UNVERIFIED'});
    },
    invalidate
  });
}
