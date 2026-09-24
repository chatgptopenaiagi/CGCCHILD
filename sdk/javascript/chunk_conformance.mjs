import {createAssembler} from './capsule_chunks.mjs';
let parts=[],size=0;
for await(const piece of process.stdin){size+=piece.length;if(size>12*1024*1024)process.exit(2);parts.push(piece);}
try {
 const cases=JSON.parse(Buffer.concat(parts).toString('utf8'));
 if(!Array.isArray(cases)||cases.length>128)process.exit(2);
 const results=cases.map(item=>{
  try {
   const receiver=createAssembler(item.expected);
   if(!Array.isArray(item.frames)||item.frames.length>66)throw Error();
   for(const raw of item.frames)receiver.accept(Buffer.from(raw,'base64'));
   const view=receiver.finish();return {accepted:true,raw:view.bytes().toString('base64'),
     authority:view.authority,capsule_validation:view.capsule_validation,source_authenticated:view.source_authenticated};
  } catch {return {accepted:false};}
 });
 process.stdout.write(JSON.stringify(results)+'\n');
} catch {process.exit(2);}
