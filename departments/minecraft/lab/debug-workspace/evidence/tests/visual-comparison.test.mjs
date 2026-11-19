import test from 'node:test';
import assert from 'node:assert/strict';
import { decodePng } from '../../../simlab/golden/png.mjs';
import { fixture,request,HASH,UUID } from './visual-fixture.mjs';
import * as comparison from '../visual-comparison.mjs';
const difference=(field,before,after)=>({field,before,after});
test('matched source/build/generation changes preserve independent absolute runs and outcomes',async t=>{
 const a=request(),b=request();b.generation=2;b.target.source_revision='b'.repeat(40);b.target.build_artifact_hash='b'.repeat(64);

 const before=await fixture(t,{request:a,run:'before',tick:30});
 const after=await fixture(t,{request:b,run:'after',tick:800,mutate:m=>{m.structuredState.subjects[0].position[0]=2;}});
 const c=await comparison.compareVisualRuns({before,after,intendedDifferences:[difference('generation',1,2),difference('target.source_revision',a.target.source_revision,b.target.source_revision),difference('target.build_artifact_hash',HASH,b.target.build_artifact_hash)]});
 assert.equal(c.comparison.status,'MATCHED_EVIDENCE_ONLY');assert.equal(c.comparison.acceptance,'NOT_EVALUATED');
 assert.equal(c.comparison.before.stateWindow.serverTickStart,30);assert.equal(c.comparison.after.stateWindow.serverTickStart,800);
 assert.equal(c.comparison.outcomes.before.behaviorVerdict,'INCONCLUSIVE_CAPTURE_PERTURBATION');
 assert.equal(c.comparison.structuredDifferences[0].subjectId,'subject');assert.deepEqual(c.comparison.structuredDifferences[0].after.position,[2,1,2]);
 assert.equal(c.comparison.viewPairs.length,4);assert.deepEqual(c.comparison.viewPairs.map(v=>v.view),['north','east','south','west']);
 const image=decodePng(c.artifacts.find(a=>a.ref.artifactId===c.comparison.sideBySide.artifactId).bytes);
 assert.deepEqual([image.width,image.height],[128,328]);
 assert.equal(c.comparison.pixelDifferenceMeansImprovement,false);
});
test('registered subject UUIDs and request action identities cannot be silently normalized',async t=>{
 for(const kind of ['uuid','action','experiment']) {
  const a=request(),b=request(),other='00000000-0000-0000-0000-000000000002';
  if(kind==='uuid')b.subjects[0].uuid=other;
  if(kind==='action')b.actions[0].action_id='new-action';
  if(kind==='experiment')b.experiment_id='new-experiment';
  b.generation=2;
  const before=await fixture(t,{request:a});const after=await fixture(t,{request:b,run:'other',mutate:m=>{
   if(kind==='uuid'){m.subjects=[other];m.frames.forEach(f=>f.subjects=[other]);m.structuredState.subjects[0].uuid=other;}
  }});
  const c=await comparison.compareVisualRuns({before,after,intendedDifferences:[difference('generation',1,2)]});
  assert.equal(c.comparison.status,'NON_COMPARABLE');
 }
});
test('all seven exact intended TECH target changes are supported with a newer generation',async t=>{
 const a=request(),b=request();b.generation=2;
 const intendedDifferences=[difference('generation',1,2)];
 for(const field of Object.keys(b.target)){b.target[field]='b'.repeat(field==='source_revision'?40:64);intendedDifferences.push(difference('target.'+field,a.target[field],b.target[field]));}
 const before=await fixture(t,{request:a});const after=await fixture(t,{request:b,run:'after'});
 const c=await comparison.compareVisualRuns({before,after,intendedDifferences});assert.equal(c.comparison.status,'MATCHED_EVIDENCE_ONLY');
});
test('changed request bytes require increasing generation even with exact intended target declarations',async t=>{
 for(const generation of [1,2]) {
  const a=request(),b=request();a.generation=2;b.generation=generation;b.target.build_artifact_hash='b'.repeat(64);
  const before=await fixture(t,{request:a});const after=await fixture(t,{request:b,run:'after'});
  const intendedDifferences=[difference('target.build_artifact_hash',HASH,b.target.build_artifact_hash)];
  if(generation!==2)intendedDifferences.push(difference('generation',2,generation));
  const c=await comparison.compareVisualRuns({before,after,intendedDifferences});
  assert.equal(c.comparison.status,'NON_COMPARABLE');assert.ok(c.comparison.reasons.includes('GENERATION_LINEAGE'));
 }
});
for(const kind of ['baseline','actions','initial_state','assertions','subject_type','camera','projection','viewport','partial_tick','control','restoration','config','generation','unintended_build']) {
 test(`comparison fails closed on unmatched ${kind}`,async t=>{
  const a=request(),b=request();
  if(kind==='actions')b.actions[0].ticks=6;
  if(kind==='initial_state')b.initial_state=[{action_id:'init',operation:'wait_ticks',ticks:1}];
  if(kind==='assertions')b.assertions[0].expected=19;
  if(kind==='subject_type')b.subjects[0].entity_type='minecraft:cow';
  if(kind==='config')b.target.config_hash='b'.repeat(64);
  if(kind==='generation')b.generation=2;
  if(kind==='unintended_build')b.target.build_artifact_hash='b'.repeat(64);
  const before=await fixture(t,{request:a});const after=await fixture(t,{request:b,run:'after',mutate:m=>{
   if(kind==='baseline')m.identity.baselineHash='b'.repeat(64);
   if(kind==='camera')m.frames[0].camera.position[0]++;
   if(kind==='projection')m.frames[0].camera.projectionMatrix[0]=2;
   if(kind==='viewport')m.frames[0].camera.viewport=[65,64];
   if(kind==='partial_tick')m.frames[0].partialTick=.5;
   if(kind==='control')m.result.perturbations.pop();
   if(kind==='restoration'){m.result.restoration='UNKNOWN';m.result.status='UNKNOWN';}
  }});
  const c=await comparison.compareVisualRuns({before,after});
  assert.equal(c.comparison.status,'NON_COMPARABLE');assert.ok(c.comparison.reasons.length);assert.equal(c.artifacts.length,0);
 });
}
test('unknown, stale, or broadened intended-difference allowances are refused',async t=>{
 const before=await fixture(t);const b=request();b.target.build_artifact_hash='b'.repeat(64);const after=await fixture(t,{request:b,run:'after'});
 for(const entry of [difference('target.config_hash',HASH,HASH),difference('target.build_artifact_hash','c'.repeat(64),b.target.build_artifact_hash),difference('actions',[],[])])
   await assert.rejects(comparison.compareVisualRuns({before,after,intendedDifferences:[entry]}),/INTENDED/);
});
test('mismatched exact request bytes and request/capture subject coverage cannot be compared',async t=>{
 const before=await fixture(t);const after=await fixture(t,{run:'after'});after.requestBytes=Buffer.from(after.requestBytes.toString()+' ');
 const c=await comparison.compareVisualRuns({before,after});assert.equal(c.comparison.status,'NON_COMPARABLE');assert.match(c.comparison.reasons.join(','),/REQUEST_HASH/);
 const b=request();b.subjects.push({subject_id:'missing',uuid:'00000000-0000-0000-0000-000000000002',entity_type:'minecraft:cow'});
 const extra=await fixture(t,{request:b,run:'extra'});const d=await comparison.compareVisualRuns({before,after:extra});
 assert.equal(d.comparison.status,'NON_COMPARABLE');assert.match(d.comparison.reasons.join(','),/SUBJECT/);
});
for(const kind of ['assertion_schema','assertion_subject','scope_schema','scope_lane'])test(`comparison rejects malformed TECH ${kind}`,async t=>{
 const req=request();
 if(kind==='assertion_schema')req.assertions=[{madeUp:'not-a-contract-assertion'}];
 if(kind==='assertion_subject')req.assertions[0].subject_id='unknown';
 if(kind==='scope_schema')req.observation_scopes=[{arbitrary:'not-a-contract-scope'}];
 if(kind==='scope_lane')req.observation_scopes[0].lanes=['ARBITRARY'];
 const before=await fixture(t,{request:req});const after=await fixture(t,{request:req,run:'after'});
 const c=await comparison.compareVisualRuns({before,after});
 assert.equal(c.comparison.status,'NON_COMPARABLE');assert.ok(c.comparison.reasons.length);
});
