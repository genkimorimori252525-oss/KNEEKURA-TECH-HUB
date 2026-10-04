import test from 'node:test';
import assert from 'node:assert/strict';
import {traceAgeStyle} from './trace-age-style.mjs';
const style=(age,traceClass='MOB_ACTUAL',identity='00000000-0000-0000-0000-000000000001')=>traceAgeStyle({traceClass,identity,sampleTick:100,currentTick:100+age});
test('retained age uses three tick bands and expires without changing evidence',()=>{
 assert.equal(style(0).color,'rgb(105,215,255)');assert.equal(style(33).ageBand,'NEW');
 assert.equal(style(34).color,'rgb(255,211,83)');assert.equal(style(66).ageBand,'MIDDLE');
 assert.equal(style(67).color,'rgb(255,96,83)');assert.equal(style(99).ageBand,'OLD');
 assert.ok(style(99).alpha<style(67).alpha);assert.equal(style(100),null);assert.equal(style(-1),null);
});
test('projectile identity keeps its base color through redraw and warms toward red',()=>{
 const a=style(0,'PROJECTILE_ACTUAL'),b=style(0,'PROJECTILE_ACTUAL','00000000-0000-0000-0000-000000000002');
 assert.deepEqual(style(0,'PROJECTILE_ACTUAL'),a);assert.notEqual(a.color,b.color);
 assert.notEqual(style(34,'PROJECTILE_ACTUAL').color,a.color);assert.notEqual(style(67,'PROJECTILE_ACTUAL').color,a.color);
 assert.equal(style(67,'PROJECTILE_ACTUAL').ageBand,'OLD');assert.equal(style(100,'PROJECTILE_ACTUAL'),null);
});
test('style follows cursor and explicit lifetime; rejects invalid derived inputs',()=>{
 assert.equal(traceAgeStyle({traceClass:'MOB_ACTUAL',identity:'mob',sampleTick:1,currentTick:6,lifetimeTicks:10}).ageBand,'MIDDLE');
 for(const change of [{currentTick:NaN},{sampleTick:-1},{lifetimeTicks:0},{traceClass:'PATH'},{identity:''}])assert.throws(()=>traceAgeStyle({traceClass:'MOB_ACTUAL',identity:'mob',sampleTick:100,currentTick:105,...change}));
});
