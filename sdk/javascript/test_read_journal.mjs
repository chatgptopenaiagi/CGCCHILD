import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {decodeJournal,encodeJournal,JournalError} from './read_journal.mjs';
const vector=JSON.parse(readFileSync(new URL('../../docs/lab/child_read_journal_vectors.json',import.meta.url),'utf8'));
const raw=Buffer.from(vector.journal_ascii,'ascii');let cases=0;
const check=(a,b)=>{assert.deepEqual(a,b);cases++;};
const view=decodeJournal(raw,vector.expected);
check(createHash('sha256').update(raw).digest('hex'),vector.journal_sha256);
check(encodeJournal(view.events(),vector.expected.expected_snapshot_digest),raw);
check(view.authority,'NONE');check(view.freshness,'HISTORICAL_UNVERIFIED');
check(view.integrity,'CONSISTENT_UNSIGNED_BYTES');check(view.completeness,'EXPECTED_PREFIX_ONLY');
check(Object.isFrozen(view),true);
const events=view.events();events[0].kind='tamper';check(view.events()[0].kind,'LOCAL_READ_HANDLE_ISSUED');
const output=view.bytes();output.fill(0);check(view.bytes(),raw);
const copy=Buffer.from(raw);const other=decodeJournal(copy,vector.expected);copy.fill(0);check(other.bytes(),raw);
assert.throws(()=>{view.authority='YES';},TypeError);cases++;
for(const bytes of [Buffer.from('{}'),Buffer.from(raw.toString('ascii').replace('NONE','YES')),raw.subarray(0,raw.length-1)]) {
  assert.throws(()=>decodeJournal(bytes,vector.expected),JournalError);cases++;
}
console.log(JSON.stringify({status:'PASS',cases}));
