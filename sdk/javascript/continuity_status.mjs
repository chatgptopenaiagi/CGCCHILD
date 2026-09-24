/** Compact historical capsule status, no source path/notes or execution. */
import {createHash} from 'node:crypto';
import {importCapsule} from './continuity_capsule.mjs';
import {summaryContinuity,encodeContinuity} from './continuity.mjs';
import {encodeIntegerJson} from './integer_json.mjs';
export class StatusError extends Error {constructor(){super('CONTINUITY_STATUS_REFUSED');}}
const hash=x=>createHash('sha256').update(x).digest('hex');
export function capsuleStatus(input,mode){try{
 if(!['json','text'].includes(mode))throw Error();
 const view=importCapsule(input),snapshot=view.snapshot(),s=summaryContinuity(snapshot);
 const result={version:'cgcchild-continuity-status-0.1-experimental',...s,capsule_sha256:hash(input),snapshot_sha256:hash(encodeContinuity(snapshot)),integrity:view.integrity,authority:'NONE',source_authenticated:false};
 let bytes;
 if(mode==='json')bytes=encodeIntegerJson(result,true);
 else bytes=Buffer.from('CGCCHILD historical continuity capsule\n'+
 'Project identifier: '+s.project_id+'\n'+
 'Saved generation: '+s.generation+'\n'+
 'Saved latest attempt: '+s.latest_attempt+'\n'+
 'Saved error: '+(s.latest_error??'None')+'\n'+
 'Saved known-good generation: '+(s.last_known_good_generation??'None')+'\n'+
 'Saved previous generation: '+(s.previous_known_good_generation??'None')+'\n'+
 'Integrity: CONSISTENT_UNSIGNED_BYTES; source authenticated: false\n'+
 'Freshness: HISTORICAL_UNVERIFIED\n'+
 'Current safe to resume: UNKNOWN; mutation authorized: false; authority: NONE\n'+
 'Current filesystem, repository and remote: NOT CHECKED\n','ascii');
 if(bytes.length>4096)throw Error();return bytes;
}catch{throw new StatusError();}}
