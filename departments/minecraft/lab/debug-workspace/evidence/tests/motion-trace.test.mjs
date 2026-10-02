import assert from 'node:assert/strict';
import test from 'node:test';
import {
  SAMPLED_MOTION_TRACE_EPISTEMIC,SAMPLED_SEGMENT_SEMANTICS,
  assertValidSampledMotionTrace,buildSampledMotionTrace,
  extractSampledMotionTraceFromEvidenceStore,extractSampledMotionTraceFromObservations
} from '../motion-trace.mjs';

const U='00000000-0000-4000-8000-000000000001',P='00000000-0000-4000-8000-000000000002';
function row(t,id,extra={}){
  return {v:1,kind:'observation',observationId:id,debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',
    processEpoch:1,arenaEpoch:extra.arenaEpoch??0,resourceEpoch:0,writerId:'server',writerSeq:extra.writerSeq??t,
    level:'L1',lane:extra.lane??'SERVER_ENTITY_STATE',observedAt:new Date(1800000000000+t*50).toISOString(),gameTime:t,
    scope:extra.scope??{kind:'ENTITY_UUID',entityUuid:U},source:{side:'SERVER',method:'fixture'},
    epistemicStatus:'OBSERVED',completeness:{complete:true},
    payload:extra.payload??{dimension:'minecraft:overworld',x:t/10,y:64,z:0,vx:.2,vy:0,vz:0,alive:true,removed:false}};
}
function sample(id,t,pos,patch={}){
  return {sampleId:id,tick:t,position:pos,identity:{debugSessionId:'s',runId:'r',runSnapshotId:'snap',
    processEpoch:1,arenaEpoch:0,resourceEpoch:0,dimension:'minecraft:overworld',...(patch.identity||{})},
    source:{sourceId:'obs:'+id,kind:'fixture'}};
}
const req=(extra={})=>({entityUuid:U,traceClass:'MOB_ACTUAL',startTick:0,endTick:300,...extra});

test('versioned trace retains endpoint provenance and derived metrics',()=>{
  const tr=extractSampledMotionTraceFromObservations([
    row(100,'track',{lane:'SERVER_TARGET_TRACKED',payload:{tracked:true,type:'minecraft:zombie',dimension:'minecraft:overworld'}}),
    row(100,'a'),row(105,'b',{payload:{dimension:'minecraft:overworld',x:11,y:65,z:1,vx:.3,vy:.1,vz:.2}})
  ],req({debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',startTick:100,endTick:110}));
  assert.equal(tr.epistemicLabel,SAMPLED_MOTION_TRACE_EPISTEMIC);
  assert.equal(tr.subject.entityType,'minecraft:zombie');
  assert.equal(tr.segments[0].semantics,SAMPLED_SEGMENT_SEMANTICS);
  assert.deepEqual(tr.provenance.sourceIds,['a','b']);
  assert.equal(tr.metrics.durationTicks,5); assert.equal(tr.metrics.gapCount,0);
  assert.ok(tr.metrics.sampledPolylineLength>0); assert.equal(tr.sourcePolicy.continuousPathClaimed,false);
  assertValidSampledMotionTrace(tr);
});

test('missing retained interval breaks instead of interpolating',()=>{
  const tr=extractSampledMotionTraceFromObservations([row(100,'a'),row(205,'b')],req({startTick:100,endTick:205,maxContinuityTicks:100}));
  assert.equal(tr.segments.length,0); assert.equal(tr.gaps[0].reason,'SOURCE_GAP_EXCEEDED');
  assert.equal(tr.metrics.sampledPolylineLength,0);
});

test('run epoch and dimension boundaries never become ordinary segments',()=>{
  const epoch=buildSampledMotionTrace({traceClass:'MOB_ACTUAL',subject:{entityUuid:U},samples:[
    sample('a',1,[0,64,0]),sample('b',2,[1,64,0],{identity:{arenaEpoch:1}})]});
  assert.equal(epoch.gaps[0].reason,'ARENA_EPOCH_CHANGED');
  const dim=buildSampledMotionTrace({traceClass:'MOB_ACTUAL',subject:{entityUuid:U},samples:[
    sample('a',1,[0,64,0]),sample('b',2,[1,64,0],{identity:{dimension:'minecraft:the_nether'}})]});
  assert.equal(dim.gaps[0].reason,'DIMENSION_CHANGED');
  const run=buildSampledMotionTrace({traceClass:'MOB_ACTUAL',subject:{entityUuid:U},samples:[
    sample('a',1,[0,64,0]),sample('b',2,[1,64,0],{identity:{runId:'r2',runSnapshotId:'snap2'}})]});
  assert.equal(run.gaps[0].reason,'RUN_IDENTITY_CHANGED');
});

test('explicit teleport receipt is a provenance-bound discontinuity',()=>{
  const tr=extractSampledMotionTraceFromObservations([
    row(100,'a'),
    row(103,'tp',{lane:'ACTION_APPLIED',payload:{actionId:'move',subjectUuid:U,measuredPose:{x:20,y:70,z:20}}}),
    row(105,'b',{payload:{dimension:'minecraft:overworld',x:20,y:70,z:20,vx:0,vy:0,vz:0}})
  ],req({startTick:100,endTick:105}));
  assert.equal(tr.segments.length,0); assert.equal(tr.gaps[0].reason,'EXPLICIT_TELEPORT');
  assert.equal(tr.gaps[0].sourceId,'tp'); assert.ok(tr.provenance.sourceIds.includes('tp'));
});

test('tracked false observation marks entity unavailable',()=>{
  const tr=extractSampledMotionTraceFromObservations([
    row(100,'a'),
    row(103,'gone',{lane:'SERVER_TARGET_TRACKED',payload:{tracked:false,reason:'not_loaded_or_absent'}}),
    row(105,'b')
  ],req({startTick:100,endTick:105}));
  assert.equal(tr.gaps[0].reason,'ENTITY_UNAVAILABLE'); assert.equal(tr.gaps[0].sourceId,'gone');
});

test('Ghast-like 3D wandering preserves vertical facts',()=>{
  const tr=buildSampledMotionTrace({traceClass:'MOB_ACTUAL',subject:{entityUuid:U,entityType:'minecraft:ghast'},
    maxContinuityTicks:5,samples:[sample('g1',10,[0,70,0]),sample('g2',15,[4,76,3]),sample('g3',20,[1,72,7])]});
  assert.equal(tr.segments.length,2); assert.equal(tr.metrics.minAltitude,70); assert.equal(tr.metrics.maxAltitude,76);
  assert.equal(tr.metrics.sampledPolylineLength,Math.hypot(4,6,3)+Math.hypot(-3,-4,4));
});

test('Mob and projectile are independently attributable in one retained set',()=>{
  const rows=[row(1,'m1'),row(2,'m2'),
    row(1,'p1',{scope:{kind:'ENTITY_UUID',entityUuid:P},payload:{dimension:'minecraft:overworld',x:0,y:66,z:0,vx:1,vy:.4,vz:0}}),
    row(2,'p2',{scope:{kind:'ENTITY_UUID',entityUuid:P},payload:{dimension:'minecraft:overworld',x:1,y:66.3,z:0,vx:1,vy:.2,vz:0}})];
  const mob=extractSampledMotionTraceFromObservations(rows,req({endTick:2}));
  const pro=extractSampledMotionTraceFromObservations(rows,{entityUuid:P,entityType:'minecraft:arrow',traceClass:'PROJECTILE_ACTUAL',startTick:1,endTick:2});
  assert.deepEqual(mob.provenance.sourceIds,['m1','m2']); assert.deepEqual(pro.provenance.sourceIds,['p1','p2']);
  assert.equal(pro.metrics.directlyObservedSpeed.sampleCount,2);
});

test('EvidenceStore adapter is read-only',async()=>{
  const rows=[row(1,'a'),row(2,'b')],before=JSON.stringify(rows); let reads=0;
  const tr=await extractSampledMotionTraceFromEvidenceStore({async readObservations(){reads++;return rows;}},req({endTick:2}));
  assert.equal(reads,1); assert.equal(JSON.stringify(rows),before); assert.equal(tr.samples.length,2);
});

test('validator rejects a segment whose retained endpoint was removed',()=>{
  const tr=buildSampledMotionTrace({traceClass:'MOB_ACTUAL',subject:{entityUuid:U},samples:[sample('a',1,[0,64,0]),sample('b',2,[1,64,0])]});
  tr.samples.pop();
  assert.throws(()=>assertValidSampledMotionTrace(tr),/segment references missing sample endpoint/);
});
