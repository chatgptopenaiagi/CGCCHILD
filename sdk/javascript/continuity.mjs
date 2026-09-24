/** Lossless historical continuity profile; never current authority. */
import {createHash} from 'node:crypto';
import {encodeIntegerJson,decodeIntegerJson} from './integer_json.mjs';
import {validateHandoff,VERSION as SOURCE_VERSION} from './handoff.mjs';
export const VERSION='cgcchild-continuity-0.1-experimental',MAX_BYTES=2101248;
export class ContinuityError extends Error {constructor(){super('INVALID_CONTINUITY_PROJECTION');}}
const fail=()=>{throw new ContinuityError();};
const omissions=['SOURCE_FILES','GIT_OBJECTS','CURRENT_OBSERVATION','CURRENT_AUTHORITY'];
const fields=['version','source_schema','source_digest','source_state','portable_project_id','freshness','current_safe_to_resume','current_mutation_authorized','omissions'];
const digest=x=>createHash('sha256').update(encodeIntegerJson(x,true)).digest('hex');
export function validateContinuity(input){try{
 const v=decodeIntegerJson(encodeIntegerJson(input,true),true);
 if(!v||typeof v!=='object'||Array.isArray(v)||Object.keys(v).sort().join('\0')!==[...fields].sort().join('\0'))fail();
 if(v.version!==VERSION||v.source_schema!==SOURCE_VERSION||typeof v.portable_project_id!=='string'||!/^[A-Za-z0-9_.-]{1,128}$/.test(v.portable_project_id)||/[^A-Za-z0-9_.-]/.test(v.portable_project_id))fail();
 if(v.freshness!=='HISTORICAL_UNVERIFIED'||v.current_safe_to_resume!=='UNKNOWN'||v.current_mutation_authorized!==false||!Array.isArray(v.omissions)||JSON.stringify(v.omissions)!==JSON.stringify(omissions))fail();
 const source=validateHandoff(v.source_state);if(v.source_digest!==digest(source)||encodeIntegerJson(v,true).length>MAX_BYTES)fail();return v;
}catch{fail();}}
export function projectContinuity(source,portable_project_id){return validateContinuity({version:VERSION,source_schema:SOURCE_VERSION,source_digest:digest(validateHandoff(source)),source_state:source,portable_project_id,freshness:'HISTORICAL_UNVERIFIED',current_safe_to_resume:'UNKNOWN',current_mutation_authorized:false,omissions:[...omissions]});}
export function encodeContinuity(value){return encodeIntegerJson(validateContinuity(value),true);}
export function decodeContinuity(bytes){try{if(bytes.length>MAX_BYTES)fail();return validateContinuity(decodeIntegerJson(bytes,true));}catch{fail();}}
export function summaryContinuity(value){const v=validateContinuity(value),s=v.source_state;return {project_id:v.portable_project_id,source_digest:v.source_digest,generation:s.generation,latest_attempt:s.latest_attempt.status,latest_error:s.latest_attempt.error_code,last_known_good_generation:s.last_known_good?.generation??null,previous_known_good_generation:s.previous_known_good?.generation??null,source_outer_safe_to_resume:s.safe_to_resume,current_safe_to_resume:'UNKNOWN',current_mutation_authorized:false,freshness:'HISTORICAL_UNVERIFIED'};}
