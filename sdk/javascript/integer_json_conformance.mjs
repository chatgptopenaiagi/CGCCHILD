/** Bounded offline integer JSON corpus, not a product parser endpoint. */
import {decodeIntegerJson,encodeIntegerJson} from './integer_json.mjs';
let chunks=[],size=0;for await(const x of process.stdin){size+=x.length;if(size>8*1024*1024)process.exit(2);chunks.push(x);}
try{
 const rows=JSON.parse(Buffer.concat(chunks).toString('ascii'));if(!Array.isArray(rows)||rows.length>1024)process.exit(2);
 const results=rows.map(row=>{try{
  if(typeof row.hex!=='string'||row.hex.length%2||row.hex.length>2*2101249||!/^[0-9a-f]*$/.test(row.hex))throw Error();
  const bytes=Buffer.from(row.hex,'hex'),value=decodeIntegerJson(bytes,row.compact);
  return {accepted:true,hex:encodeIntegerJson(value,row.compact).toString('hex')};
 }catch{return {accepted:false};}});process.stdout.write(JSON.stringify(results)+'\n');
}catch{process.exit(2);}
