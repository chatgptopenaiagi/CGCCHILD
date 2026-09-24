// Offline test harness only. No transport/authority capability.
import {readFileSync} from 'node:fs';
import {decodeState,encodeState,stateDigest,humanStatus} from './state.mjs';
const raw=readFileSync(0);
if(raw.length>2*1024*1024)throw new Error('TEST_CORPUS_LIMIT');
const cases=JSON.parse(raw.toString('ascii'));
if(!Array.isArray(cases)||cases.length>2048)throw new Error('TEST_CORPUS_LIMIT');
const results=cases.map(hex=>{
  try {
    if(typeof hex!=='string'||hex.length>32768)throw new Error('TEST_CORPUS_LIMIT');
    const state=decodeState(Buffer.from(hex,'hex'));
    return {accepted:true,hex:encodeState(state).toString('hex'),digest:stateDigest(state),human:humanStatus(state)};
  } catch {return {accepted:false};}
});
process.stdout.write(JSON.stringify(results));
