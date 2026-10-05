import test from 'node:test';
import assert from 'node:assert/strict';
import {buildExperimentDigest} from '../experiment-digest.mjs';
import {sha256,stableJson} from '../../bridge/json.mjs';
export const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1,subjectUuid:'00000000-0000-0000-0000-000000000001'};
export const request={experiment_id:'experiment',question:'observed motion?',subjects:[{subject_id:'A',uuid:identity.subjectUuid,entity_type:'minecraft:zombie'}],target:{source_revision:'a'},arena:{baseline_hash:'b',bounds:{min:[0,0,0],max:[64,64,64]}},assertions:[{assertion_id:'registered'}],actions:[]};
export const row=(tick,x=tick/10)=>({kind:'observation',...identity,observationId:'obs:'+tick,gameTime:tick,lane:'SERVER_ENTITY_STATE',source:{side:'SERVER'},scope:{kind:'ENTITY_UUID',entityUuid:identity.subjectUuid},epistemicStatus:'OBSERVED',completeness:{complete:true},payload:{targetRevision:1,x,y:64,z:0,dimension:'minecraft:overworld'}});
export const build=extra=>buildExperimentDigest({request,identity,window:{startTick:0,endTick:300},observations:Array.from({length:301},(_,i)=>row(i)),actionReceipts:[],...extra});
test('metrics use all canonical samples beyond display/cursor/bookmark limits',()=>{
  const a=build(),b=build({limits:{displayPoints:1,bookmarks:1,cursors:1}});
  assert.deepEqual(a.metrics,b.metrics);assert.equal(a.metrics.positionSamples.value,301);assert(Math.abs(a.metrics.observedDistance.value-30)<1e-8);
  assert.equal(a.quality.coverage.eligibleCount,301);assert.equal(a.registeredAssertions[0].status,'INCONCLUSIVE');
  assert.throws(()=>build({observations:Array(50001).fill(row(0))}),/LIMIT/);
});
test('gaps, partial samples, dimension and terminal boundaries never contribute connecting distance',()=>{
  const observations=[row(0,0),row(1,1),{...row(2,2),completeness:{complete:false}},row(3,3),row(30,4),{...row(31,5),payload:{...row(31,5).payload,dimension:'other'}},row(32,6)];
  const a=build({observations});assert.equal(a.metrics.observedDistance.value,1);assert(a.quality.coverage.gapCount>=4);
  assert.equal(a.quality.coverage.endCaptured,false);assert.equal(a.quality.status,'INCONCLUSIVE');
  const stop=build({observations:[row(0,0),row(1,0),row(30,0)]});assert.equal(stop.metrics.sameCoordinateIntervals.value.totalObservedTicks,1);
});
test('accepted is never promoted and foreign identity/duplicate IDs fail closed',()=>{
  const a=build({actionReceipts:[{action_id:'a',status:'ACCEPTED'}]});assert.equal(a.actions[0].status,'ACCEPTED');assert.equal(a.executionEffect,'NOT_ESTABLISHED');
  assert.throws(()=>build({observations:[row(0),row(0)]}),/DUPLICATE/);
  assert.throws(()=>build({observations:[{...row(0),runId:'other'}]}),/IDENTITY/);
  assert.throws(()=>build({identity:{...identity,subjectUuid:'other'}}),/SUBJECT/);
});

test('alignment requires exact APPLIED export bytes and the original canonical effect tick',()=>{
  const action={action_id:'start',operation:'wait_ticks',ticks:1},req={...request,initial_state:[],actions:[action]};
  const effect={...row(10),observationId:'effect:start',lane:'ACTION_APPLIED',payload:{actionId:'start',postconditionMatched:true}};
  const effectBytes=Buffer.from(stableJson(effect)),effectHash=sha256(effectBytes);
  const receiptBytes=Buffer.from(stableJson({kind:'lab_action_receipt_export',identity,actionId:'start',reportedStatus:'APPLIED',effectEvidence:[{contentHash:effectHash,observationId:effect.observationId}]}));
  const receiptHash=sha256(receiptBytes),input={request:req,window:{startTick:10,endTick:11},observations:[effect,row(10),row(11)],
    actionReceipts:[{action_id:'start',status:'APPLIED',evidence_hash:receiptHash}],limits:{alignment:{actionReceiptHash:receiptHash,anchorTick:10},
      receiptBlobs:[{contentHash:receiptHash,bytes:receiptBytes},{contentHash:effectHash,bytes:effectBytes}]}};
  const a=build(input);assert.equal(a.alignmentEvidence.status,'VERIFIED_RETAINED_ACTION_EFFECT');assert.equal(a.conditions.alignment.windowStartOffset,0);
  const b=build({...input,window:{startTick:100,endTick:101}});assert.equal(b.conditions.alignment.windowStartOffset,90);
  assert.equal(build({...input,limits:{...input.limits,alignment:{actionReceiptHash:receiptHash,anchorTick:0}}}).conditions.alignment,null);
  assert.equal(build({...input,actionReceipts:[]}).conditions.alignment,null);
  assert.equal(a.conditionEvidence.world,'UNVERIFIED');assert.equal(a.conditionEvidence.observer,'UNVERIFIED');
});

test('more than32 retained hit callbacks are counted independently from selected bookmarks',()=>{
  const events=Array.from({length:40},(_,i)=>({...row(i),observationId:'hit:'+i,lane:'AI_DECISION',payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',kind:'CONTROL_PROJECTILE_HIT_RETURN',targetRevision:1,burstId:'burst:1:0',eventIndex:i+2,
    observerCostNanos:10,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER',data:{ownerUuid:identity.subjectUuid,projectileUuid:'00000000-0000-0000-0000-000000000002',projectileClass:'Arrow',spawnEventIndex:1,relationshipScope:'ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER',hitType:'BLOCK',hitPosition:{x:0,y:64,z:0},dispatchScope:'BASE_PROJECTILE_ON_HIT_RETURN',damageOutcomeStatus:'NOT_EXPOSED'}}}));
  const input={observations:[...Array.from({length:301},(_,i)=>row(i)),...events]};
  const a=build(input),b=build({...input,limits:{displayPoints:1,bookmarks:1,cursors:1}});
  assert.equal(a.metrics.retainedEventCounts.CONTROL_PROJECTILE_HIT_RETURN.value,40);assert.deepEqual(a.metrics,b.metrics);
  assert.equal(a.metrics.attackCount.status,'NOT_EXPOSED');
});

test('known zero health plus sealed canonical source establish only the declared sampling grid',()=>{
  const limits={observer:{sampleIntervalTicks:1},sourceBinding:{verifiedCanonical:true},health:{dropped:0,errors:0,trailingPartialFiles:0,partialCaptures:0}};
  const a=build({limits});assert.equal(a.quality.status,'SAMPLING_GRID_COMPLETE');assert.equal(a.quality.coverage.allEventsCaptured,'NOT_ESTABLISHED');
  assert.equal(build({limits:{...limits,health:{...limits.health,dropped:1}}}).quality.status,'INCONCLUSIVE');
  assert.equal(build({limits,observations:Array.from({length:300},(_,i)=>row(i+1))}).quality.status,'INCONCLUSIVE');
});

test('arrival cites an interval between original observations and never an exact invented arrival tick',()=>{
  const result=build({request:{...request,assertions:[{assertion_id:'arrival',kind:'structured',subject_id:'A',field:'position',operator:'equals',expected:[3,64,0]}]},observations:[row(0,0),row(30,3)]});
  assert.deepEqual(result.metrics.arrival.value[0].observedInterval,{afterTick:0,atOrBeforeTick:30});
  assert.equal(result.registeredAssertions[0].status,'INCONCLUSIVE');assert.equal(result.quality.status,'INCONCLUSIVE');
});
