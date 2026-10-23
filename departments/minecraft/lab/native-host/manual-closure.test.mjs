import test from 'node:test';import assert from 'node:assert/strict';
import {validateManualClosure} from './manual-closure.mjs';
import fs from 'node:fs/promises';import path from 'node:path';import os from 'node:os';
import {EvidenceStore} from '../debug-workspace/evidence/store.mjs';
function sample(){const raw=[1,2].map(n=>({writerId:'manual-25',writerSeq:n,observationId:'event-'+n,producerDeltaApplied:true,payload:{requestHash:'hash',healthAtEnd:20}}));return {raw,canonical:structuredClone(raw),ack:{finalWriterSeq:2},native:{pid:25,events:2,requestHash:'hash'},runtimePid:25,requestHash:'hash'};}
test('identical discrete native events each reconcile to their canonical ID',()=>assert.equal(validateManualClosure(sample()).canonicalEvents,2));
for(const [name,mutate] of [
 ['coalesced repeated event',x=>x.canonical.pop()],['unprocessed ACK tail',x=>x.ack.finalWriterSeq=3],['raw gap',x=>x.raw[1].writerSeq=3],['changed payload',x=>x.canonical[1].payload.healthAtEnd=0],['wrong runtime',x=>x.runtimePid=26],['missing event semantics',x=>delete x.raw[0].producerDeltaApplied],['rewritten identity',x=>x.canonical[0].observationId='other']
])test('reject '+name,()=>{const x=sample();mutate(x);assert.throws(()=>validateManualClosure(x));});
test('canonical store preserves identical discrete events while ordinary L1 snapshots still aggregate',async t=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'tank-event-store-'));t.after(async()=>{assert(path.basename(root).startsWith('tank-event-store-')&&path.dirname(root)===path.resolve(os.tmpdir()));await fs.rm(root,{recursive:true,force:true});});
 for(const discrete of [false,true]){
  const store=new EvidenceStore({runDir:path.join(root,String(discrete)),debugSessionId:'session',runId:'run',runSnapshotId:'snapshot'});await store.init();
  const base={v:1,kind:'observation',debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,arenaEpoch:1,resourceEpoch:1,level:'L1',lane:'MANUAL_INTERACTION',observedAt:new Date().toISOString(),epistemicStatus:'OBSERVED',scope:{kind:'ENTITY_UUID',entityUuid:'11111111-1111-4111-8111-111111111111'},source:{side:'SERVER',method:'POST_HURT_END'},writerId:'manual-25',payload:{healthAtEnd:20},...(discrete?{producerDeltaApplied:true}:{})};
  await store.appendObservation({...base,writerSeq:1,observationId:'event-1'});await store.appendObservation({...base,writerSeq:2,observationId:'event-2'});
  assert.equal((await store.readObservations()).length,discrete?2:1);
 }
});
