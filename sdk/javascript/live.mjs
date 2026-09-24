// Explicit Windows CLI facade. No daemon, shell, network or authority promotion.
import {spawnSync} from 'node:child_process';
export const LIVE_EVENT_VERSION = 'cgc-live-event-0.1';
export const LIVE_REPORT_TYPES = Object.freeze({
  session_started:'SESSION_STARTED', command_report:'COMMAND_REPORTED',
  file_edit_report:'FILE_EDIT_REPORTED', test_started:'TEST_STARTED', test_finished:'TEST_FINISHED',
  error_observed:'ERROR_OBSERVED', error_resolved:'ERROR_RESOLVED', error_reopened:'ERROR_REOPENED',
  decision_declared:'DECISION_DECLARED', commit_reported:'COMMIT_REPORTED',
  push_reported:'PUSH_REPORTED', next_action_declared:'NEXT_ACTION_DECLARED', session_finished:'SESSION_ENDING',
  unfinished_work_declared:'UNFINISHED_WORK_DECLARED',
});
function text(value, max=32768) {
  if(typeof value!=='string'||!value.length||value.length>max||value.includes('\0')) throw new Error('INVALID_LIVE_ARGUMENT');
  return value;
}
function bounded(value, depth=0) {
  if(depth>8) throw new Error('INVALID_LIVE_PAYLOAD');
  if(value===null||typeof value==='boolean') return;
  if(typeof value==='number'&&Number.isFinite(value)&&Math.abs(value)<=Number.MAX_SAFE_INTEGER) return;
  if(typeof value==='string'&&value.length<=4096) return;
  if(Array.isArray(value)&&value.length<=128) { for(const item of value) bounded(item,depth+1); return; }
  if(value&&Object.getPrototypeOf(value)===Object.prototype&&Object.keys(value).length<=128) {
    for(const [key,item] of Object.entries(value)) { text(key,128); bounded(item,depth+1); } return;
  }
  throw new Error('INVALID_LIVE_PAYLOAD');
}
export function buildLiveReport(kind,payload,correlationId) {
  if(!Object.hasOwn(LIVE_REPORT_TYPES,kind)||!payload||Object.getPrototypeOf(payload)!==Object.prototype) throw new Error('INVALID_LIVE_REPORT');
  bounded(payload);
  const args={payload:JSON.parse(JSON.stringify(payload))};
  if(correlationId!==undefined) args.correlation_id=text(correlationId,128);
  const report={name:'cgc_live_'+kind,arguments:args};
  if(Buffer.byteLength(JSON.stringify(report),'utf8')>14*1024) throw new Error('LIVE_PAYLOAD_LIMIT');
  return report; // Always a report. Validation and secret redaction are owned by CGC.
}
export class LiveClient {
  constructor({executable='cgcchild',prefix=[],timeout=30000}={}) {
    this.executable=text(executable);
    if(!Array.isArray(prefix)||prefix.length>8||!Number.isInteger(timeout)||timeout<100||timeout>120000) throw new Error('INVALID_LIVE_CLIENT');
    this.prefix=prefix.map(v=>text(v)); this.timeout=timeout;
  }
  invoke(args) {
    if(process.platform!=='win32') throw new Error('WINDOWS_REQUIRED');
    const result=spawnSync(this.executable,[...this.prefix,'live',...args.map(v=>text(v))],{
      shell:false,windowsHide:true,encoding:'utf8',timeout:this.timeout,maxBuffer:2*1024*1024,
    });
    if(result.error||result.signal||result.status!==0) throw new Error('LIVE_OPERATION_REFUSED');
    try { return JSON.parse(result.stdout); } catch { throw new Error('INVALID_LIVE_RESPONSE'); }
  }
  start(project,store) { return this.invoke(['start','--project',text(project),...(store?['--store',text(store)]:[])]); }
  list(store) { return this.invoke(['list',...(store?['--store',text(store)]:[])]); }
  status(session) { return this.invoke(['status','--session',text(session)]); }
  observe(session,{verifyRemote=false}={}) {
    if(typeof verifyRemote!=='boolean') throw new Error('INVALID_LIVE_ARGUMENT');
    return this.invoke(['observe','--session',text(session),...(verifyRemote?['--verify-remote']:[])]);
  }
  report(session,kind,payload,correlationId) {
    const event=buildLiveReport(kind,payload,correlationId);
    return this.invoke(['report','--session',text(session),'--event-type',LIVE_REPORT_TYPES[kind],
      '--payload',JSON.stringify(event.arguments.payload),...(correlationId?['--correlation-id',correlationId]:[])]);
  }
  checkpoint(session) { return this.invoke(['checkpoint','--session',text(session)]); }
  preserve(session) { return this.invoke(['preserve','--session',text(session)]); }
  recover(session) { return this.invoke(['recover','--session',text(session)]); }
  resume(session) { return this.invoke(['resume','--session',text(session)]); }
  openCapsule(path) { return this.invoke(['open','--input',text(path)]); }
}
