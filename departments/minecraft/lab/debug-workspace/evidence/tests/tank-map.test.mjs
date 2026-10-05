import test from 'node:test';
import assert from 'node:assert/strict';
import {buildTankMap} from '../tank-map.mjs';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0};
const status={schema:'kneekura.tank-status/v1',identity,geometry:{status:'SAMPLED_OBSERVED',value:{x:0,y:64,z:0,width:16,height:8,depth:16},sourceObservationIds:['obs:g']}};
test('Tank map uses fixed block scale and north-negative-Z without fitting to subjects',()=>{
  const a=buildTankMap({status,positions:[{tick:100,x:1,y:64,z:1,source_observation_id:'obs:1'}]}),
    b=buildTankMap({status,positions:[{tick:100,x:1000,y:64,z:1000,source_observation_id:'obs:1'}]});
  assert.deepEqual(a.bounds,b.bounds);assert.equal(a.axes.north,'-Z');assert.equal(a.viewport.pixelsPerBlock,12);
  assert.equal(b.layers.motion.points[0].x,1000);assert.equal(b.layers.motion.points[0].outsideTank,true);
  assert.deepEqual(a.layers.walls,[]);assert.equal(a.layers.motion.segments.length,0);
});
test('missing geometry stays unavailable and oversized/invalid coordinates are rejected',()=>{
  assert.equal(buildTankMap({status:{...status,geometry:{status:'NOT_CAPTURED',value:null}},positions:[]}).status,'NOT_CAPTURED');
  assert.throws(()=>buildTankMap({status,positions:[{x:Infinity,y:64,z:0}]}),/POSITION/);
  assert.throws(()=>buildTankMap({status,positions:Array(129).fill({x:1,y:64,z:1})}),/LIMIT/);
});
