import test from 'node:test';
import assert from 'node:assert/strict';
import {validDecisionSnapshot, observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';

const uuid='00000000-0000-0000-0000-000000000001';
const point={status:'AVAILABLE',className:'net.minecraft.world.phys.Vec3',x:1.25,y:64.75,z:-2.5};
const block={status:'AVAILABLE',className:'net.minecraft.core.BlockPos',x:1,y:64,z:-3};
const ref=(namespace='memory',index=1)=>({status:'AVAILABLE',allocator:'SNAPSHOT_REFERENCE',targetRevision:19,token:`${namespace}:19:${index}`});
function tracker(){return {status:'AVAILABLE',className:'net.minecraft.world.entity.ai.behavior.BlockPosTracker',encoding:'TYPED_CACHED_MEMORY_V1',kind:'BLOCK_POSITION_TRACKER',data:{instanceIdentity:ref(),position:structuredClone(point),blockPosition:structuredClone(block),semantics:'CACHED_FIXED_TRACKER_FIELDS_NOT_VISIBILITY_QUERY'}};}
function snapshot(value=tracker()){
  return {schema:'kneekura.vanilla-decision-snapshot/v1',targetRevision:19,semantics:'MOB_COMPONENT_SNAPSHOT_ONLY',sections:{
    goal_scheduler:{status:'NOT_EXPOSED'},brain_memory:{status:'AVAILABLE',data:{entries:[{registered:true,present:true,key:'minecraft:look_target',value}],truncated:false}},
    brain_activities:{status:'NOT_EXPOSED'},navigation_path:{status:'NOT_EXPOSED'},movement_control:{status:'NOT_EXPOSED'}}};
}
test('typed memory rejects a component allocator token or a different revision, and identity lies after a cap',()=>{
  for(const mutate of [d=>{d.instanceIdentity.token='component:19:1';},d=>{d.instanceIdentity.targetRevision=20;},d=>{d.instanceIdentity.token='memory:20:1';},d=>{d.instanceIdentity.token='memory:19:257';},d=>{d.instanceIdentity.status='NOT_EXPOSED';}]){
    const value=tracker();mutate(value.data);assert.equal(validDecisionSnapshot(snapshot(value)),false);
  }
});
test('typed memory rejects incomplete facts advertised as available and nonfinite or fractional cached blocks',()=>{
  for(const mutate of [v=>{v.data.position.status='NOT_EXPOSED';},v=>{v.data.position.x=Infinity;},v=>{v.data.blockPosition.x=1.5;},v=>{v.kind='SELECTION';},v=>{delete v.data.position;}]){
    const value=tracker();mutate(value);assert.equal(validDecisionSnapshot(snapshot(value)),false);
  }
});
test('known cached fields survive identity exhaustion with Gson omitted token; absence and unsupported stay distinct',()=>{
  const value=tracker();value.status='PARTIAL';value.data.instanceIdentity={status:'NOT_EXPOSED',allocator:'SNAPSHOT_REFERENCE',targetRevision:19,detail:'REFERENCE_LIMIT'};
  assert.equal(validDecisionSnapshot(snapshot(value)),true);
  assert.equal(validDecisionSnapshot(snapshot({status:'AVAILABLE',className:'null'})),true);
  assert.equal(validDecisionSnapshot(snapshot({status:'NOT_EXPOSED',className:'custom.Tracker'})),true);
  const invalid=structuredClone(value);invalid.data.instanceIdentity.token=null;
  assert.equal(validDecisionSnapshot(snapshot(invalid)),false);
});
test('typed cached state alone cannot manufacture candidate, selection, execution or result decisions',()=>{
  const value=tracker();const row={v:1,kind:'observation',observationId:'obs:typed:1',debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,resourceEpoch:1,writerId:'server',writerSeq:1,level:'L2',lane:'AI_DECISION',observedAt:'2026-10-04T00:00:00.000Z',gameTime:100,scope:{kind:'ENTITY_UUID',entityUuid:uuid},source:{side:'SERVER',method:'typed-fixture'},epistemicStatus:'OBSERVED',completeness:{complete:true},payload:snapshot(value)};
  const model=observeDebugWorkspaceDecision({observations:[row],subjectUuid:uuid});
  assert.equal(model.stages.STATE.facts.some(f=>f.key==='brain_memory'||f.name==='brain_memory'),true);
  for(const stage of ['CANDIDATE','SELECTION','EXECUTION','RESULT'])assert.equal(model.stages[stage]?.facts?.length??0,0,stage);
});

test('actual WalkTarget -> EntityTracker -> cached Entity fields fit the typed branch while arbitrary deep structures stay rejected',()=>{
  const entity={status:'AVAILABLE',className:'net.minecraft.server.level.ServerPlayer',encoding:'TYPED_CACHED_MEMORY_V1',kind:'ENTITY_REFERENCE',data:{instanceIdentity:ref('entity',2),entityUuid:{status:'AVAILABLE',value:uuid},position:structuredClone(point),blockPosition:structuredClone(block),eyeHeight:{status:'AVAILABLE',value:1.62},semantics:'BASE_ENTITY_CACHED_FIELDS_ONLY_NOT_TRACKER_QUERY_OR_ACTUAL_MOTION'}};
  const tracking={status:'AVAILABLE',className:'net.minecraft.world.entity.ai.behavior.EntityTracker',encoding:'TYPED_CACHED_MEMORY_V1',kind:'ENTITY_TRACKER',data:{instanceIdentity:ref('memory',3),trackEyeHeight:true,entity,semantics:'CACHED_TRACKER_POLICY_NOT_CURRENT_POSITION_OR_VISIBILITY_QUERY'}};
  const walk={status:'AVAILABLE',className:'net.minecraft.world.entity.ai.memory.WalkTarget',encoding:'TYPED_CACHED_MEMORY_V1',kind:'WALK_TARGET',data:{instanceIdentity:ref('memory',4),speedModifier:.5,closeEnoughDist:2,target:tracking,semantics:'CACHED_WALK_PARAMETERS_NOT_ELIGIBILITY_OR_NAVIGATION_RESULT'}};
  assert.equal(validDecisionSnapshot(snapshot(walk)),true);
  const unrelated=snapshot();unrelated.unrelated={};let current=unrelated.unrelated;for(let i=0;i<13;i++){current.child={};current=current.child;}
  assert.equal(validDecisionSnapshot(unrelated),false,'historical unrelated depth limit remains enforced');
});
