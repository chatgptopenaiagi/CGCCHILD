import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {decodeState,encodeState} from './state.mjs';
import {exportCapsule,importCapsule,CapsuleError} from './capsule.mjs';

const vector=JSON.parse(readFileSync(new URL('../../docs/lab/child_state_vectors.json',import.meta.url),'utf8'));
const state=decodeState(Buffer.from(vector.state_ascii,'ascii'));
const raw=exportCapsule(state);
assert.equal(raw.length,vector.capsule_bytes);
assert.equal(createHash('sha256').update(raw).digest('hex'),vector.capsule_sha256);
const view=importCapsule(raw);
assert.deepEqual(encodeState(view.snapshot()),Buffer.from(vector.state_ascii,'ascii'));
assert.deepEqual(exportCapsule(view.snapshot()),raw);
assert.equal(view.authority,'NONE');
assert.equal(view.freshness,'HISTORICAL_UNVERIFIED');
assert.equal(view.integrity,'CONSISTENT_UNSIGNED_BYTES');
let cases=7;
function reject(value){assert.throws(()=>importCapsule(value),CapsuleError);cases++;}
for(let i=0;i<raw.length;i++)reject(raw.subarray(0,i));
for(let i=0;i<raw.length;i++) {
  const changed=Buffer.from(raw);changed[i]^=128;reject(changed);
}
for(const value of [null,[],{},'archive',Buffer.alloc(65537),Buffer.concat([Buffer.from('x'),raw]),
                    Buffer.concat([raw,Buffer.from('x')]),Buffer.concat([raw,raw])])reject(value);
const detached=importCapsule(Buffer.from(raw)),snapshot=detached.snapshot();
snapshot.mutation_authorized=true;snapshot.model.claims.domain_empty='NO';
assert.equal(detached.snapshot().mutation_authorized,false);cases++;
assert.deepEqual(exportCapsule(detached.snapshot()),raw);cases++;
const input=Buffer.from(raw),copied=importCapsule(input);input.fill(0);
assert.deepEqual(exportCapsule(copied.snapshot()),raw);cases++;
assert.throws(()=>{copied.authority='ALL';},TypeError);cases++;
const invalid=structuredClone(state);invalid.mutation_authorized=true;
assert.throws(()=>exportCapsule(invalid),CapsuleError);cases++;
console.log(JSON.stringify({status:'PASS',cases,pinned_digest:vector.capsule_sha256,node:process.version}));
