import test from 'node:test';
import assert from 'node:assert/strict';
const helper=await import('../native/trial-finalization.mjs').catch(e=>{if(e.code==='ERR_MODULE_NOT_FOUND')return {};throw e;});
test('native PASS requires verified owned exit, clean ACK and complete evidence seal',async()=>{
 assert.equal(typeof helper.finalizeNativeTrial,'function');
 for(const scenario of ['exit-timeout','ack-missing','partial-seal','success']){
  let seals=0;const current={runId:'run',runSnapshotId:'snapshot'};
  const stopped={...current,ok:scenario!=='exit-timeout',cleanup:{status:scenario==='exit-timeout'?'EXIT_TIMEOUT':'VERIFIED_EXIT'}};
  const after={...current,live:false,evidenceShutdown:{clean:scenario!=='ack-missing',ack:{}}};
  const result=await helper.finalizeNativeTrial({current,stop:async()=>stopped,read:async()=>after,finalize:async(_,{cleanShutdown})=>{
   seals++;assert.equal(cleanShutdown,scenario!=='ack-missing');return {manifest:{status:scenario==='success'?'EVIDENCE_COMPLETE':'EVIDENCE_PARTIAL'}};
  }});
  assert.equal(result.status,scenario==='success'?'PASS':'FAIL');
  assert.equal(seals,scenario==='exit-timeout'?0:1);
 }
});
