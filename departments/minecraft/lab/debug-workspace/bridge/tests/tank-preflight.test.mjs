import test from 'node:test';
import assert from 'node:assert/strict';
import {buildTankPreflight,requireTankTimeBudget} from '../tank-preflight.mjs';

const fact=value=>({status:'SAMPLED_OBSERVED',value,sourceObservationIds:['obs:1'],observedTick:100,limitations:[]});
const status={schema:'kneekura.tank-status/v1',identity:{debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0},
  presentation:{requested:fact(true),registered:fact(true),eligible:fact(true),drawSubmitted:fact(true),brightness:fact(false),
    motion:fact(false),reason:'DRAW_SUBMITTED',freshness:{status:'CURRENT',ageMs:100}},channels:{SERVER_ENTITY_STATE:{status:'AVAILABLE'}},evidenceRefs:['obs:1']};
const profile={kind:'OBSERVE_GRID',grid:true,brightness:false,motion:false,decisionChannels:['SERVER_ENTITY_STATE']};
const timeBudget={experimentMs:30000,finalizationMs:5000,cleanupMs:5000,marginMs:5000};
const build=extra=>buildTankPreflight({status,profile,requiredChannels:['SERVER_ENTITY_STATE'],timeBudget,
  leaseCheck:{status:'SUFFICIENT',remainingMs:45000,requiredMs:45000},...extra});

test('preflight requires exact fresh draw, requested channels and the complete lease budget',()=>{
  const packet=build();assert.equal(packet.status,'READY');assert.equal(packet.leaseCheck.requiredMs,45000);
  assert.equal(packet.semantics.grantsAuthority,false);assert.equal(packet.semantics.requiresDispatchRecheck,true);
  assert.equal(build({leaseCheck:{status:'INSUFFICIENT',remainingMs:44999,requiredMs:45000}}).status,'NOT_READY');
  assert.equal(build({leaseCheck:{status:'SUFFICIENT',remainingMs:44999,requiredMs:45000}}).status,'NOT_READY');
  assert.equal(build({leaseCheck:{status:'SUFFICIENT',remainingMs:45000,requiredMs:1}}).status,'NOT_READY');
  assert.equal(build({leaseCheck:null}).status,'UNKNOWN');
});
test('historical remaining and historical rendering cannot make a stored run READY',()=>{
  const old=structuredClone(status);old.presentation.reportedRemainingMs= fact(120000);old.presentation.freshness.status='STORED';
  assert.equal(build({status:old,leaseCheck:null}).status,'UNKNOWN');
  for(const reason of ['EXPIRED','RECIPE_MISMATCH','SERVER_MISMATCH','DISCONNECTED']) {
    const invalid=structuredClone(status);invalid.presentation.reason=reason;
    assert.equal(build({status:invalid}).status,'NOT_READY');
  }
  const missing=structuredClone(status);missing.presentation.drawSubmitted={...fact(null),status:'NOT_CAPTURED'};
  assert.equal(build({status:missing}).status,'UNKNOWN');
  assert.equal(build({requiredChannels:['BRAIN_MEMORY']}).status,'UNKNOWN');
});
test('benchmark options are explicit; disabling grid does not bypass owner/lease checks',()=>{
  const benchmark={...profile,kind:'BENCHMARK',grid:false};
  const off=structuredClone(status);off.presentation.drawSubmitted=fact(false);off.presentation.eligible=fact(false);
  off.presentation.reason='UNREGISTERED';
  assert.equal(build({status:off,profile:benchmark}).status,'READY');
  assert.equal(build({status:off,profile:benchmark,leaseCheck:null}).status,'UNKNOWN');
  assert.throws(()=>build({profile:{kind:'BENCHMARK',grid:false}}),/PROFILE/);
  assert.throws(()=>build({profile:{...profile,grid:false}}),/PROFILE/);
});
test('declared motion OFF cannot pass with a running or unobserved motion overlay',()=>{
  const on=structuredClone(status);on.presentation.motion=fact(true);
  assert.equal(build({status:on}).status,'NOT_READY');
  const unknown=structuredClone(status);delete unknown.presentation.motion;
  assert.equal(build({status:unknown}).status,'UNKNOWN');
});
test('nonfinite, missing, fractional, negative and over-120s budgets are rejected',()=>{
  assert.equal(requireTankTimeBudget(timeBudget),45000);
  for(const value of [null,{}, {...timeBudget,experimentMs:Infinity},{...timeBudget,cleanupMs:-1},
    {...timeBudget,marginMs:0.5},{...timeBudget,experimentMs:120001}])assert.throws(()=>requireTankTimeBudget(value),/BUDGET/);
});
