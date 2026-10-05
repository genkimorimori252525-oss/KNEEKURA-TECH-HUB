import test from 'node:test';
import assert from 'node:assert/strict';
import {buildTankStatus} from '../tank-status.mjs';

const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0};
const hash='a'.repeat(64);
const geometry={x:0,y:64,z:0,width:16,height:8,depth:16};
const clock={domain:'JVM_PROCESS_MONOTONIC',processId:12,processStartedAt:'start',monotonicOriginWallClock:'origin',monotonicElapsedNanos:1e9};
const row={kind:'observation',...identity,lane:'TANK_PRESENTATION_STATUS',observationId:'obs:1',gameTime:100,
  writerSeq:1,scope:{kind:'GLOBAL_HEALTH'},source:{side:'CLIENT'},epistemicStatus:'OBSERVED',completeness:{complete:true},clock,
  payload:{schema:'kneekura.tank-presentation-status/v1',recipeHash:hash,geometry,requested:true,registered:true,
    eligible:true,drawSubmitted:true,brightness:true,reason:'DRAW_SUBMITTED',reportedRemainingMs:60000,statusSuppressedTotal:0}};
const expected={recipeHash:hash,currentClock:{...clock,monotonicElapsedNanos:1.1e9},maxAgeMs:2000};
const build=(extra={})=>buildTankStatus({observations:[row],identity,expected,...extra});

test('submission is a sampled fact, not visible pixels or a lease authority',()=>{
  const status=build();
  assert.equal(status.presentation.drawSubmitted.value,true);
  assert.equal(status.presentation.pixelEvidence.status,'NOT_CAPTURED');
  assert.equal(status.presentation.freshness.status,'CURRENT');
  assert.deepEqual(status.presentation.drawSubmitted.sourceObservationIds,['obs:1']);
  assert.equal(status.presentation.drawSubmitted.observedTick,100);
  assert.equal(status.semantics.grantsAuthority,false);
  assert.equal(status.presentation.reportedRemainingMs.value,60000);
  assert.deepEqual(status.geometry.value,geometry);
});
test('source, fixture and unknown provenance are never conflated',()=>{
  const binding={authorityHash:hash,copyBaselineHash:hash,fixtureHash:'b'.repeat(64),fixtureChanges:['wall changed']};
  const status=build({worldBinding:binding});
  assert.equal(status.worldBinding.fixtureHash,'b'.repeat(64));
  assert.equal(status.worldBinding.provenanceStatus,'UNKNOWN');
  assert.equal(build().worldBinding.authorityHash,null);
  assert.equal(build({observations:[]}).presentation.drawSubmitted.value,null);
  assert.equal(build({observations:[]}).presentation.drawSubmitted.status,'NOT_CAPTURED');
});
test('foreign run/Arena and malformed or duplicate evidence fail closed',()=>{
  for(const key of ['runId','arenaEpoch']) {
    assert.throws(()=>build({observations:[{...row,[key]:key==='runId'?'foreign':1}]}),/IDENTITY/);
  }
  assert.throws(()=>build({identity:{runId:'r'}}),/IDENTITY/);
  assert.throws(()=>build({observations:[row,row]}),/DUPLICATE/);
  assert.throws(()=>build({observations:[{...row,payload:{...row.payload,drawSubmitted:'true'}}]}),/STATUS/);
});
test('stored evidence, another clock, expired and mismatched recipes do not become current ON',()=>{
  assert.equal(build({expected:{recipeHash:hash}}).presentation.freshness.status,'STORED');
  assert.equal(build({expected:{...expected,currentClock:{...clock,processId:13}}}).presentation.freshness.status,'UNKNOWN');
  assert.equal(build({expected:{...expected,currentClock:{...clock,monotonicElapsedNanos:9e9}}}).presentation.freshness.status,'STALE');
  assert.equal(build({expected:{...expected,recipeHash:'b'.repeat(64)}}).presentation.reason,'RECIPE_MISMATCH');
  const expired={...row,payload:{...row.payload,eligible:false,drawSubmitted:false,reason:'EXPIRED',reportedRemainingMs:0}};
  assert.equal(build({observations:[expired]}).presentation.reason,'EXPIRED');
  assert.equal(build({observations:[row, {...expired,observationId:'obs:2',writerSeq:2,gameTime:101}]}).presentation.eligible.value,false);
});

test('production Gson omitted optional metadata at startup does not reject later valid status',()=>{
  const startup={...row,observationId:'obs:startup',writerSeq:1,payload:{schema:'kneekura.tank-presentation-status/v1',
    requested:false,registered:false,eligible:false,drawSubmitted:false,brightness:false,reason:'UNREGISTERED',motionEnabled:false,statusSuppressedTotal:0}};
  const missing=build({observations:[startup]});assert.equal(missing.geometry.value,null);assert.equal(missing.geometry.status,'NOT_CAPTURED');
  assert.equal(missing.presentation.recipeHash.status,'NOT_CAPTURED');assert.equal(missing.presentation.reportedRemainingMs.status,'NOT_CAPTURED');
  const drawn={...row,observationId:'obs:drawn',writerSeq:2};assert.equal(build({observations:[startup,drawn]}).presentation.drawSubmitted.value,true);
  assert.throws(()=>build({observations:[{...startup,payload:{...startup.payload,registered:true}}]}),/STATUS/);
});
