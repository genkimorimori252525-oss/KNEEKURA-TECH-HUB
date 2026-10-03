import test from 'node:test';
import assert from 'node:assert/strict';
import {decisionBurstFromArgs} from '../../decision-burst-cli.mjs';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
import {queryDecisionDrilldown} from '../decision-drilldown.mjs';
const uuid='00000000-0000-0000-0000-000000000001';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:2,targetRevision:1};
function row(){return {kind:'observation',lane:'AI_DECISION',...identity,epistemicStatus:'OBSERVED',completeness:{complete:true},
 source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:uuid},observationId:'obs:effective-malus:1',gameTime:100,
 payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:1,
  eventIndex:1,burstId:'burst:1:90',kind:'EFFECTIVE_MALUS_RETURN',observerCostNanos:1,
  observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{receiverUuid:uuid,
    receiverClass:'example.CustomMob',evaluatorClass:'net.minecraft.world.level.pathfinder.WalkNodeEvaluator',
    pathType:'WATER',returnedMalus:17.25,dispatchScope:'ORIGINAL_EVALUATOR_VIRTUAL_MOB_MALUS_RETURN',
    callSiteScope:'KNOWN_BASE_EVALUATOR_CLASS_SET_NOT_EXACT_METHOD',effectivePathCostStatus:'NOT_EXPOSED',underlyingSourceStatus:'NOT_EXPOSED'}}};}
test('effective getter return is separately opt-in and retains custom value without claiming final path cost or its reason',()=>{
  assert.equal(decisionBurstFromArgs(['--decision-burst']).channels.includes('effective_malus'),false);
  assert.deepEqual(decisionBurstFromArgs(['--decision-burst','--decision-channels','effective_malus']).channels,['effective_malus']);
  const r=row(),before=JSON.stringify(r);assert.equal(validOriginalDecisionEvent(r),true);
  const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents([r],stages,capabilities,timeline);
  assert.equal(stages.EVALUATION.facts[0].value.returnedMalus,17.25);
  assert.equal(capabilities.effective_malus.status,'PARTIAL');assert.equal(stages.SELECTION,undefined);
  const out=queryDecisionDrilldown({observations:[r],subjectUuid:uuid,identity,
    request:{channel:'effective_malus',startTick:90,endTick:110,limit:1,maxNodes:1}});
  assert.equal(out.items[0].data.receiverClass,'example.CustomMob');assert.equal(out.items[0].data.effectivePathCostStatus,'NOT_EXPOSED');
  assert.equal(JSON.stringify(r),before);
});
test('non-finite getter return is unknown in JSON; forged receiver, total cost or underlying formula is rejected',()=>{
  const r=row();delete r.payload.data.returnedMalus;r.payload.data.returnedMalusStatus='NOT_EXPOSED';
  assert.equal(validOriginalDecisionEvent(r),true);
  for(const mutate of [d=>d.receiverUuid='00000000-0000-0000-0000-000000000002',d=>d.returnedMalus=NaN,
    d=>d.effectivePathCostStatus='AVAILABLE',d=>d.underlyingSourceStatus='AVAILABLE',d=>d.dispatchScope='BASE_METHOD_RETURN',
    d=>d.finalPathCost=17.25,d=>d.returnedMalusStatus='AVAILABLE']){
    const bad=row();mutate(bad.payload.data);assert.equal(validOriginalDecisionEvent(bad),false);
  }
});
