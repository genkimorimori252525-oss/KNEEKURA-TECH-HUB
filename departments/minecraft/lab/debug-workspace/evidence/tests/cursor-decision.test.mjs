import test from 'node:test';
import assert from 'node:assert/strict';
import {buildCursorDecisionPacket,selectTankCursorTicks} from '../cursor-decision.mjs';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1};
const uuid='00000000-0000-0000-0000-000000000001';
const row=(tick,x)=>({kind:'observation',...identity,lane:'SERVER_ENTITY_STATE',observationId:'obs:'+tick,gameTime:tick,
  scope:{kind:'ENTITY_UUID',entityUuid:uuid},source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},
  payload:{targetRevision:1,dimension:'minecraft:overworld',x,y:64,z:0}});
const build=extra=>buildCursorDecisionPacket({observations:[row(100,0),row(110,999)],identity,subjectUuid:uuid,window:{startTick:100,endTick:120},cursorTick:105,maxGapTicks:10,...extra});
test('cursor105 excludes110 without relabelling original100 facts or positions',()=>{
  const packet=build();assert.equal(packet.cursorTick,105);assert.equal(packet.layers.motion.trace.samples.length,1);
  assert.equal(packet.layers.motion.trace.samples[0].tick,100);
  assert.equal(JSON.stringify(packet.overview).includes('999'),false);
  const facts=Object.values(packet.overview.stages).flatMap(s=>s.facts);
  assert(facts.length>0);assert(facts.every(f=>f.observedTick===100&&f.ageTicks===5));
  assert.equal(packet.semantics.futureEvidenceIncluded,false);
});
test('stopped samples retain trace history and gaps remain breaks',()=>{
  const packet=build({observations:[row(100,0),row(105,1),row(110,1),row(115,1)],cursorTick:115});
  assert.equal(packet.layers.motion.trace.samples.length,4);assert.equal(packet.layers.motion.trace.samples[0].x,0);
  const gap=build({observations:[row(100,0),row(115,1)],cursorTick:115});assert.equal(gap.layers.motion.trace.segments.length,0);
  assert.equal(gap.layers.motion.trace.gaps.length,1);
});
test('display cap and byte/input bounds are explicit and do not alter evidence',()=>{
  const observations=Array.from({length:140},(_,i)=>row(i,i/10)),before=JSON.stringify(observations);
  const packet=build({observations,window:{startTick:0,endTick:140},cursorTick:139});
  assert.equal(packet.displaySelection.motion.eligibleCount,140);assert.equal(packet.displaySelection.motion.displayedCount,128);
  assert.equal(packet.displaySelection.motion.omittedCount,12);assert.equal(JSON.stringify(observations),before);
  assert.throws(()=>build({cursorTick:121}),/CURSOR/);
  assert.throws(()=>build({observations:Array(50001).fill(row(100,0))}),/LIMIT/);
});

test('cursor selection reports deterministic omission without fabricating samples at endpoints',()=>{
  const args={observations:Array.from({length:300},(_,i)=>row(i+1,i)),identity,subjectUuid:uuid,window:{startTick:0,endTick:301},maxCursors:32};
  const a=selectTankCursorTicks(args);assert.deepEqual(a,selectTankCursorTicks(args));
  assert.equal(a.eligibleCount,302);assert.equal(a.displayedCount,32);assert.equal(a.omittedCount,270);
  assert.equal(a.ticks[0],0);assert.equal(a.ticks.at(-1),301);assert.equal(a.endpointsAreCursorBoundsNotObservations,true);
  assert.throws(()=>selectTankCursorTicks({...args,maxCursors:257}),/BOUND/);
});
