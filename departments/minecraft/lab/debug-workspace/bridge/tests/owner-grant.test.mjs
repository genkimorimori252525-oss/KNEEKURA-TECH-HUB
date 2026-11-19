import test from 'node:test';
import assert from 'node:assert/strict';
async function api(){return import('../owner-grant.mjs');}
function fixture(){
 const binding={schema_version:1,experiment_id:'exp',generation:1,request_hash:'a'.repeat(64),target:{profile_id:'b'.repeat(64),index_snapshot_id:'c'.repeat(64),build_artifact_hash:'d'.repeat(64),source_revision:'e'.repeat(40),dirty_hash:'f'.repeat(64),config_hash:'1'.repeat(64),resource_hash:'2'.repeat(64)},arena_id:'arena',arena_baseline_hash:'3'.repeat(64),assertions_hash:'4'.repeat(64)};
 return {binding,request:{experiment_id:'exp',generation:1,target:structuredClone(binding.target),arena:{arena_id:'arena',baseline_hash:'3'.repeat(64),bounds:{min:[0,64,0],max:[4,68,4]}},subjects:[{subject_id:'pig',uuid:'00000000-0000-0000-0000-000000000001',entity_type:'minecraft:pig'}],budgets:{time_budget_ms:1000,max_actions:2,max_captures:4},initial_state:[],actions:[{operation:'wait_ticks',action_id:'wait',ticks:1}]},identity:{debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,handshakeNonce:'nonce-0123456789abcdef',dimensionId:'minecraft:overworld',disposableWorldName:'KNEEKURA_DEBUG_WORLD'},selection:{grantId:'grant',leaseId:'lease',arenaEpoch:0,expectedArenaRevision:0,allowedActions:['wait_ticks']}};
}
test('owner grant is exact bounded intent and contains no false authority proof',async()=>{
 const {buildOwnerGrantIntent}=await api();const f=fixture();const r=buildOwnerGrantIntent(f);
 assert.equal(r.requestHash,f.binding.request_hash);assert.equal(r.maxCaptures,4);assert.equal(r.subjects[0].subjectId,'pig');
 assert.equal(Object.hasOwn(r,'runtimeAttestation'),false);assert.equal(Object.hasOwn(r,'authorized'),false);
});
test('owner grant denies requested expansion and unsupported actions',async()=>{
 const {buildOwnerGrantIntent}=await api();
 for(const change of ['extra','world','actions','volume','identity','subject','budget']){
  const f=fixture();
  if(change==='extra')f.selection.authorized=true;
  if(change==='world')f.identity.disposableWorldName='production';
  if(change==='actions')f.selection.allowedActions=['use_item'];
  if(change==='volume')f.request.arena.bounds.max=[64,128,64];
  if(change==='identity')f.request.experiment_id='other';
  if(change==='subject')f.request.subjects[0].entity_type='minecraft:player';
  if(change==='budget')f.request.budgets.time_budget_ms=120001;
  assert.throws(()=>buildOwnerGrantIntent(f),change);
 }
});

test('owner grant matches Java epoch nonce and resource boundaries',async()=>{
 const {buildOwnerGrantIntent}=await api();
 for(const change of ['epochZero','epochOverflow','shortNonce','dimensionDot','entityDot']){
  const f=fixture();
  if(change==='epochZero')f.identity.processEpoch=0;
  if(change==='epochOverflow')f.identity.processEpoch=2147483648;
  if(change==='shortNonce')f.identity.handshakeNonce='short';
  if(change==='dimensionDot')f.identity.dimensionId='minecraft:../world';
  if(change==='entityDot')f.request.subjects[0].entity_type='minecraft:./pig';
  assert.throws(()=>buildOwnerGrantIntent(f),change);
 }
});
