/** CGCCHILD inert model-capsule0.1 only. No extraction, paths or execution. */
import {createHash} from 'node:crypto';
import {validateState,encodeState,decodeState,humanStatus,MAX_BYTES as STATE_MAX} from './state.mjs';

export const CAPSULE_VERSION='cgcchild-capsule-0.1-experimental';
export const MAX_CAPSULE_BYTES=65536;
const names=['manifest.json','state.json','HUMAN-STATUS.txt'];
export class CapsuleError extends Error {
  constructor(){super('INVALID_CAPSULE');this.name='CapsuleError';}
}
const fail=()=>{throw new CapsuleError();};
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function crc32(bytes) {
  let crc=0xffffffff;
  for(const byte of bytes) {
    crc^=byte;
    for(let bit=0;bit<8;bit++)crc=(crc>>>1)^((crc&1)?0xedb88320:0);
  }
  return (crc^0xffffffff)>>>0;
}
function members(value) {
  const snapshot=validateState(value);
  const state=encodeState(snapshot),human=Buffer.from(humanStatus(snapshot),'ascii');
  const manifest=Buffer.from(JSON.stringify({
    members:{'HUMAN-STATUS.txt':hash(human),'state.json':hash(state)},
    signature:'UNSIGNED',version:CAPSULE_VERSION
  })+'\n','ascii');
  return [manifest,state,human];
}
function archive(values) {
  const local=[],central=[];let offset=0;
  for(let index=0;index<3;index++) {
    const data=values[index],name=Buffer.from(names[index],'ascii');
    if(!data.length||data.length>STATE_MAX)fail();
    const crc=crc32(data),h=Buffer.alloc(30);
    h.writeUInt32LE(0x04034b50,0);h.writeUInt16LE(20,4);h.writeUInt16LE(33,12);
    h.writeUInt32LE(crc,14);h.writeUInt32LE(data.length,18);h.writeUInt32LE(data.length,22);
    h.writeUInt16LE(name.length,26);
    local.push(h,name,data);
    const c=Buffer.alloc(46);
    c.writeUInt32LE(0x02014b50,0);c.writeUInt16LE(0x0314,4);c.writeUInt16LE(20,6);
    c.writeUInt16LE(33,14);c.writeUInt32LE(crc,16);
    c.writeUInt32LE(data.length,20);c.writeUInt32LE(data.length,24);
    c.writeUInt16LE(name.length,28);c.writeUInt32LE(0x81800000,38);c.writeUInt32LE(offset,42);
    central.push(c,name);offset+=h.length+name.length+data.length;
  }
  const directory=Buffer.concat(central),end=Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50,0);end.writeUInt16LE(3,8);end.writeUInt16LE(3,10);
  end.writeUInt32LE(directory.length,12);end.writeUInt32LE(offset,16);
  const result=Buffer.concat([...local,directory,end]);
  if(result.length>MAX_CAPSULE_BYTES)fail();
  return result;
}
export function exportCapsule(value) {
  try{return archive(members(value));}catch{fail();}
}
export function importCapsule(input) {
  try {
    if(!(input instanceof Uint8Array)||input.byteLength<1||input.byteLength>MAX_CAPSULE_BYTES)fail();
    const raw=Buffer.from(input),values=[];let offset=0;
    for(const expected of names) {
      if(raw.length-offset<30)fail();
      const h=raw.subarray(offset,offset+30),name=Buffer.from(expected,'ascii');
      if(h.readUInt32LE(0)!==0x04034b50||h.readUInt16LE(4)!==20||
         h.readUInt16LE(6)!==0||h.readUInt16LE(8)!==0||h.readUInt16LE(10)!==0||
         h.readUInt16LE(12)!==33||h.readUInt16LE(26)!==name.length||h.readUInt16LE(28)!==0)fail();
      const size=h.readUInt32LE(22);
      if(size<1||size>STATE_MAX||h.readUInt32LE(18)!==size)fail();
      offset+=30;
      if(name.length>raw.length-offset||!raw.subarray(offset,offset+name.length).equals(name))fail();
      offset+=name.length;
      if(size>raw.length-offset)fail();
      const data=raw.subarray(offset,offset+size);
      if(crc32(data)!==h.readUInt32LE(14))fail();
      values.push(data);offset+=size;
    }
    const state=decodeState(values[1]),expected=members(state);
    if(values.some((data,i)=>!data.equals(expected[i])))fail();
    // Exact reconstruction validates all central records, offsets and EOCD too.
    // No tolerant ZIP parser, extraction or filename resolution is involved.
    if(!archive(expected).equals(raw))fail();
    const saved=Buffer.from(values[1]);
    return Object.freeze({
      integrity:'CONSISTENT_UNSIGNED_BYTES',freshness:'HISTORICAL_UNVERIFIED',authority:'NONE',
      snapshot:()=>decodeState(saved)
    });
  }catch{fail();}
}
