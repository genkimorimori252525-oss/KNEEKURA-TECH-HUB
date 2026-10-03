import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import descriptor from '../adapters/twilightforest-anchor.json' with {type:'json'};
import {twilightForestDecisionAdapter} from '../adapters/twilightforest-decision-adapter.mjs';
import {createDecisionAdapterRegistry} from '../decision-adapter-sdk.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';
import {buildDecisionPacket} from '../decision-observation.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
function row(bossKind,state) {
  return {kind:'observation',lane:'AI_DECISION',observationId:'obs:tf:'+bossKind,gameTime:100,
    debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,scope:{kind:'ENTITY_UUID',entityUuid:uuid},
    source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},payload:{
      schema:'kneekura.mod-decision-snapshot/v1',semantics:'SOURCE_SPECIFIC_CACHED_SNAPSHOT_ONLY',targetRevision:1,sampleTick:100,
      descriptor,compatibilityStatus:'MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION',entityClass:'twilightforest.entity.boss.'+bossKind,
      data:{status:'AVAILABLE',bossKind,stateSemantics:'CACHED_STATE_NOT_ORIGINAL_TRANSITION_OR_REASON',state}}};
}
const capture=record=>createDecisionAdapterRegistry([twilightForestDecisionAdapter]).captureSnapshot([record]);
test('Java and retained SDK declare the same exact mapped TF generation',async()=>{
  const java=await readFile(new URL('../../forge-bridge/src/main/java/com/github/tartaricacid/touhoulittlemaid/sim/debug/KneekuraDebugTwilightForestDescriptor.java',import.meta.url),'utf8');
  const raw=java.match(/static final String JSON="""\s*([\s\S]*?)\s*""";/)[1];
  assert.deepEqual(JSON.parse(raw),descriptor);assert.equal(Object.keys(descriptor.classHashes).length,10);
});
test('Hydra keeps coordinator/head state and stored assigned targets without Vanilla selection claims',()=>{
  const record=row('Hydra',{numHeads:7,scope:'SELECTED_COORDINATOR_STORED_HEAD_CONTAINERS',
    heads:Array.from({length:7},(_,headNum)=>({headNum,prevState:'IDLE',currentState:'IDLE',nextState:null,
      nextStateSemantics:'AUTOMATIC_SENTINEL',ticksNeeded:60,ticksProgress:1,targetUuid:null,headUuid:null}))});
  const out=capture(record);assert.equal(out.facts[0].key,'twilightforest:hydra_heads');
  assert.equal(out.facts[0].value.heads.length,7);assert.equal(out.facts[0].causal_relation,'UNKNOWN_CAUSALITY');
  assert.equal(out.capabilities['twilightforest:original_transitions'].status,'NOT_EXPOSED');
  const bad=structuredClone(record);bad.payload.data.state.heads[1].headNum=0;
  assert.throws(()=>capture(bad),/TF_CACHED_STATE_CONTRACT/);
});
test('Snow Queen phase and Knight local formation remain distinct from exact transitions/group leadership',()=>{
  const snow=capture(row('SnowQueen',{phase:'SUMMON',beamActive:false,summonsRemaining:6,successfulDrops:0,maxDrops:2,damageWhileBeaming:0}));
  assert.equal(snow.facts[0].key,'twilightforest:snow_queen_phase');
  const knight=capture(row('KnightPhantom',{number:2,ticksProgress:10,currentFormation:'HOVER',chargePos:{x:0,y:64,z:0},
    groupIdentityStatus:'NOT_EXPOSED',leaderStatus:'NOT_EXPOSED'}));
  assert.equal(knight.facts[0].value.leaderStatus,'NOT_EXPOSED');
  const bad=row('KnightPhantom',{number:2,ticksProgress:10,currentFormation:'HOVER',chargePosStatus:'NOT_EXPOSED',
    groupIdentityStatus:'NOT_EXPOSED',leaderStatus:'AVAILABLE'});assert.throws(()=>capture(bad));
});
test('source-specific facts share the common Decision Packet and typed retained query without Vanilla substitutions',()=>{
  const record=row('SnowQueen',{phase:'SUMMON',beamActive:false,summonsRemaining:6,successfulDrops:0,maxDrops:2,damageWhileBeaming:0});
  const observation=observeDebugWorkspaceDecision({observations:[record],subjectUuid:uuid});
  const packet=buildDecisionPacket(observation);
  assert.equal(packet.schema,'kneekura.decision-observation-packet/v1');
  assert.equal(packet.stages.STATE.facts[0].adapter_namespace,'twilightforest');
  assert.equal(packet.stages.SELECTION,undefined);assert.equal(packet.capabilities.goal_eligibility.status,'NOT_EXPOSED');
  assert.equal(packet.stages.STATE.facts[1].value.mappedArtifactSha256,descriptor.mappedArtifactSha256);
  const query=queryDecisionDrilldown({observations:[record],subjectUuid:uuid,identity:{debugSessionId:'s',runId:'r',runSnapshotId:'snap',
    processEpoch:1,arenaEpoch:0,targetRevision:1},request:{channel:'mod_state',startTick:100,endTick:100,limit:1,maxNodes:1}});
  assert.equal(query.items[0].facts[0].value.phase,'SUMMON');assert.equal(query.items[0].primitives[0].subjectUuid,uuid);
});
test('Ur-Ghast preserves tantrum and cached custom direct-flight steering without invented A-star candidates',()=>{
  const out=capture(row('UrGhast',{inTantrum:false,damageUntilNextPhase:48,nextTantrumCry:10,wanderFactor:32,
    customFlight:{controllerClass:'twilightforest.entity.ai.control.NoClipMoveControl',courseChangeCooldown:2,
      operation:'MOVE_TO',wantedX:4,wantedY:70,wantedZ:2,speedModifier:1,candidatePopulationStatus:'NOT_EXPOSED',aStarExplanationStatus:'NOT_EXPOSED'}}));
  assert.equal(out.facts[0].key,'twilightforest:ur_ghast_custom_flight');
  assert.equal(out.facts[0].value.customFlight.aStarExplanationStatus,'NOT_EXPOSED');
  assert.equal(out.primitives.length,1);assert.equal(out.primitives[0].semantics,'DERIVED_PRESENTATION_ONLY');
});

test('Hydra accepts native Gson omitted nulls only with automatic sentinel and preserves missing references as unknown',()=>{
  const record=row('Hydra',{numHeads:7,scope:'SELECTED_COORDINATOR_STORED_HEAD_CONTAINERS',
    heads:Array.from({length:7},(_,headNum)=>({headNum,prevState:'IDLE',currentState:'IDLE',
      nextStateSemantics:'AUTOMATIC_SENTINEL',ticksNeeded:10,ticksProgress:9,headUuid:uuid}))});
  const before=JSON.stringify(record),out=capture(record),head=out.facts[0].value.heads[0];
  assert.equal(head.nextState,null);
  assert.equal(head.targetUuidStatus,'NOT_CAPTURED');
  assert.equal(head.targetUuid,undefined);
  assert.equal(head.headUuid,uuid);
  assert.equal(JSON.stringify(record),before);
  const bad=structuredClone(record);bad.payload.data.state.heads[0].nextStateSemantics='STORED_REQUESTED_STATE';
  assert.throws(()=>capture(bad),/TF_CACHED_STATE_CONTRACT/);
});
