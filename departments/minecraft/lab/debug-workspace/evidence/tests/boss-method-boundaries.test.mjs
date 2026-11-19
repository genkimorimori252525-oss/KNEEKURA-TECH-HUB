import test from 'node:test';
import assert from 'node:assert/strict';
import anchor from '../adapters/twilightforest-anchor.json' with {type:'json'};
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';

const subject='00000000-0000-0000-0000-000000000001';
const member='00000000-0000-0000-0000-000000000002';
const target='00000000-0000-0000-0000-000000000003';
const knight='twilightforest.entity.boss.KnightPhantom';
const goal='twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal';
const hydra='twilightforest.entity.boss.Hydra';
const head='twilightforest.entity.boss.HydraHeadContainer';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
const proof=kind=>({mappedArtifactSha256:anchor.mappedArtifactSha256,
  classHashes:kind==='KnightPhantom'?{[knight]:anchor.classHashes[knight],[goal]:'bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1'}:
    {[hydra]:anchor.classHashes[hydra],[head]:anchor.classHashes[head]},
  compatibilityStatus:'MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION'});
const knightState=()=>({number:0,currentFormation:'SMALL_CLOCKWISE',ticksProgress:0});
function row(kind){
  let data;
  if(kind==='MOD_KNIGHT_LEADER_RETURN')data={bossKind:'KnightPhantom',methodOwner:goal,methodName:'isThisTheLeader',
    sourceUuid:subject,sourceProof:proof('KnightPhantom'),leaderResult:true,originalListClass:'java.util.ArrayList',
    originalListCount:2,maxMembers:2,truncated:false,sourceStateAtReturn:knightState(),
    membersAtReturn:[{listIndex:0,entityClass:knight,entityUuid:subject,stateStatus:'AVAILABLE',cachedState:knightState(),targetUuid:target},
      {listIndex:1,entityClass:knight,entityUuid:member,stateStatus:'AVAILABLE',cachedState:{...knightState(),number:1},targetUuid:target}],
    returnScope:'ORIGINAL_LEADER_PREDICATE_RETURN',memberStateScope:'CACHED_FIELDS_AT_RETURN',groupIdentityStatus:'NOT_EXPOSED',sharedTargetStatus:'NOT_EXPOSED'};
  if(kind==='MOD_KNIGHT_MEMBER_DISPATCH_RETURN')data={bossKind:'KnightPhantom',methodOwner:goal,methodName:'broadcastMyFormation',
    sourceUuid:subject,sourceProof:proof('KnightPhantom'),memberUuid:member,memberStateAtReturn:{...knightState(),number:1},
    targetUuid:target,dispatchScope:'ORIGINAL_LOOP_MEMBER_SWITCH_RETURN',requestedValueStatus:'NOT_CAPTURED',
    stateChangeStatus:'NOT_EXPOSED',groupIdentityStatus:'NOT_EXPOSED'};
  if(kind==='MOD_HYDRA_TARGET_RETURN')data={bossKind:'Hydra',methodOwner:head,methodName:'setTargetEntity',
    sourceUuid:subject,sourceProof:proof('Hydra'),headNum:0,requestedTargetUuid:target,cachedTargetUuid:target,
    assignmentScope:'ORIGINAL_TARGET_SETTER_RETURN',attackSuccessStatus:'NOT_EXPOSED'};
  if(kind==='MOD_HYDRA_STATE_WRITE_CHECKPOINT')data={bossKind:'Hydra',methodOwner:head,methodName:'advanceHeadState',
    sourceUuid:subject,sourceProof:proof('Hydra'),headNum:0,previousState:'IDLE',currentState:'MORTAR_BEGINNING',
    valueChanged:true,targetUuid:target,ticksProgress:0,ticksNeeded:40,isSecondaryAttacking:false,
    activeAttackType:'MORTAR',attackTypeScope:'DERIVED_FROM_STORED_STATE',
    assignmentScope:'AFTER_ORIGINAL_CONDITIONAL_CURRENT_STATE_WRITE',reasonStatus:'NOT_EXPOSED',attackSuccessStatus:'NOT_EXPOSED'};
  return {kind:'observation',lane:'AI_DECISION',observationId:'obs:boss:'+kind,gameTime:100,...identity,
    scope:{kind:'ENTITY_UUID',entityUuid:subject},source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},
    payload:{schema:'kneekura.original-decision-event/v1',semantics:kind.endsWith('CHECKPOINT')?
      'ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY':'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,burstId:'burst:1:90',
      eventIndex:1,kind,observerCostNanos:1,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data}};
}

test('actual leader return keeps original member targets without inventing a persistent shared target or leader UUID',()=>{
  const r=row('MOD_KNIGHT_LEADER_RETURN'),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},caps={},timeline=[];appendOriginalDecisionEvents([r],stages,caps,timeline);
  assert.equal(stages.EVALUATION.facts[0].value.leaderResult,true);assert.equal(stages.SELECTION,undefined);
  assert.equal(stages.EVALUATION.facts[0].value.membersAtReturn[1].targetUuid,target);
  assert.equal(caps.mod_coordination.status,'PARTIAL');assert.equal(JSON.stringify(r),before);
});
test('member dispatch identifies the actual assigned member, without guessing skipped members or before/after value change',()=>{
  const r=row('MOD_KNIGHT_MEMBER_DISPATCH_RETURN');assert.equal(validOriginalDecisionEvent(r),true);
  const out=observeDebugWorkspaceDecision({observations:[r],subjectUuid:subject,identity});
  assert.equal(out.stages.EXECUTION.facts[0].value.memberUuid,member);
  assert.equal(out.stages.EXECUTION.facts[0].value.stateChangeStatus,'NOT_EXPOSED');
});
test('leader predicate remains an original boolean when the retained member prefix is incomplete or opaque',()=>{
  const r=row('MOD_KNIGHT_LEADER_RETURN'),d=r.payload.data;d.leaderResult=false;
  d.originalListCount=3;d.truncated=true;
  d.membersAtReturn[1]={listIndex:1,entityClass:'custom.Knight',stateStatus:'NOT_EXPOSED',detail:'UNSUPPORTED_MEMBER_CLASS'};
  assert.equal(validOriginalDecisionEvent(r),true);
  d.membersAtReturn[1].targetUuid=target;assert.equal(validOriginalDecisionEvent(r),false);
});
test('Hydra original target assignment distinguishes null and exact assigned target from attack success',()=>{
  const r=row('MOD_HYDRA_TARGET_RETURN');assert.equal(validOriginalDecisionEvent(r),true);
  r.payload.data.requestedTargetUuid=null;r.payload.data.cachedTargetUuid=null;assert.equal(validOriginalDecisionEvent(r),true);
  r.payload.data.cachedTargetUuid=target;assert.equal(validOriginalDecisionEvent(r),false);
});
test('existing Gson transport may omit nullable Boss target UUIDs without inventing a retained null',()=>{
  const leader=row('MOD_KNIGHT_LEADER_RETURN');delete leader.payload.data.membersAtReturn[0].targetUuid;
  const dispatch=row('MOD_KNIGHT_MEMBER_DISPATCH_RETURN');delete dispatch.payload.data.targetUuid;
  const assigned=row('MOD_HYDRA_TARGET_RETURN');delete assigned.payload.data.requestedTargetUuid;delete assigned.payload.data.cachedTargetUuid;
  const state=row('MOD_HYDRA_STATE_WRITE_CHECKPOINT');delete state.payload.data.targetUuid;
  for(const r of [leader,dispatch,assigned,state]){
    const before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
    const stages={},caps={},timeline=[];appendOriginalDecisionEvents([r],stages,caps,timeline);
    assert.equal(JSON.stringify(r),before,'missing target remains absent, rather than reconstructed');
  }
  assigned.payload.data.cachedTargetUuid=target;assert.equal(validOriginalDecisionEvent(assigned),false);
  for(const value of [false,123,'invalid-uuid',{}]){
    dispatch.payload.data.targetUuid=value;assert.equal(validOriginalDecisionEvent(dispatch),false);
  }
});
test('Hydra conditional write is algorithm state and its derived attack type is not an executed attack',()=>{
  const r=row('MOD_HYDRA_STATE_WRITE_CHECKPOINT');assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},caps={},timeline=[];appendOriginalDecisionEvents([r],stages,caps,timeline);
  assert.equal(stages.STATE.facts[0].epistemic_status,'INSTRUMENTED_ALGORITHM_STATE');
  assert.equal(stages.EXECUTION,undefined);assert.equal(stages.RESULT,undefined);
  r.payload.data.previousState='MORTAR_BEGINNING';r.payload.data.valueChanged=false;
  assert.equal(validOriginalDecisionEvent(r),true); // an assignment need not change the enum value
});
test('new Boss boundaries reject forged source/owner/context, invalid lists, target contradictions and invented attack reasons',()=>{
  for(const kind of ['MOD_KNIGHT_LEADER_RETURN','MOD_KNIGHT_MEMBER_DISPATCH_RETURN','MOD_HYDRA_TARGET_RETURN','MOD_HYDRA_STATE_WRITE_CHECKPOINT']){
    for(const mutate of [d=>d.sourceUuid=member,d=>d.methodOwner='custom.Owner',d=>d.sourceProof.classHashes={},
      d=>d.sourceProof.compatibilityStatus='VERSION_ONLY',d=>d.leaderUuid=subject,d=>d.reason='INVENTED']){
      const r=row(kind);mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
    }
    const r=row(kind);r.arenaEpoch=3;
    const out=observeDebugWorkspaceDecision({observations:[r],subjectUuid:subject,identity});
    assert.equal(Object.values(out.stages).some(s=>s.facts?.some(f=>f.key===kind.toLowerCase())) ,false);
  }
  for(const mutate of [d=>d.originalListClass='custom.List',d=>d.maxMembers=17,d=>d.membersAtReturn[1].listIndex=0,
    d=>d.membersAtReturn[1].entityClass='custom.Knight',d=>d.sharedTargetStatus='AVAILABLE']){
    const r=row('MOD_KNIGHT_LEADER_RETURN');mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
  for(const mutate of [d=>d.headNum=7,d=>d.activeAttackType='BITE',d=>d.valueChanged=false,d=>d.attackSuccessStatus='AVAILABLE']){
    const r=row('MOD_HYDRA_STATE_WRITE_CHECKPOINT');mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
});
