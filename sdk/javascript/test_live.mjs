import assert from 'node:assert/strict';
import {buildLiveReport,LiveClient,LIVE_REPORT_TYPES,LIVE_EVENT_VERSION} from './index.mjs';
assert.equal(LIVE_EVENT_VERSION,'cgc-live-event-0.1');
let checks=1;
for(const name of Object.keys(LIVE_REPORT_TYPES)) {
  const source={text:'engineering fact'};
  const report=buildLiveReport(name,source,'correlation-1');
  source.text='changed';
  assert.equal(report.name,'cgc_live_'+name);
  assert.equal(report.arguments.payload.text,'engineering fact');
  assert.equal(report.arguments.correlation_id,'correlation-1');
  checks+=3;
}
for(const kind of ['PUSH_VERIFIED','execute','__proto__','constructor']) {
  assert.throws(()=>buildLiveReport(kind,{})); checks++;
}
for(const payload of [null,[],{data:'x'.repeat(4097)},{number:NaN},{number:Infinity},{number:2**54}, {nested:{nested:{nested:{nested:{nested:{nested:{nested:{nested:{nested:1}}}}}}}}}]) {
  assert.throws(()=>buildLiveReport('command_report',payload)); checks++;
}
assert.throws(()=>new LiveClient({prefix:['x'.repeat(32769)]})); checks++;
assert.throws(()=>new LiveClient({timeout:Infinity})); checks++;
assert.throws(()=>new LiveClient({executable:'bad\0name'})); checks++;
const client=new LiveClient();
client.invoke=args=>args;
assert.deepEqual(client.observe('session'),['observe','--session','session']); checks++;
assert.deepEqual(client.observe('session',{verifyRemote:true}),['observe','--session','session','--verify-remote']); checks++;
assert.throws(()=>client.observe('session',{verifyRemote:'true'})); checks++;
assert.equal(client.report('session','push_reported',{sha:'abc'})[4],'PUSH_REPORTED'); checks++;
console.log(`Live SDK: ${checks} contract checks passed`);
