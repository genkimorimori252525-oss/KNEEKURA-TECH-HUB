import test from 'node:test';
import assert from 'node:assert/strict';
import {validateScenario,validateExpect,tickSegments,judge} from './scenario.mjs';

const steps=[{at:0,try:'difficulty normal'},{at:0,run:'time set day'},{at:20,run:'execute at @p run summon minecraft:husk ^ ^ ^6'},{at:40,mark:'crowd'},{at:60,screenshot:'crowd'},{at:90,check:'execute if entity @e[type=minecraft:husk]'}];
test('scenario steps are exact, ordered, bounded and named',()=>{
 assert.equal(validateScenario(steps,600).length,6);
 for(const bad of [[],[{at:0}],[{at:0,run:'a',check:'b'}],[{at:0,run:'a',extra:1}],[{at:5,run:'a'},{at:4,run:'b'}],[{at:600,run:'a'}],[{at:0,run:'a\nb'}],[{at:0,mark:'Bad Name'}],[{at:0,mark:'baseline'}],[{at:0,mark:'m'},{at:1,mark:'m'}]])
  assert.throws(()=>validateScenario(bad,600));
});
test('expectations are exact and only reference existing marks and enabled observers',()=>{
 const ok=[{entity:'minecraft:husk',target:'minecraft:player',by:100},{entity:'minecraft:husk',goal:'ZombieAttackGoal',between:[20,200]},{entity:'mymod:boss',state:{phase:'ENRAGED'},after:100},{entity:'minecraft:husk',gone:'ANY',by:500},{seen:'minecraft:arrow'},{tickMs:{segment:'crowd',p95:50}},{tickMs:{segment:'baseline',mean:20,tankExcluded:false}}];
 assert.equal(validateExpect(ok,steps,600).length,7);
 for(const bad of [[{tickMs:{segment:'missing',p95:5}}],[{tickMs:{segment:'crowd'}}],[{entity:'husk',target:'minecraft:player',by:1}],[{entity:'a:b',goal:'G',between:[5,1]}],[{entity:'a:b',gone:'DEAD',by:1}],[{entity:'a:b',target:'c:d',by:1,x:1}]])
  assert.throws(()=>validateExpect(bad,steps,600));
 assert.throws(()=>validateExpect([{entity:'a:b',target:'c:d',by:1}],steps,600,{ai:false}),/NEEDS_AI/);
 assert.throws(()=>validateExpect([{seen:'a:b'}],undefined,600),/NEEDS_SCENARIO/);
});
const result={ticks:8,startGameTime:1000,tickMicros:[10000,10000,10000,10000,40000,40000,40000,60000],tankToolMicros:[1000,1000,1000,1000,1000,1000,1000,1000],
 steps:[{at:0,run:'time set day',tick:0,status:'PASS'},{at:4,mark:'crowd',tick:4,status:'MARKED',loadedEntities:30,mobsNear:21},{at:6,screenshot:'crowd',tick:6,status:'TAKEN',file:'x.png'},{at:7,check:'execute if entity @e',tick:7,status:'PASS'}]};
test('tick segments split at marks and report Tank tool cost separately',()=>{
 const s=tickSegments(result);assert.deepEqual([s.baseline.from,s.baseline.to,s.baseline.n],[0,4,4]);assert.equal(s.baseline.ms.mean,10);assert.equal(s.baseline.tankExcludedMs.mean,9);
 assert.equal(s.crowd.n,4);assert.equal(s.crowd.ms.max,60);assert.equal(s.crowd.ms.p95,60);assert.equal(s.crowd.mobsNear,21);assert.equal(s.crowd.tankToolMeanMs,1);
});
test('judge uses change-only AI intervals, gone records, load budgets and failed steps',()=>{
 const ai=[{tick:1001,event:'CHANGE',uuid:'u',type:'minecraft:husk',goals:['2:ZombieAttackGoal'],targetGoals:[],target:{type:'minecraft:player'}},
  {tick:1005,event:'CHANGE',uuid:'u',type:'minecraft:husk',goals:[],targetGoals:[],state:{phase:'IDLE'},why:{phase:'-> ENRAGED'}},{tick:1007,event:'GONE',uuid:'u',type:'minecraft:husk',why:'REMOVED'}];
 const expect=[{entity:'minecraft:husk',target:'minecraft:player',by:2},{entity:'minecraft:husk',goal:'ZombieAttackGoal',between:[3,4]},{entity:'minecraft:husk',state:{phase:'-> ENRAGED'},after:5},{entity:'minecraft:husk',gone:'REMOVED',by:7},{seen:'minecraft:arrow'},{tickMs:{segment:'baseline',p95:15}}];
 let v=judge({expect,result,aiLines:ai,seenTypes:['minecraft:arrow']});assert.equal(v.status,'PASS',JSON.stringify(v.rows.filter(r=>r.status!=='PASS')));
 assert.equal(v.screenshots[0].file,'x.png');
 v=judge({expect:[{entity:'minecraft:husk',goal:'ZombieAttackGoal',between:[5,7]},{tickMs:{segment:'crowd',p95:50}},{entity:'minecraft:husk',target:'minecraft:player',by:0}],result,aiLines:ai});
 assert.equal(v.status,'FAIL');assert.equal(v.failed,2);assert.deepEqual(v.rows.find(r=>r.expect?.tickMs).evidence.over,['p95']);
 v=judge({expect:[],result:{...result,steps:[...result.steps,{at:0,try:'difficulty normal',tick:0,status:'FAIL'},{at:9,try:'late',status:'NOT_REACHED'},{at:7,run:'bogus',tick:7,status:'FAIL',messages:['Unknown command']},{at:9,run:'later',status:'NOT_REACHED'}]}});
 assert.equal(v.status,'FAIL');assert.equal(v.failed,2);
});
