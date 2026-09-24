/** Pure historical preservation record consistency. No receipts authenticated or actions executed. */
export const VERSION='cgc-preservation-v3.0-provisional',MAX_BYTES=262144;
export class RecordError extends Error {constructor(){super('INVALID_PRESERVATION_RECORD');this.name='RecordError';}}
const fail=()=>{throw new RecordError();};
const failures=['BLOCKED','FAILED','CANCELLED'],terminal=[...failures,'PRESERVED','PARTIAL'];
const next={INSPECTING:['STABILIZING','TESTING','DOCUMENTING'],STABILIZING:['TESTING','DOCUMENTING'],TESTING:['DOCUMENTING'],
 DOCUMENTING:['CHECKPOINTING','VERIFYING'],CHECKPOINTING:['PUBLISHING','VERIFYING'],PUBLISHING:['VERIFYING'],VERIFYING:['PRESERVED','PARTIAL']};
const lists=['complete','partial','not_started','files_changed','tests_run','test_results','known_failures','important_discoveries','decisions','do_not_repeat','limitations'];
const texts=['mission','next_exact_action'],digests=['inspection_digest','handoff_digest','resume_digest'],commits=['local_commit','tracking_commit','remote_commit'];
const publicationErrors=['REMOTE_UNAVAILABLE','REMOTE_MISSING','PUSH_REJECTED','AUTHENTICATION_FAILED','HOOK_REJECTED','VERIFICATION_MISMATCH'];
const derived=['preservation_status','publication_status','safe_to_resume','outcome','local_checkpoint','automatic_mutation_authorized'];
const fields=['schema_version','project_request','project_basis','trigger','requested_level','evidence_basis','phase','events','evidence','project_test_status','notes',...derived];
function keys(value,expected){
 if(value===null||typeof value!=='object'||Array.isArray(value)||Reflect.ownKeys(value).some(k=>typeof k!=='string')||
    Object.keys(value).sort().join('\0')!==[...expected].sort().join('\0'))fail();
}
function asciiString(value){return JSON.stringify(value).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));}
function canonical(value,spaced=true){
 const comma=spaced?', ':',',colon=spaced?': ':':';
 if(typeof value==='string')return asciiString(value);
 if(Array.isArray(value))return '['+value.map(v=>canonical(v,spaced)).join(comma)+']';
 if(value!==null&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>asciiString(k)+colon+canonical(value[k],spaced)).join(comma)+'}';
 return JSON.stringify(value);
}
function text(value){
 if(typeof value!=='string'||[...value].length<1||[...value].length>2048||/[\x00-\x1f\x7f]/.test(value)||
    /^[ \u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/.test(value))fail();
}
function stamp(value){
 if(typeof value!=='string')fail();
 const match=/^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{6}))?Z$/.exec(value);
 if(!match||match[0]!==value||value.startsWith('0000')||match[2]==='000000')fail();
 const date=new Date(match[1]+'Z');
 if(!Number.isFinite(date.getTime())||date.toISOString().slice(0,19)!==match[1])fail();
 return match[1]+'.'+(match[2]??'000000');
}
function conclusions(r){
 const e=r.evidence,phase=r.phase,level=r.requested_level;
 const handoff=digests.every(k=>e[k]!==null),local=e.local_commit!==null;
 const remote=local&&e.local_commit===e.tracking_commit&&e.local_commit===e.remote_commit;
 const sufficient=handoff&&(level==='HANDOFF_ONLY'||local)&&(level!=='REMOTE_VERIFIED'||remote)&&!e.unsafe_target;
 if(phase==='PRESERVED'&&!sufficient)fail();
 const publication=level!=='REMOTE_VERIFIED'?'NOT_REQUESTED':remote?'VERIFIED':local&&terminal.includes(phase)?'LOCAL_CHECKPOINT_ONLY':
   e.publication_error?'FAILED':e.push_attempted?'PUSH_ATTEMPTED':'NOT_ATTEMPTED';
 const survived=e.handoff_digest!==null||local;
 const resume=e.unsafe_target?'NO':phase==='PRESERVED'?'YES':terminal.includes(phase)&&survived?'PARTIAL':failures.includes(phase)?'NO':'UNKNOWN';
 const outcome=e.unsafe_target?'BLOCKED_UNSAFE':phase==='PRESERVED'&&remote?'REMOTE_VERIFIED':phase==='PRESERVED'&&local?'LOCAL_CHECKPOINT':
   phase==='PRESERVED'?'HANDOFF_ONLY':terminal.includes(phase)&&survived?'PARTIAL_PRESERVATION':['FAILED','CANCELLED'].includes(phase)?phase:
   phase==='BLOCKED'?'BLOCKED_UNSAFE':phase==='PARTIAL'?'PARTIAL_PRESERVATION':e.push_attempted?'REMOTE_PUSH_ATTEMPTED':'IN_PROGRESS';
 return {preservation_status:phase,publication_status:publication,safe_to_resume:resume,outcome,local_checkpoint:e.local_commit,automatic_mutation_authorized:false};
}
export function validateRecord(record){
 try {
  keys(record,fields);if(record.schema_version!==VERSION)fail();text(record.project_request);
  if(!record.project_request.startsWith('/')||record.project_request==='/'||record.project_request.split('/').includes('..'))fail();
  if(record.project_basis!=='OPERATOR_REQUESTED'||!['MANUAL','SYNTHETIC'].includes(record.trigger)||
     record.evidence_basis!==(record.trigger==='SYNTHETIC'?'SYNTHETIC':'ADAPTER_REPORTED')||
     !['HANDOFF_ONLY','LOCAL_CHECKPOINT','REMOTE_VERIFIED'].includes(record.requested_level))fail();
  if(!Array.isArray(record.events)||record.events.length<1||record.events.length>64)fail();
  let previous=null,previousStamp=null;
  for(const event of record.events){
   keys(event,['phase','at']);const at=stamp(event.at);
   if(previous===null){if(event.phase!=='INSPECTING')fail();}
   else if(terminal.includes(previous.phase)||![...(next[previous.phase]??[]),...failures].includes(event.phase)||at<previousStamp)fail();
   previous=event;previousStamp=at;
  }
  if(record.phase!==previous.phase)fail();keys(record.notes,[...lists,...texts]);
  for(const key of texts)text(record.notes[key]);
  for(const key of lists){if(!Array.isArray(record.notes[key])||record.notes[key].length>64)fail();for(const item of record.notes[key])text(item);}
  const test=record.project_test_status,n=record.notes;
  if(!['UNKNOWN','PASSED','FAILED','SKIPPED'].includes(test)||(['PASSED','FAILED'].includes(test)&&(!n.tests_run.length||!n.test_results.length))||
     (test==='FAILED'&&!n.known_failures.length)||(test==='SKIPPED'&&!n.limitations.length))fail();
  const e=record.evidence;keys(e,[...digests,...commits,'unsafe_target','push_attempted','publication_error']);
  for(const key of [...digests,...commits]){
   const value=e[key],pattern=digests.includes(key)?/^[0-9a-f]{64}$/:/^(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
   if(value!==null&&(typeof value!=='string'||pattern.exec(value)?.[0]!==value))fail();
  }
  if(typeof e.unsafe_target!=='boolean'||typeof e.push_attempted!=='boolean'||(e.publication_error!==null&&!publicationErrors.includes(e.publication_error)))fail();
  if((e.handoff_digest||e.local_commit)&&!e.inspection_digest||e.resume_digest&&!e.handoff_digest)fail();
  if(new Set(commits.map(k=>e[k]).filter(x=>x!==null)).size>1&&e.publication_error!=='VERIFICATION_MISMATCH')fail();
  if((e.remote_commit||e.tracking_commit)&&!e.local_commit)fail();
  if(record.requested_level!=='REMOTE_VERIFIED'&&(e.push_attempted||e.publication_error||e.remote_commit||e.tracking_commit))fail();
  if(e.publication_error&&e.local_commit&&e.remote_commit===e.tracking_commit&&e.remote_commit===e.local_commit)fail();
  if(canonical(Object.fromEntries(derived.map(k=>[k,record[k]])))!==canonical(conclusions(record)))fail();
  const serialized=canonical(record);if(Buffer.byteLength(serialized,'ascii')>MAX_BYTES)fail();
  return JSON.parse(serialized);
 }catch{fail();}
}
export function encodeRecord(record){return Buffer.from(canonical(validateRecord(record))+'\n','ascii');}
export function decodeRecord(raw){
 try {
  if(!(raw instanceof Uint8Array)||raw.byteLength<1||raw.byteLength>MAX_BYTES+1)fail();
  const bytes=Buffer.from(raw);if(bytes.some(x=>x>127))fail();
  const record=validateRecord(JSON.parse(bytes.toString('ascii')));
  if(!encodeRecord(record).equals(bytes))fail();return record;
 }catch{fail();}
}
export function historicalRecord(raw){
 const bytes=encodeRecord(decodeRecord(raw));
 return Object.freeze({record:()=>decodeRecord(bytes),bytes:()=>Buffer.from(bytes),authority:'NONE',
   freshness:'HISTORICAL_UNVERIFIED',current_safe_to_resume:'UNKNOWN',mutation_authorized:false,receipts_authenticated:false});
}
