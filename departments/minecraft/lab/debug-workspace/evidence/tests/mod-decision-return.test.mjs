import test from 'node:test';
import assert from 'node:assert/strict';
import base from '../adapters/twilightforest-anchor.json' with {type:'json'};
import {createDecisionAdapterRegistry} from '../decision-adapter-sdk.mjs';
import {twilightForestTransitionAdapter} from '../adapters/twilightforest-transition-adapter.mjs';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {observeDebugWorkspaceDecision} from '../debug-workspace-decision-adapter.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1};
function row() {
  return {kind:'observation',lane:'AI_DECISION',observationId:'obs:tf-return:1',gameTime:100,...identity,
    scope:{kind:'ENTITY_UUID',entityUuid:uuid},source:{side:'SERVER'},epistemicStatus:'OBSERVED',completeness:{complete:true},
    payload:{schema:'kneekura.mod-decision-return/v1',semantics:'ORIGINAL_MOD_INVOCATION_RETURN_ONLY',
      targetRevision:1,returnTick:100,returnLocalTick:100,localTickScope:'LAST_COMPLETED_SERVER_END_COUNTER',
      burstId:'burst:1:95',eventIndex:1,kind:'MOD_TRANSITION_RETURN',
      descriptor:twilightForestTransitionAdapter.descriptor,entityClass:'twilightforest.entity.boss.SnowQueen',
      compatibilityStatus:'MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION',observerCostNanos:1,
      observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{bossKind:'SnowQueen',
        methodOwner:'twilightforest.entity.boss.SnowQueen',methodName:'setCurrentPhase',requestedValue:'SUMMON',requestedValueStatus:'AVAILABLE',
        cachedState:{phase:'SUMMON',beamActive:false,summonsRemaining:6,successfulDrops:0,maxDrops:0,damageWhileBeaming:0},
        stateChangeStatus:'NOT_EXPOSED',reasonStatus:'NOT_EXPOSED'}}};
}
test('MOD burst channel is explicit and excluded from existing default channel selection',()=>{
  assert.equal(decisionBurstFromArgs([]),null);
  assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('mod'),false);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','mod']).channels,['mod']);
});
test('SDK burst retains exact original method-return source without pretending setter calls prove changes or reasons',()=>{
  const r=row(),before=JSON.stringify(r),registry=createDecisionAdapterRegistry([twilightForestTransitionAdapter]);
  assert.equal(registry.acceptsBurst(r),true);assert.equal(registry.captureSnapshot([r]),null);
  const out=registry.captureBurst([r]);
  assert.equal(out.descriptor.id,'twilightforest:boss-original-return');
  assert.equal(out.descriptor.mappedArtifactSha256,base.mappedArtifactSha256);
  assert.equal(out.facts[0].epistemic_status,'DIRECT_OBSERVED');
  assert.equal(out.facts[0].value.stateChangeStatus,'NOT_EXPOSED');
  assert.equal(out.facts[0].value.reasonStatus,'NOT_EXPOSED');
  assert.deepEqual(out.facts[0].source_observation_ids,[r.observationId]);assert.equal(JSON.stringify(r),before);
  const observation=observeDebugWorkspaceDecision({observations:[r],subjectUuid:uuid,identity});
  assert.equal(observation.stages.EXECUTION.facts[0].key,'twilightforest:original_invocation_return');
  assert.equal(observation.stages.SELECTION,undefined);
  assert.equal(observation.timeline[0].kind,'MOD_TRANSITION_METHOD_RETURN');
  const query=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,
    request:{channel:'mod_returns',startTick:100,endTick:100,limit:1,maxNodes:1}});
  assert.equal(query.items[0].facts[0].value.methodName,'setCurrentPhase');
});
test('MOD return rejects forged compatibility, snapshot substitution, wrong owner, requested value and mixed boundaries',()=>{
  const registry=createDecisionAdapterRegistry([twilightForestTransitionAdapter]);
  for(const change of [r=>r.payload.returnTick=99,r=>r.payload.compatibilityStatus='VERSION_ONLY',
    r=>r.payload.descriptor={...r.payload.descriptor,classHashes:{...base.classHashes,'twilightforest.entity.boss.SnowQueen':'a'.repeat(64)}},
    r=>r.payload.schema='kneekura.mod-decision-snapshot/v1',r=>r.payload.eventIndex=257]) {
    const r=row();change(r);assert.equal(registry.captureBurst([r]),null);
  }
  for(const change of [r=>r.payload.data.methodOwner='twilightforest.entity.boss.Hydra',r=>r.payload.data.requestedValue='UNKNOWN',
    r=>r.payload.data.stateChangeStatus='AVAILABLE',r=>r.payload.data.reasonStatus='AVAILABLE',r=>r.payload.data.cachedState.phase='DROP']) {
    const r=row();change(r);assert.throws(()=>registry.captureBurst([r]),/TF_ORIGINAL_RETURN_CONTRACT/);
  }
  const a=row(),b=row();b.observationId+='other';b.arenaEpoch=1;
  assert.throws(()=>registry.captureBurst([a,b]),/CONTEXT/);
});
test('MOD packets bound recent callbacks and refuse repeated event indices under different observation IDs',()=>{
  const registry=createDecisionAdapterRegistry([twilightForestTransitionAdapter]);
  const rows=Array.from({length:10},(_,i)=>{
    const r=row();r.observationId+=':'+i;r.payload.eventIndex=i+1;return r;
  });
  const out=registry.captureBurst(rows);assert.equal(out.facts.length,8);assert.equal(out.retainedInputTruncated,true);
  assert.deepEqual(out.facts[0].source_observation_ids,[rows[2].observationId]);
  rows[1].payload.eventIndex=rows[0].payload.eventIndex;
  assert.throws(()=>registry.captureBurst(rows),/EVENT_DUPLICATED/);
});
test('world game time and last-completed local burst clock are independent retained identities',()=>{
  const registry=createDecisionAdapterRegistry([twilightForestTransitionAdapter]),r=row();
  r.gameTime=40100;r.payload.returnTick=40100;
  assert.equal(registry.captureBurst([r]).facts[0].value.tick,40100);
  r.payload.returnLocalTick=295;
  assert.equal(registry.captureBurst([r]),null);
});
