import assert from 'node:assert/strict';
import {encodeIntegerJson as encode,decodeIntegerJson as decode,IntegerJsonError,MAX_DEPTH,MAX_NODES,MAX_BYTES} from './integer_json.mjs';
let cases=0;
for(const compact of [true,false]){
 const value={inode:9007199254740993n,negative:-18446744073709551615n,small:1};
 const raw=encode(value,compact),restored=decode(raw,compact);
 assert.equal(restored.inode,value.inode);assert.equal(typeof restored.inode,'bigint');assert.equal(typeof restored.small,'number');
 assert.deepEqual(encode(restored,compact),raw);cases++;
}
for(const bad of [NaN,Infinity,1.5,9007199254740992,-0,undefined,()=>0,new Date(),10n**4300n]){
 assert.throws(()=>encode(bad),IntegerJsonError);cases++;
}
let called=false;const getter={get value(){called=true;return 1;}};assert.throws(()=>encode(getter),IntegerJsonError);assert.equal(called,false);cases++;
const cycle={};cycle.self=cycle;assert.throws(()=>encode(cycle),IntegerJsonError);cases++;
const sparse=Array(2);assert.throws(()=>encode(sparse),IntegerJsonError);cases++;
let nested=0;for(let i=0;i<MAX_DEPTH;i++)nested=[nested];assert.deepEqual(encode(decode(encode(nested))),encode(nested));cases++;
assert.throws(()=>encode([nested]),IntegerJsonError);cases++;
assert.throws(()=>decode(Buffer.from('['.repeat(MAX_DEPTH+1)+'0'+']'.repeat(MAX_DEPTH+1)+'\n')),IntegerJsonError);cases++;
assert.throws(()=>encode(Array(MAX_NODES).fill(0)),IntegerJsonError);cases++;
assert.throws(()=>decode(Buffer.alloc(MAX_BYTES+1,32)),IntegerJsonError);cases++;
const raw=Buffer.from('{"__proto__": {"polluted": true}}\n');const value=decode(raw,false);
assert.equal(Object.getPrototypeOf(value),null);assert.equal({}.polluted,undefined);assert.equal(value.__proto__.polluted,true);cases++;
process.stdout.write(JSON.stringify({status:'PASS',cases})+'\n');
