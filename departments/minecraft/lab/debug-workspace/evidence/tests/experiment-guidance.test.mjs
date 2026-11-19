import test from 'node:test';
import assert from 'node:assert/strict';
import {buildExperimentGuidance} from '../experiment-guidance.mjs';
const identity={debugSessionId:'s',runId:'r',runSnapshotId:'snap',processEpoch:1,arenaEpoch:0,targetRevision:1,subjectUuid:'00000000-0000-0000-0000-000000000001'};
const digest={schema:'kneekura.experiment-digest/v1',identity,quality:{status:'INCONCLUSIVE',coverage:{requestedWindow:{startTick:0,endTick:100},gapCount:1}},cleanup:'UNKNOWN',
  retainedEvents:Array.from({length:40},(_,i)=>({observationId:'obs:'+i,tick:i,kind:'CONTROL_PROJECTILE_HIT_RETURN',evidenceRefs:['obs:'+i],imageStatus:'NOT_CAPTURED'})),evidenceRefs:{sourceObservationIds:['obs:0'],canonicalBinding:{canonicalFileHash:'a'.repeat(64)}}};
test('32 bookmarks describe selected real events and never invent missing preframes or change event totals',()=>{
  const original=JSON.stringify(digest),a=buildExperimentGuidance({digest,health:{},capabilities:{queries:['path_search','movement_control']},maxBookmarks:32});
  assert.equal(a.bookmarks.length,32);assert.deepEqual(a.displaySelection,{eligibleCount:40,displayedCount:32,omittedCount:8,selectionPolicy:'LATEST_RETAINED_EVENTS_SORTED_BY_TICK_AND_ID'});
  assert(a.bookmarks.every(b=>b.image.status==='NOT_CAPTURED'));assert.equal(JSON.stringify(digest),original);
  assert.throws(()=>buildExperimentGuidance({digest,health:{},capabilities:{queries:[]},maxBookmarks:33}),/BOOKMARK/);
});
test('guidance uses only supported typed read queries, source refs and explicit budgets without automatic actions',()=>{
  const a=buildExperimentGuidance({digest,health:{targetMismatch:true,leaseExpired:true,pathAdoptionMissing:true},capabilities:{queries:['path_search','path_returned_nodes','movement_control']}});
  assert(a.suggestions.length>0);assert(a.suggestions.every(s=>!('probability' in s)&&!('cause' in s)&&s.proposedQuery.readOnly===true));
  assert.equal(a.budgets.coldStartupMs,null);assert.equal(a.budgets.cleanup,'UNKNOWN');assert.equal(a.automaticallyExecutes,false);
  assert.throws(()=>buildExperimentGuidance({digest,health:{},capabilities:{queries:['run_command']}}),/QUERY/);
});

test('only sealed same-tick image references can accompany a bookmark; missing preframe stays absent',()=>{
  const capture={status:'VERIFIED_SEALED_CAPTURE_REFERENCE',captureTick:39,imageHash:'a'.repeat(64),sourceObservationId:'capture:39',view:'north',imagePath:'evidence/captures/a.png'};
  const a=buildExperimentGuidance({digest:{...digest,retainedCaptures:[capture]},health:{},capabilities:{queries:[]}});
  assert.equal(a.bookmarks.at(-1).image.status,'RETAINED_SAME_TICK_CONTEXT');assert.equal(a.bookmarks.at(-2).image.status,'NOT_CAPTURED');
  assert.throws(()=>buildExperimentGuidance({digest:{...digest,retainedCaptures:[{...capture,status:'REQUESTED'}]},health:{},capabilities:{queries:[]}}),/VERIFIED/);
});
