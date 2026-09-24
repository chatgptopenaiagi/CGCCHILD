// Stable facade; underlying experimental wire profiles retain their own versions.
import {decodeState, encodeState} from './state.mjs';
import {decodeContinuity, encodeContinuity} from './continuity.mjs';
import {importCapsule, exportCapsule} from './capsule.mjs';
import {importCapsule as importContinuityCapsule, exportCapsule as exportContinuityCapsule} from './continuity_capsule.mjs';
export {LIVE_EVENT_VERSION, LIVE_REPORT_TYPES, buildLiveReport, LiveClient} from './live.mjs';
export const API_VERSION = 'cgcchild-sdk-1';
export function negotiate(version) {
  if (version !== API_VERSION) throw new Error('UNSUPPORTED_SDK_VERSION');
  return {api_version:API_VERSION, package_version:'0.4.0', profiles:['QUIESCENCE_MODEL_ONLY','V3_CONTINUITY_HISTORICAL'],mutation_authorized:false};
}
export function decode(raw) {
  if (!Buffer.isBuffer(raw)) throw new Error('INVALID_SNAPSHOT');
  try { return decodeState(raw); } catch {}
  try { return decodeContinuity(raw); } catch { throw new Error('INVALID_SNAPSHOT'); }
}
export function encode(value) {
  try { return value?.version === 'cgcchild-state-0.1-experimental' ? encodeState(value) : encodeContinuity(value); }
  catch { throw new Error('INVALID_SNAPSHOT'); }
}
export function capsuleExport(value) {
  const v=decode(encode(value));
  return v.version === 'cgcchild-state-0.1-experimental' ? exportCapsule(v) : exportContinuityCapsule(v);
}
export function capsuleImport(raw) {
  try { return importCapsule(raw).snapshot(); } catch {}
  try { return importContinuityCapsule(raw).snapshot(); } catch { throw new Error('INVALID_CAPSULE'); }
}
