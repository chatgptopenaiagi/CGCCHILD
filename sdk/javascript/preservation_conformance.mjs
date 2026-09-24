/** Bounded offline record corpus, not an execution or preservation endpoint. */
import {decodeRecord,encodeRecord,historicalRecord} from './preservation.mjs';
let pieces=[],size=0;for await(const part of process.stdin){size+=part.length;if(size>8*1024*1024)process.exit(2);pieces.push(part);}
try{
 const rows=JSON.parse(Buffer.concat(pieces).toString('ascii'));if(!Array.isArray(rows)||rows.length>2000)process.exit(2);
 const result=rows.map(hex=>{try{
  if(typeof hex!=='string'||hex.length>2*262146||hex.length%2||!/^[0-9a-f]*$/.test(hex))throw Error();
  const raw=Buffer.from(hex,'hex'),record=decodeRecord(raw),view=historicalRecord(raw);
  const saved=view.bytes(),detached=view.record();detached.notes.mission='changed copy';raw.fill(0);view.bytes().fill(0);
  if(!Object.isFrozen(view)||!view.bytes().equals(saved)||view.record().notes.mission!==record.notes.mission)throw Error();
  return {accepted:true,hex:encodeRecord(record).toString('hex'),current_safe_to_resume:view.current_safe_to_resume,
    authority:view.authority,receipts_authenticated:view.receipts_authenticated};
 }catch{return {accepted:false};}});
 process.stdout.write(JSON.stringify(result)+'\n');
}catch{process.exit(2);}
