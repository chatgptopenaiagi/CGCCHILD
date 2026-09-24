import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {decodeState,encodeState,stateDigest,humanStatus} from './state.mjs';

const vectors=JSON.parse(readFileSync(new URL('../../docs/lab/child_state_vectors.json',import.meta.url),'utf8'));
const raw=Buffer.from(vectors.state_ascii,'ascii');
const state=decodeState(raw);
assert.deepEqual(encodeState(state),raw);
assert.equal(stateDigest(state),vectors.state_sha256);
assert.match(humanStatus(state),/P3: UNKNOWN; safe to resume: UNKNOWN/);
let cases=3;
function reject(bytes) {assert.throws(()=>decodeState(bytes)); cases++;}
for (let i=0;i<raw.length;i++) reject(raw.subarray(0,i));
for (const key of ['version','project','domain_empty']) {
  reject(Buffer.from(vectors.state_ascii.replace('"'+key+'":','"'+key+'":"forged","'+key+'":')));
}
for (const [field,value] of [['mutation_authorized',true],['production_p3','YES'],['safe_to_resume','YES'],
  ['version','future'],['captured_at','2026-02-30T12:00:00Z'],['captured_at','0000-01-01T00:00:00Z']]) {
  const v=structuredClone(state);v[field]=value;assert.throws(()=>encodeState(v));cases++;
}
for (const value of ['01','-1','1.0','9223372036854775808',true,10,'1\n']) {
  const v=structuredClone(state);v.model.observed_ns=value;assert.throws(()=>encodeState(v));cases++;
}
for (const value of ['id\n','id\r','id\r\n','é','', 'a'.repeat(129)]) {
  const v=structuredClone(state);v.source_instance=value;assert.throws(()=>encodeState(v));cases++;
}
for (const status of ['YES','NO','UNKNOWN']) {
  const v=structuredClone(state);v.model.claims.domain_empty=status;
  assert.equal(decodeState(encodeState(v)).model.claims.domain_empty,status);cases++;
}
const max=structuredClone(state);max.model.observed_ns='9223372036854775806';max.model.expires_ns='9223372036854775807';
assert.equal(decodeState(encodeState(max)).model.expires_ns,'9223372036854775807');cases++;
console.log(JSON.stringify({status:'PASS',cases,pinned_digest:vectors.state_sha256,node:process.version}));
