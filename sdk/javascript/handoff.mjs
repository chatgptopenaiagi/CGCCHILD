/** Historical handoff integrity only; no storage, repository access or authority. */
import {createHash} from 'node:crypto';
import {encodeIntegerJson,decodeIntegerJson} from './integer_json.mjs';
import {validateRecord} from './preservation.mjs';
import {validateInspection} from './inspection.mjs';
export const VERSION='cgc-handoff-v3.0-provisional',MAX_BYTES=2097152;
export class HandoffError extends Error {constructor(){super('INVALID_HANDOFF');}}
const fail=()=>{throw new HandoffError();};
function keys(x,k){if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).sort().join('\0')!==[...k].sort().join('\0'))fail();}
function stamp(x){if(typeof x!=='string')fail();const m=/^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{6}))?Z$/.exec(x);if(!m||m[0]!==x||x.startsWith('0000')||m[2]==='000000')fail();const d=new Date(m[1]+'Z');if(!Number.isFinite(d.getTime())||d.toISOString().slice(0,19)!==m[1])fail();return m[1]+'.'+(m[2]??'000000');}
function generation(x,max=9007199254740991){if(!Number.isSafeInteger(x)||x<1||x>max)fail();}
function slot(s,project,g,at){
 keys(s,['generation','published_at','content_basis','record','inspection','digest']);generation(s.generation,g);
 if(s.content_basis!=='OPERATOR_CURATED'||stamp(s.published_at)>stamp(at))fail();
 const r=validateRecord(s.record);if(r.project_request!==project||stamp(r.events.at(-1).at)>stamp(s.published_at))fail();
 if(s.inspection===null){if(r.evidence.inspection_digest!==null)fail();}
 else{const i=validateInspection(s.inspection);if(i.status!=='OBSERVED'||i.snapshot.root!==project||i.inspection_digest!==r.evidence.inspection_digest||stamp(i.snapshot.observed_at)>stamp(s.published_at))fail();}
 const unsigned=Object.fromEntries(Object.entries(s).filter(([k])=>k!=='digest'));
 if(createHash('sha256').update(encodeIntegerJson(unsigned,true)).digest('hex')!==s.digest)fail();
}
function check(s){
 keys(s,['schema_version','scope','project_request','generation','latest_attempt','last_known_good','previous_known_good','safe_to_resume','automatic_mutation_authorized']);
 if(s.schema_version!==VERSION||s.scope!=='CONTINUITY_ONLY'||s.safe_to_resume!=='UNKNOWN'||s.automatic_mutation_authorized!==false)fail();
 const p=s.project_request;if(typeof p!=='string'||!p.startsWith('/')||[...p].length>2048||p.split('/').slice(1).some(x=>['','.','..'].includes(x))||/[\x00-\x1f\x7f]/.test(p))fail();
 generation(s.generation);const l=s.latest_attempt;keys(l,['status','at','error_code','handoff_digest']);stamp(l.at);
 const good=s.last_known_good,previous=s.previous_known_good;for(const x of [good,previous])if(x!==null)slot(x,p,s.generation,l.at);
 if(previous!==null&&(good===null||previous.generation>=good.generation||stamp(previous.published_at)>stamp(good.published_at)))fail();
 if(l.status==='PUBLISHED'){if(good===null||good.generation!==s.generation||good.published_at!==l.at||l.error_code!==null||l.handoff_digest!==good.digest)fail();}
 else if(l.status==='FAILED'){if(!['INPUT_REJECTED','INSPECTION_FAILED','WRITE_FAILED','VERIFICATION_FAILED','CANCELLED'].includes(l.error_code)||l.handoff_digest!==null||good!==null&&good.generation>=s.generation)fail();}
 else fail();
 const bytes=encodeIntegerJson(s,true);if(bytes.length>MAX_BYTES)fail();
 if(/(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|https?:\/\/[^\x09-\x0d\x20/":]+:[^\x09-\x0d\x20/"@]+@)/.test(bytes.toString('ascii')))fail();
 return s;
}
export function validateHandoff(value){try{return check(decodeIntegerJson(encodeIntegerJson(value,true),true));}catch{fail();}}
export function encodeHandoff(value){return encodeIntegerJson(validateHandoff(value),true);}
export function decodeHandoff(bytes){try{if(bytes.length>MAX_BYTES)fail();return check(decodeIntegerJson(bytes,true));}catch{fail();}}
export function historicalHandoff(value){const bytes=encodeHandoff(value);return Object.freeze({current_safe_to_resume:'UNKNOWN',authority:'NONE',mutation_authorized:false,receipts_authenticated:false,record:()=>decodeHandoff(bytes),bytes:()=>Buffer.from(bytes)});}
