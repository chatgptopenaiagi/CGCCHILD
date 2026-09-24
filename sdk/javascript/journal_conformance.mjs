/** Bounded offline parity harness, not a product transport or grant endpoint. */
import {decodeJournal,encodeJournal,MAX_BYTES} from './read_journal.mjs';
import {readSync} from 'node:fs';
const storage=Buffer.alloc(8*1024*1024+1);let size=0;
while(size<storage.length){const n=readSync(0,storage,size,storage.length-size,null);if(!n)break;size+=n;}
if(size>8*1024*1024)throw new Error('CORPUS_LIMIT');
const rows=JSON.parse(storage.subarray(0,size).toString('ascii'));
if(!Array.isArray(rows)||rows.length>2000)throw new Error('CORPUS_LIMIT');
const result=rows.map(row=>{
  try {
    if(row===null||typeof row!=='object'||Object.keys(row).sort().join(',')!=='expected,hex'||
       typeof row.hex!=='string'||row.hex.length>2*(MAX_BYTES+1)||row.hex.length%2||
       /^[0-9a-f]*$/.exec(row.hex)?.[0]!==row.hex)throw new Error();
    const view=decodeJournal(Buffer.from(row.hex,'hex'),row.expected);
    const bytes=encodeJournal(view.events(),row.expected.expected_snapshot_digest);
    return {accepted:true,hex:bytes.toString('hex'),authority:view.authority,
      freshness:view.freshness,integrity:view.integrity,completeness:view.completeness};
  } catch {return {accepted:false};}
});
process.stdout.write(JSON.stringify(result));
