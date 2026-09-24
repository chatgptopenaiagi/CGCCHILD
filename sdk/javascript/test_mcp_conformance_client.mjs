import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createConformanceClient,ClientError,MAX_RESPONSE} from './mcp_conformance_client.mjs';
const v=JSON.parse(readFileSync(new URL('../../docs/lab/child_state_vectors.json',import.meta.url),'utf8'));
const raw=Buffer.from(v.state_ascii,'ascii');let cases=0;
function refused(client,action){assert.throws(action,ClientError);cases++;assert.throws(()=>client.next(),ClientError);cases++;}
let c=createConformanceClient(raw);refused(c,()=>c.accept(Buffer.from('{}\n')));
c=createConformanceClient(raw);c.next();refused(c,()=>c.next());
c=createConformanceClient(raw);refused(c,()=>c.finish());
c=createConformanceClient(raw);c.invalidate();refused(c,()=>c.next());
for(const bad of [Buffer.alloc(MAX_RESPONSE+1),Buffer.alloc(0),'not bytes']) {
  c=createConformanceClient(raw);c.next();refused(c,()=>c.accept(bad));
}
c=createConformanceClient(raw);assert.equal(Object.isFrozen(c),true);cases++;
const copy=c.snapshot();copy.fill(0);assert.deepEqual(c.snapshot(),raw);cases++;
const source=Buffer.from(raw);c=createConformanceClient(source);source.fill(0);assert.deepEqual(c.snapshot(),raw);cases++;
const request=c.next();assert.equal(Object.isFrozen(request),true);cases++;
assert.deepEqual(Object.keys(c).sort(),['accept','finish','invalidate','next','snapshot','snapshotDigest'].sort());cases++;
console.log(JSON.stringify({status:'PASS',cases}));
