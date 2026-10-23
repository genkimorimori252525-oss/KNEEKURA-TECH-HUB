import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
export function validateManualClosure({raw,canonical,ack,native,requestHash,runtimePid}){
 assert.equal(native.pid,runtimePid);assert.equal(native.requestHash,requestHash);assert.equal(ack.finalWriterSeq,native.events);assert.equal(raw.length,native.events);
 const writer='manual-'+runtimePid,actual=canonical.filter(r=>r.writerId===writer);assert.equal(actual.length,raw.length,'TANK_MANUAL_CANONICAL_COUNT');
 for(let i=0;i<raw.length;i++){
  const r=raw[i],c=actual[i];assert.equal(r.writerId,writer);assert.equal(r.writerSeq,i+1,'TANK_MANUAL_RAW_SEQUENCE');assert.equal(r.producerDeltaApplied,true,'TANK_MANUAL_DISCRETE_EVENTS');
  assert.equal(r.payload.requestHash,requestHash);assert.equal(c.observationId,r.observationId,'TANK_MANUAL_CANONICAL_ID');
  for(const key of Object.keys(r))assert.deepEqual(c[key],r[key],'TANK_MANUAL_CANONICAL_CONTENT_'+key);
 }
 return {rawEvents:raw.length,canonicalEvents:actual.length,finalWriterSeq:ack.finalWriterSeq,status:'EXACT_DISCRETE_EVENT_CLOSURE'};
}
export async function verifyManualClosure(runDir,ack,native,requestHash,runtimePid){
 const rawFile=path.join(runDir,'evidence/raw','manual-'+runtimePid+'.jsonl');const parse=async file=>(await fs.readFile(file,'utf8')).trim().split('\n').filter(Boolean).map(JSON.parse);
 return validateManualClosure({raw:await parse(rawFile),canonical:await parse(path.join(runDir,'evidence/observations.jsonl')),ack,native,requestHash,runtimePid});
}
