import test from 'node:test';
import assert from 'node:assert/strict';
import { observeGenericMobFromSimStore } from '../generic-mob-decision-adapter.mjs';

function sample(t,x){
  return {tick:t,x,y:64,z:0,source_observation_id:'pos-'+t,source_kind:'SIMLAB_POS_RETAINED_POINT'};
}
function fakeStore(){
  const entities=new Map([[7,{id:7,uuid:'uuid-7',type:'example:custom_boss',role:'target'}]]);
  const points=[sample(5,0),sample(10,2)];
  return {
    entities,
    trackOf(id){ assert.equal(id,7); return {
      t0:5,t1:10,
      samples(a,b){ return points.filter(p=>p.tick>=a&&p.tick<=b); },
      sampleAtOrBefore(t){ return [...points].reverse().find(p=>p.tick<=t)||null; },
    }; },
    stateAt(ch,id,t){ assert.equal(ch,'pos'); assert.equal(id,7); const p=[...points].reverse().find(p=>p.tick<=t); return p?{...p,t}:null; },
  };
}

test('generic adapter observes one exact subject without fabricating Vanilla semantics',()=>{
  const observation=observeGenericMobFromSimStore({store:fakeStore(),entityId:7,tick:10,identity:{run_id:'r1'}});
  assert.equal(observation.subject.id,'uuid-7');
  assert.equal(observation.capabilities.position.status,'AVAILABLE');
  assert.equal(observation.capabilities.vanilla_goal.status,'NOT_EXPOSED');
  assert.equal(observation.capabilities.vanilla_pathfinding.status,'NOT_EXPOSED');
  assert.equal(observation.capabilities.custom_decision.status,'NOT_EXPOSED');
  assert.equal(observation.stages.STATE.facts[0].epistemic_status,'SAMPLED_OBSERVED');
  assert.deepEqual(observation.available_drilldowns,['motion_trace']);
});

test('forward-filled selected state is labelled derived, not sampled',()=>{
  const observation=observeGenericMobFromSimStore({store:fakeStore(),entityId:7,tick:12});
  const fact=observation.stages.STATE.facts[0];
  assert.equal(fact.epistemic_status,'DERIVED_FROM_OBSERVED');
  assert.match(fact.note,/forward-filled/);
  assert.deepEqual(fact.source_observation_ids,['pos-10']);
});

test('missing retained state remains NOT_CAPTURED instead of invented',()=>{
  const store={entities:new Map([[9,{id:9,type:'minecraft:zombie'}]]),trackOf(){return null;},stateAt(){return null;}};
  const observation=observeGenericMobFromSimStore({store,entityId:9,tick:1});
  assert.equal(observation.capabilities.position.status,'NOT_CAPTURED');
  assert.equal(observation.stages.STATE,undefined);
  assert.equal(observation.capabilities.vanilla_goal.status,'NOT_EXPOSED');
});

test('gone entity does not regain a forward-filled current position',()=>{
  const point=sample(5,1);
  const store={
    entities:new Map([[7,{id:7,uuid:'uuid-7',type:'minecraft:zombie',goneAt:6}]]),
    trackOf(){return {t0:5,t1:5,samples(){return [point];},sampleAtOrBefore(){return point;}};},
    isAlive(){return false;},
    stateAt(){return point;},
  };
  const observation=observeGenericMobFromSimStore({store,entityId:7,tick:8});
  assert.equal(observation.capabilities.position.status,'NOT_APPLICABLE');
  assert.equal(observation.stages.STATE,undefined);
  assert.match(observation.capabilities.position.detail,/explicitly gone/);
});
