/** Inert bounded journal codec. No grants, authentication or replay. */
import {createHash} from 'node:crypto';
export const VERSION='cgcchild-read-journal-0.1-experimental';
export const MAX_BYTES=32768,MAX_EVENTS=64;
const zero='0'.repeat(64);
const kinds=['LOCAL_READ_HANDLE_ISSUED','READ_DENIED','CORE_REFUSED','READ_COMPLETE',
  'LOCAL_READ_HANDLE_REVOKED','SNAPSHOT_INVALIDATED'];
const fields=['version','sequence','kind','observed_ns','snapshot_digest','previous','digest'];
const envelope=['version','snapshot_digest','events','completeness','authority','freshness','clock'];
export class JournalError extends Error {constructor(){super('INVALID_READ_JOURNAL');this.name='JournalError';}}
const fail=()=>{throw new JournalError();};
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function keys(value,expected) {
  if(value===null||typeof value!=='object'||Array.isArray(value)||
     Reflect.ownKeys(value).some(k=>typeof k!=='string')||
     Object.keys(value).sort().join('\0')!==[...expected].sort().join('\0'))fail();
}
function digest(value) {
  if(typeof value!=='string'||/^[0-9a-f]{64}$/.exec(value)?.[0]!==value)fail();
}
function canonical(value) {
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  if(value!==null&&typeof value==='object')return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  return JSON.stringify(value);
}
function validate(value) {
  keys(value,envelope);
  if(value.version!==VERSION||value.completeness!=='EXPECTED_PREFIX_ONLY'||value.authority!=='NONE'||
     value.freshness!=='HISTORICAL_UNVERIFIED'||value.clock!=='SOURCE_MONOTONIC_NOT_PORTABLE')fail();
  digest(value.snapshot_digest);
  if(!Array.isArray(value.events)||value.events.length>MAX_EVENTS)fail();
  let previous=zero,clock=-1n,ended=false;
  for(let index=0;index<value.events.length;index++) {
    const event=value.events[index];keys(event,fields);
    if(ended||event.version!=='cgcchild-read-events-0.1'||!Number.isInteger(event.sequence)||event.sequence!==index+1||!kinds.includes(event.kind))fail();
    if(typeof event.observed_ns!=='string'||/^(0|[1-9][0-9]{0,18})$/.exec(event.observed_ns)?.[0]!==event.observed_ns)fail();
    const now=BigInt(event.observed_ns);
    if(now<clock||now>=9223372036854775808n)fail();
    clock=now;
    if(event.snapshot_digest!==value.snapshot_digest||event.previous!==previous)fail();
    digest(event.digest);
    const body={};for(const field of fields)if(field!=='digest')body[field]=event[field];
    if(hash(Buffer.from(canonical(body),'ascii'))!==event.digest)fail();
    previous=event.digest;ended=event.kind==='SNAPSHOT_INVALIDATED';
  }
  return value;
}
export function encodeJournal(events,snapshotDigest) {
  try {
    const value={version:VERSION,snapshot_digest:snapshotDigest,events,
      completeness:'EXPECTED_PREFIX_ONLY',authority:'NONE',freshness:'HISTORICAL_UNVERIFIED',clock:'SOURCE_MONOTONIC_NOT_PORTABLE'};
    const out=Buffer.from(canonical(validate(value))+'\n','ascii');
    if(out.length>MAX_BYTES)fail();
    return out;
  } catch {fail();}
}
export function decodeJournal(bytes,expected) {
  try {
    keys(expected,['expected_snapshot_digest','expected_tip','expected_count']);
    digest(expected.expected_snapshot_digest);digest(expected.expected_tip);
    if(!Number.isInteger(expected.expected_count)||expected.expected_count<0||expected.expected_count>MAX_EVENTS)fail();
    if(!(bytes instanceof Uint8Array)||bytes.byteLength<1||bytes.byteLength>MAX_BYTES)fail();
    const raw=Buffer.from(bytes);if(raw.some(x=>x>127))fail();
    const value=validate(JSON.parse(raw.toString('ascii')));
    if(!Buffer.from(canonical(value)+'\n','ascii').equals(raw))fail();
    const events=value.events,tip=events.length?events.at(-1).digest:zero;
    if(value.snapshot_digest!==expected.expected_snapshot_digest||events.length!==expected.expected_count||tip!==expected.expected_tip)fail();
    const text=raw.toString('ascii');
    return Object.freeze({authority:'NONE',freshness:'HISTORICAL_UNVERIFIED',integrity:'CONSISTENT_UNSIGNED_BYTES',
      completeness:'EXPECTED_PREFIX_ONLY',events:()=>JSON.parse(text).events,bytes:()=>Buffer.from(text,'ascii')});
  } catch {fail();}
}
