import test from 'node:test';
import assert from 'node:assert/strict';
import { request } from '../../evidence/tests/visual-fixture.mjs';
import { sha256,stableJson } from '../json.mjs';
async function api(){return import('../selected-action.mjs');}
function fixture(){
 const r=request();r.budgets.max_actions=3;r.actions=[{action_id:'block',operation:'set_block',position:[0,1,0],block:'minecraft:stone'},{action_id:'wait',operation:'wait_ticks',ticks:1},{action_id:'move',operation:'teleport_subject',subject_id:'subject',position:[1,2,1],rotation:[0,0]}];
 const g={schemaVersion:1,debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1,experimentId:r.experiment_id,generation:r.generation,requestHash:sha256(stableJson(r)),arenaId:r.arena.arena_id,arenaEpoch:0,expectedArenaRevision:4,baselineHash:r.arena.baseline_hash,allowedActions:['set_block','wait_ticks','teleport_subject']};
 return {request:r,grant:g};
}
test('selected retained action has fixed replay identity and derived revision',async()=>{
 const {selectRetainedAction}=await api();const f=fixture();const a=selectRetainedAction({...f,selectedActionId:'move'});
 assert.deepEqual(a.priorActionIds,['block','wait']);assert.equal(a.action.expectedArenaRevision,5);
 assert.deepEqual(a.action.args,{subject_id:'subject',position:[1,2,1],rotation:[0,0]});
 assert.equal(a.action.idempotencyKey,sha256(stableJson({actionId:'move',processEpoch:1,requestHash:f.grant.requestHash,runId:'run',runSnapshotId:'snapshot'})));
 assert.deepEqual(selectRetainedAction({...f,selectedActionId:'move'}),a);
});
test('unknown action and foreign grant identity reject before queue publication',async()=>{
 const {selectRetainedAction}=await api();const f=fixture();
 assert.throws(()=>selectRetainedAction({...f,selectedActionId:'unregistered'}));
 for(const field of ['experimentId','generation','arenaId','baselineHash']){
  const bad=structuredClone(f);bad.grant[field]=field==='generation'?2:'foreign';assert.throws(()=>selectRetainedAction({...bad,selectedActionId:'block'}));
 }
 const bad=structuredClone(f);bad.grant.allowedActions=['wait_ticks'];assert.throws(()=>selectRetainedAction({...bad,selectedActionId:'block'}));
});
test('same action name in another process snapshot has a separate exact key',async()=>{
 const {selectRetainedAction}=await api();const f=fixture();const a=selectRetainedAction({...f,selectedActionId:'block'});
 const g={...f.grant,runSnapshotId:'next-snapshot',processEpoch:2};const b=selectRetainedAction({...f,grant:g,selectedActionId:'block'});
 assert.notEqual(a.action.idempotencyKey,b.action.idempotencyKey);
});
