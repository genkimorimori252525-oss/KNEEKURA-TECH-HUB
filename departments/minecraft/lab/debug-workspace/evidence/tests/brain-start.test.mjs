import test from 'node:test';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
const common=()=>({sinkClass:'net.minecraft.world.entity.ai.behavior.MoveToTargetSink',instanceIdentityStatus:'AVAILABLE',instanceIdentity:'component:7:1',tryStartInvocationId:'try-start:7:1',gameTimeArgument:'100',dispatchScope:'ORIGINAL_BRAIN_NON_RUNNING_BEHAVIOR_INTERFACE_CALL_EXACT_SINK',operandReasonStatus:'NOT_EXPOSED',arrivalStatus:'NOT_EXPOSED',searchRelationStatus:'NOT_EXPOSED'});
const record=(kind,extra)=>({source:{side:'SERVER'},gameTime:100,observationId:'obs:start:'+kind,payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:7,burstId:'burst:7:100',eventIndex:1,kind,data:{...common(),...extra},observerCostNanos:1,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'}});
const condition=(condition='HAS_REQUIRED_MEMORIES',result=false)=>record('BRAIN_PATH_START_CONDITION_RETURN',{condition,result,capturedComputeInvocationIds:[],capturedComputeInvocationsTruncated:false,childScope:'DIRECT_CAPTURED_PRIVATE_COMPUTE_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN',resultScope:'ORIGINAL_VIRTUAL_START_CONDITION_BOOLEAN_NOT_INDIVIDUAL_MEMORY_REASONS'});
const dispatch=()=>record('BRAIN_PATH_START_DISPATCH_RETURN',{branch:'START',capturedSinkInvocationIds:['sink:7:1'],capturedSinkInvocationsTruncated:false,childScope:'DIRECT_CAPTURED_CONCRETE_CALL_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN',returnScope:'NORMAL_ORIGINAL_START_VOID_NOT_NAVIGATION_SUCCESS_OR_ARRIVAL'});
const returned=()=>record('BRAIN_PATH_TRY_START_RETURN',{result:true,resultScope:'ORIGINAL_INTERFACE_TRY_START_BOOLEAN_NOT_NAVIGATION_SUCCESS_OR_ARRIVAL'});
test('actual memory/extra condition, start dispatch and interface return remain distinct partial facts',()=>{
 const extra=condition('CHECK_EXTRA_START',true);extra.payload.data.capturedComputeInvocationIds=['compute:7:2'];const rows=[condition('HAS_REQUIRED_MEMORIES',true),extra,dispatch(),returned()];assert.ok(rows.every(validOriginalDecisionEvent));const stages={},caps={},timeline=[];appendOriginalDecisionEvents(rows,stages,caps,timeline);assert.equal(stages.EVALUATION.facts.length,3);assert.equal(stages.EXECUTION.facts.length,1);assert.equal(caps.brain_navigation.status,'PARTIAL');for(const s of ['CANDIDATE','SELECTION','RESULT'])assert.equal(stages[s],undefined);
});
test('false memory, empty direct children and unknown component identity do not invent absent conditions',()=>{
 const rows=[condition(),returned()];rows[1].payload.data.result=false;for(const r of rows){delete r.payload.data.instanceIdentity;r.payload.data.instanceIdentityStatus='NOT_EXPOSED';assert.equal(validOriginalDecisionEvent(r),true);}const r=dispatch();r.payload.data.capturedSinkInvocationIds=[];assert.equal(validOriginalDecisionEvent(r),true);
});
test('reject invented reasons/results, extra keys, wrong revision and invalid component IDs',()=>{
 for(const mutate of [d=>d.operandReasonStatus='AVAILABLE',d=>d.arrivalStatus='AVAILABLE',d=>d.result='false',d=>d.tryStartInvocationId='try-start:8:1',d=>d.instanceIdentity='component:7:129',d=>d.rngResult=1,d=>d.condition='TIMED_OUT',d=>d.resultScope='ARRIVED']){const r=condition();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);}
 for(const mutate of [d=>d.resultScope='NAVIGATION_SUCCESS',d=>d.result=0,d=>d.started=true]){const r=returned();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);}
});
test('compute children require actual extra-condition scope and bounded ordered same-revision IDs',()=>{
 for(const mutate of [d=>d.capturedComputeInvocationIds=['compute:7:1'],d=>d.capturedComputeInvocationsTruncated=true]){const r=condition();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);}
 for(const ids of [['compute:8:1'],['compute:7:1','compute:7:1'],['compute:7:2','compute:7:1'],Array.from({length:9},(_,i)=>'compute:7:'+(i+1)),['compute:7:257']]){const r=condition('CHECK_EXTRA_START',true);r.payload.data.capturedComputeInvocationIds=ids;assert.equal(validOriginalDecisionEvent(r),false);}
 const r=condition('CHECK_EXTRA_START',false);r.payload.data.capturedComputeInvocationIds=Array.from({length:8},(_,i)=>'compute:7:'+(i+1));r.payload.data.capturedComputeInvocationsTruncated=true;assert.equal(validOriginalDecisionEvent(r),true);
});
test('start dispatch child IDs never imply navigation success or a complete child list',()=>{
 for(const mutate of [d=>d.branch='TICK',d=>d.result=true,d=>d.capturedSinkInvocationIds=['sink:8:1'],d=>d.capturedSinkInvocationIds=['sink:7:1','sink:7:1'],d=>d.capturedSinkInvocationsTruncated=true]){const r=dispatch();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);}const r=dispatch();r.payload.data.capturedSinkInvocationIds=Array.from({length:8},(_,i)=>'sink:7:'+(i+1));r.payload.data.capturedSinkInvocationsTruncated=true;assert.equal(validOriginalDecisionEvent(r),true);
});
test('consumer rejects malformed event scope and preserves original signed-long argument',()=>{
 const r=returned();r.payload.data.gameTimeArgument='-9223372036854775808';assert.equal(validOriginalDecisionEvent(r),true);for(const v of ['01','-0','9223372036854775808','100.0',100]){r.payload.data.gameTimeArgument=v;assert.equal(validOriginalDecisionEvent(r),false);}r.payload.data.gameTimeArgument='100';r.source.side='CLIENT';assert.equal(validOriginalDecisionEvent(r),false);
});
