/** Pure historical receipt validation. No filesystem observation or authority. */
import {createHash} from 'node:crypto';
import {encodeIntegerJson,decodeIntegerJson} from './integer_json.mjs';
export const VERSION='cgc-inspection-v3.0-provisional',MAX_BYTES=263168;
export class InspectionError extends Error {constructor(){super('INVALID_INSPECTION');}}
const fail=()=>{throw new InspectionError();};
const codes='INVALID_TARGET UNSAFE_PATH UNSAFE_FILE NOT_REPOSITORY_ROOT UNSUPPORTED_GITFILE UNSUPPORTED_LAYOUT UNSUPPORTED_CONFIG RESOURCE_LIMIT TIMEOUT GIT_FAILED MALFORMED_GIT TARGET_CHANGED FILESYSTEM_ERROR SENSITIVE_METADATA CANCELLED INVALID_TIME'.split(' ');
const operations='MERGE_HEAD CHERRY_PICK_HEAD REVERT_HEAD rebase-merge rebase-apply sequencer BISECT_LOG'.split(' ');
const documents='AGENTS.md README.md PROGRESS.md HANDOFF.md docs/PROGRESS.md docs/HANDOFF.md docs/V3_PROGRESS.md'.split(' ');
const outer='schema_version status error_code snapshot inspection_digest safe_to_resume automatic_mutation_authorized'.split(' ');
const fields='head branch detached upstream ahead behind changes project_request root repository_identity observed_at evidence_basis consistency remotes remote_state operations linked_worktrees_present submodules submodule_worktrees document_candidates instructions test_command nested_repositories hidden_index_paths'.split(' ');
function keys(x,k){if(!x||typeof x!=='object'||Array.isArray(x)||Object.keys(x).sort().join('\0')!==[...k].sort().join('\0'))fail();}
function text(x){if(typeof x!=='string'||![...x].length||[...x].length>4096||x.includes('\0')||/(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|:\/\/[^/\x09-\x0d\x1c-\x20\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+@)/u.test(x))fail();}
function path(x){text(x);if(x.startsWith('/')||x.replace(/\/+$/,'').split('/').some(p=>['','.','..','.git'].includes(p)))fail();}
function integer(x){return typeof x==='bigint'||typeof x==='number'&&Number.isSafeInteger(x);}
function stamp(x){if(typeof x!=='string')fail();const m=/^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2})(?:\.([0-9]{6}))?Z$/.exec(x);if(!m||m[0]!==x||x.startsWith('0000')||m[2]==='000000')fail();const d=new Date(m[1]+'Z');if(!Number.isFinite(d.getTime())||d.toISOString().slice(0,19)!==m[1])fail();}
function check(r){
 keys(r,outer);if(r.schema_version!==VERSION||r.safe_to_resume!=='UNKNOWN'||r.automatic_mutation_authorized!==false)fail();
 if(r.status==='REFUSED'){if(!codes.includes(r.error_code)||r.snapshot!==null||r.inspection_digest!==null)fail();return r;}
 if(r.status!=='OBSERVED'||r.error_code!==null)fail();const s=r.snapshot;keys(s,fields);
 for(const [k,v] of Object.entries({evidence_basis:'LOCAL_OBSERVATION',consistency:'REPEATED_OBSERVATION_NOT_ATOMIC',remote_state:'NOT_QUERIED',submodule_worktrees:'NOT_INSPECTED',instructions:'NOT_READ',test_command:'UNKNOWN'}))if(s[k]!==v)fail();
 stamp(s.observed_at);text(s.root);if(s.root!==s.project_request||!s.root.startsWith('/')||s.root==='/'||s.root.split('/').includes('..'))fail();
 keys(s.repository_identity,['device','inode','git_device','git_inode']);for(const v of Object.values(s.repository_identity))if(!integer(v)||v<0)fail();
 for(const k of ['detached','linked_worktrees_present'])if(typeof s[k]!=='boolean')fail();if(s.detached!==(s.branch===null))fail();
 if(s.head!==null&&(typeof s.head!=='string'||!/^([0-9a-f]{40}|[0-9a-f]{64})$/.test(s.head)||![40,64].includes(s.head.length)))fail();
 for(const k of ['branch','upstream'])if(s[k]!==null)text(s[k]);
 for(const k of ['ahead','behind'])if(s[k]!==null&&(!integer(s[k])||s[k]<0||s[k]>=1000000000000))fail();
 for(const k of ['remotes','operations','submodules','document_candidates','nested_repositories','hidden_index_paths']){
  const a=s[k];if(!Array.isArray(a)||a.length>10000||new Set(a).size!==a.length)fail();
  for(const v of a){text(v);if(['submodules','nested_repositories','hidden_index_paths'].includes(k))path(v);if(k==='operations'&&!operations.includes(v)||k==='document_candidates'&&!documents.includes(v))fail();}
 }
 if(!Array.isArray(s.changes)||s.changes.length>10000)fail();for(const c of s.changes){keys(c,['path','index','worktree','conflict','original_path']);path(c.path);if(c.original_path!==null)path(c.original_path);for(const k of ['index','worktree'])if(typeof c[k]!=='string'||c[k].length!==1||!'.MADRCUT?'.includes(c[k]))fail();if(typeof c.conflict!=='boolean')fail();}
 const bytes=encodeIntegerJson(s,false).subarray(0,-1);if(bytes.length>262144||createHash('sha256').update(bytes).digest('hex')!==r.inspection_digest)fail();return r;
}
export function validateInspection(value){try{return check(decodeIntegerJson(encodeIntegerJson(value,false),false));}catch{fail();}}
export function encodeInspection(value){const bytes=encodeIntegerJson(validateInspection(value),false);if(bytes.length>MAX_BYTES)fail();return bytes;}
export function decodeInspection(bytes){try{if(bytes.length>MAX_BYTES)fail();return check(decodeIntegerJson(bytes,false));}catch{fail();}}
export function historicalInspection(value){const bytes=encodeInspection(value);return Object.freeze({current_safe_to_resume:'UNKNOWN',authority:'NONE',mutation_authorized:false,receipt_authenticated:false,record:()=>decodeInspection(bytes),bytes:()=>Buffer.from(bytes)});}
