/** Bounded canonical integer JSON for inert records; not a schema or authority validator. */
export const MAX_BYTES=2101248,MAX_DEPTH=32,MAX_NODES=262144,MAX_INTEGER_DIGITS=4300;
export class IntegerJsonError extends Error {constructor(){super('INVALID_CANONICAL_INTEGER_JSON');this.name='IntegerJsonError';}}
const fail=()=>{throw new IntegerJsonError();};
const ceiling=10n**BigInt(MAX_INTEGER_DIGITS),safe=BigInt(Number.MAX_SAFE_INTEGER);
const ascii=x=>JSON.stringify(x).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
function compare(a,b){
 const left=[...a],right=[...b];
 for(let i=0;i<Math.min(left.length,right.length);i++){const x=left[i].codePointAt(0),y=right[i].codePointAt(0);if(x!==y)return x-y;}
 return left.length-right.length;
}
export function encodeIntegerJson(value,compact=true){
 try{
  if(typeof compact!=='boolean')fail();
  let size=0,nodes=0;const parts=[],active=new Set(),comma=compact?',':', ',colon=compact?':':': ';
  function emit(text){size+=text.length;if(size>MAX_BYTES)fail();parts.push(text);}
  function visit(v,depth){
   if(depth>MAX_DEPTH||++nodes>MAX_NODES)fail();
   if(v===null){emit('null');return;}
   if(typeof v==='boolean'){emit(v?'true':'false');return;}
   if(typeof v==='string'){if(v.length>MAX_BYTES)fail();emit(ascii(v));return;}
   if(typeof v==='number'){if(!Number.isSafeInteger(v)||Object.is(v,-0))fail();emit(String(v));return;}
   if(typeof v==='bigint'){if(v>=ceiling||v<=-ceiling)fail();emit(v.toString());return;}
   if(typeof v!=='object'||active.has(v))fail();active.add(v);
   if(Array.isArray(v)){
    if(v.length>MAX_NODES||Object.keys(v).length!==v.length||Reflect.ownKeys(v).length!==v.length+1)fail();
    emit('[');for(let i=0;i<v.length;i++){const d=Object.getOwnPropertyDescriptor(v,String(i));if(!d||!('value' in d))fail();if(i)emit(comma);visit(d.value,depth+1);}emit(']');
   }else{
    if(![Object.prototype,null].includes(Object.getPrototypeOf(v)))fail();
    const keys=Reflect.ownKeys(v);if(keys.length>MAX_NODES||keys.some(k=>typeof k!=='string'))fail();keys.sort(compare);
    emit('{');for(let i=0;i<keys.length;i++){
     const key=keys[i],d=Object.getOwnPropertyDescriptor(v,key);if(!d.enumerable||!('value' in d)||key.length>MAX_BYTES)fail();
     if(i)emit(comma);emit(ascii(key));emit(colon);visit(d.value,depth+1);
    }emit('}');
   }
   active.delete(v);
  }
  visit(value,0);emit('\n');return Buffer.from(parts.join(''),'ascii');
 }catch{fail();}
}
export function decodeIntegerJson(raw,compact=true){
 try{
  if(typeof compact!=='boolean'||!(raw instanceof Uint8Array)||raw.byteLength<1||raw.byteLength>MAX_BYTES)fail();
  const bytes=Buffer.from(raw);if(bytes.some(x=>x>127))fail();const text=bytes.toString('ascii');let at=0,nodes=0;
  const skip=()=>{while(at<text.length&&' \r\n\t'.includes(text[at]))at++;};
  function string(){
   if(text[at]!=='"')fail();const start=at++;
   while(at<text.length){const c=text[at++];if(c==='"')return JSON.parse(text.slice(start,at));if(c==='\\')at++;}
   fail();
  }
  function value(depth){
   if(depth>MAX_DEPTH||++nodes>MAX_NODES)fail();skip();const c=text[at];
   if(c==='"')return string();
   if(c==='['){
    at++;skip();const out=[];if(text[at]===']'){at++;return out;}
    while(true){out.push(value(depth+1));skip();if(text[at]===']'){at++;return out;}if(text[at++]!==',')fail();}
   }
   if(c==='{'){
    at++;skip();const out=Object.create(null);if(text[at]==='}'){at++;return out;}
    while(true){skip();const key=string();if(Object.hasOwn(out,key))fail();skip();if(text[at++]!==':')fail();out[key]=value(depth+1);skip();if(text[at]==='}'){at++;return out;}if(text[at++]!==',')fail();}
   }
   for(const [word,result] of [['null',null],['true',true],['false',false]])if(text.startsWith(word,at)){at+=word.length;return result;}
   const start=at;if(c==='-')at++;
   if(text[at]==='0')at++;
   else{if(!(text[at]>='1'&&text[at]<='9'))fail();while(text[at]>='0'&&text[at]<='9')at++;}
   const token=text.slice(start,at);if(token.length-(token[0]==='-'?1:0)>MAX_INTEGER_DIGITS)fail();
   const number=BigInt(token);return number>=-safe&&number<=safe?Number(number):number;
  }
  const result=value(0);skip();if(at!==text.length||!encodeIntegerJson(result,compact).equals(bytes))fail();return result;
 }catch{fail();}
}
