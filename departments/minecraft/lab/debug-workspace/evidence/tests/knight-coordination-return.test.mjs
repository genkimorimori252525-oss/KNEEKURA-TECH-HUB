import test from 'node:test';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const knight='twilightforest.entity.boss.KnightPhantom';
const goal='twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(){return {kind:'observation',lane:'AI_DECISION',observationId:'obs:knight:broadcast:1',gameTime:100,...identity,
  scope:{kind:'ENTITY_UUID',entityUuid:uuid},source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},
  payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',
    targetRevision:1,burstId:'burst:1:90',eventIndex:1,kind:'MOD_COORDINATION_RETURN',observerCostNanos:1,
    observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{
      bossKind:'KnightPhantom',methodOwner:goal,methodName:'broadcastMyFormation',sourceUuid:uuid,
      sourceStateAtReturn:{number:0,currentFormation:'SMALL_CLOCKWISE',ticksProgress:0},
      sourceProof:{mappedArtifactSha256:'7d7842c3c66d355c94bd726ef69ad14ac4f944061198927c3eb54a728e23580a',
        goalClassSha256:'bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1',
        knightClassSha256:'5be6108fbd0606e7c03060fbe843afe8a8b2b1c57247f71f146ad307b695292f',
        compatibilityStatus:'MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION'},
      originalListClass:'java.util.ArrayList',originalListCount:2,maxMembers:16,truncated:false,
      membersAtReturn:[{listIndex:0,entityClass:knight,entityUuid:uuid,stateStatus:'AVAILABLE',
        cachedState:{number:0,currentFormation:'SMALL_CLOCKWISE',ticksProgress:0}},
        {listIndex:1,entityClass:knight,entityUuid:'00000000-0000-0000-0000-000000000002',stateStatus:'AVAILABLE',
          cachedState:{number:1,currentFormation:'ATTACK_PLAYER_ATTACK',ticksProgress:12}}],
      dispatchScope:'ORIGINAL_PASSED_LIST_AFTER_BROADCAST',memberStateScope:'CACHED_FIELDS_AT_RETURN',
      affectedMembersStatus:'NOT_EXPOSED',leaderDecisionStatus:'NOT_EXPOSED',groupIdentityStatus:'NOT_EXPOSED'}}};}
test('Knight broadcast retains original passed-list order and post-state without inferring leader or affected members',()=>{
  const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
  assert.equal(stages.EXECUTION.facts[0].key,'mod_coordination_return');
  assert.equal(stages.SELECTION,undefined);assert.equal(capabilities.mod_coordination.status,'PARTIAL');
  assert.deepEqual(timeline[0].source_observation_ids,[r.observationId]);
  const out=observeDebugWorkspaceDecision({observations:[r],subjectUuid:uuid,identity});
  assert.equal(out.stages.EXECUTION.facts[0].value.membersAtReturn[1].cachedState.currentFormation,'ATTACK_PLAYER_ATTACK');
  assert.equal(JSON.stringify(r),before);
});
test('Knight coordination rejects forged source/context, invented leader, and inconsistent collection bounds',()=>{
  for(const mutate of [d=>d.sourceUuid='00000000-0000-0000-0000-000000000003',
    d=>d.sourceProof.goalClassSha256='a'.repeat(64),d=>d.sourceProof.compatibilityStatus='VERSION_ONLY',
    d=>d.leaderDecisionStatus='AVAILABLE',d=>d.affectedMembersStatus='AVAILABLE',d=>d.groupIdentityStatus='AVAILABLE',d=>d.leaderUuid=uuid,
    d=>d.originalListClass='custom.List',d=>d.originalListCount=1,d=>d.maxMembers=17,d=>d.truncated=true,
    d=>d.membersAtReturn[1].listIndex=0,d=>d.membersAtReturn[0].cachedState.currentFormation='INVENTED',
    d=>d.membersAtReturn[1].entityClass='custom.Knight']) {
    const r=row();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);
  }
  const r=row();r.arenaEpoch=3;
  const out=observeDebugWorkspaceDecision({observations:[r],subjectUuid:uuid,identity});
  assert.equal(out.stages.EXECUTION?.facts?.some(f=>f.key==='mod_coordination_return')??false,false);
});
test('bounded partial collection preserves unknown custom members without calling them Vanilla or known Knight state',()=>{
  const r=row(),d=r.payload.data;d.originalListCount=3;d.maxMembers=2;d.truncated=true;
  d.membersAtReturn[1]={listIndex:1,entityClass:'custom.Knight',stateStatus:'NOT_EXPOSED',detail:'UNSUPPORTED_MEMBER_CLASS'};
  assert.equal(validOriginalDecisionEvent(r),true);
  d.membersAtReturn[1].entityUuid=uuid;assert.equal(validOriginalDecisionEvent(r),false);
});
