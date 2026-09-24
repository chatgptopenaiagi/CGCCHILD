/** CGCCHILD experimental Node codec; inert validation, never execution authority. */
import {createHash} from 'node:crypto';

export const VERSION = 'cgcchild-state-0.1-experimental';
export const MAX_BYTES = 16384;
const obligations = ['launch_identity','controller_continuity','closed_admission',
  'domain_empty','filesystem_exclusive','epoch_current'];
const omissions = ['SOURCE_CONTENT','GIT_OBJECTS','V3_RECEIPTS','LIVE_AUTHORITY','FILESYSTEM_PROOF'];
const fields = ['version','profile','source_instance','snapshot_id','captured_at','clock',
  'model','production_p3','safe_to_resume','mutation_authorized','omissions'];
const modelFields = ['project','generation','observed_ns','expires_ns','claims','provenance'];
const fail = () => {throw new Error('INVALID_STATE');};
function keys(value, expected) {
  if (value === null || typeof value !== 'object' || Array.isArray(value) ||
      Reflect.ownKeys(value).some(k => typeof k !== 'string') ||
      Object.keys(value).sort().join('\0') !== [...expected].sort().join('\0')) fail();
}
function identifier(value) {
  if (typeof value !== 'string' || /^[A-Za-z0-9_.-]{1,128}$/.exec(value)?.[0] !== value) fail();
}
function clock(value) {
  if (typeof value !== 'string' || /^(0|[1-9][0-9]{0,18})$/.exec(value)?.[0] !== value) fail();
  const number = BigInt(value);
  if (number > 9223372036854775807n) fail();
  return number;
}
function canonical(value) {
  if (Array.isArray(value)) return '['+value.map(canonical).join(',')+']';
  if (value !== null && typeof value === 'object') {
    return '{'+Object.keys(value).sort().map(k => JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}';
  }
  return JSON.stringify(value);
}
export function validateState(value) {
  keys(value, fields);
  if (value.version !== VERSION || value.profile !== 'QUIESCENCE_MODEL_ONLY' ||
      value.clock !== 'SOURCE_MONOTONIC_NOT_PORTABLE' || value.production_p3 !== 'UNKNOWN' ||
      value.safe_to_resume !== 'UNKNOWN' || value.mutation_authorized !== false) fail();
  identifier(value.source_instance); identifier(value.snapshot_id);
  const stamp = value.captured_at;
  if (typeof stamp !== 'string' || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$/.test(stamp) ||
      stamp.startsWith('0000') || !Number.isFinite(Date.parse(stamp)) ||
      new Date(stamp).toISOString() !== stamp.replace('Z','.000Z')) fail();
  if (!Array.isArray(value.omissions) || JSON.stringify(value.omissions) !== JSON.stringify(omissions)) fail();
  const m = value.model;
  keys(m, modelFields); identifier(m.project); identifier(m.generation);
  const first = clock(m.observed_ns), last = clock(m.expires_ns);
  if (last < first || last-first > 60000000000n || !['SYNTHETIC','IMPORTED'].includes(m.provenance)) fail();
  keys(m.claims, obligations);
  if (obligations.some(k => !['YES','NO','UNKNOWN'].includes(m.claims[k]))) fail();
  const text = canonical(value)+'\n';
  if (Buffer.byteLength(text,'ascii') > MAX_BYTES) fail();
  return JSON.parse(text);
}
export function encodeState(value) {
  return Buffer.from(canonical(validateState(value))+'\n','ascii');
}
export function decodeState(bytes) {
  if (!(bytes instanceof Uint8Array) || bytes.byteLength < 1 || bytes.byteLength > MAX_BYTES) fail();
  const copy = Buffer.from(bytes);
  if (copy.some(x => x > 127)) fail();
  let value;
  try {value = JSON.parse(copy.toString('ascii'));} catch {fail();}
  value = validateState(value);
  // Canonical comparison also rejects duplicate keys that JSON.parse collapses.
  // No parsed value is returned before this comparison succeeds.
  if (!encodeState(value).equals(copy)) fail();
  return value;
}
export function stateDigest(value) {
  return createHash('sha256').update(encodeState(value)).digest('hex');
}
export function humanStatus(value) {
  const v=validateState(value);
  return 'CGCCHILD experimental historical model snapshot\n'+
    'Project identifier: '+v.model.project+'\n'+
    'Snapshot: '+v.snapshot_id+'; captured: '+v.captured_at+'\n'+
    'P3: UNKNOWN; safe to resume: UNKNOWN; mutation authorized: false\n'+
    'Current filesystem, repository and remote: NOT CHECKED\n'+
    'Saved: synthetic model claims only; not a source-code backup\n'+
    'Next: obtain current independent evidence and scoped authority\n';
}
