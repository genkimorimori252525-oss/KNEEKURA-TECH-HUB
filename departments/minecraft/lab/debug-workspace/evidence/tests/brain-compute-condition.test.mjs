import test from 'node:test';
import assert from 'node:assert/strict';
import {validOriginalDecisionEvent,appendOriginalDecisionEvents} from '../original-decision-events.mjs';
const common=()=>({sinkClass:'net.minecraft.world.entity.ai.behavior.MoveToTargetSink',instanceIdentity:'component:7:1',instanceIdentityStatus:'AVAILABLE',computeInvocationId:'compute:7:1',callSite:'CHECK_EXTRA_START',gameTimeArgument:'100',walkTargetClass:'net.minecraft.world.entity.ai.memory.WalkTarget',enclosingSinkInvocationStatus:'NOT_CAPTURED',enclosingTickStopInvocationStatus:'NOT_CAPTURED',parentScope:'CAPTURED_ENCLOSING_SOURCE_SCOPES_NOT_IMMEDIATE_CAUSE_OR_ADOPTION',fieldScope:'BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY',arrivalStatus:'NOT_EXPOSED',operandReasonStatus:'NOT_EXPOSED'});
const record=d=>({source:{side:'SERVER'},observationId:'obs:compute-condition:'+d.condition,gameTime:100,payload:{schema:'kneekura.original-decision-event/v1',semantics:'ORIGINAL_INVOCATION_RETURN_ONLY',targetRevision:7,burstId:'burst:7:100',eventIndex:1,kind:'BRAIN_PATH_COMPUTE_CONDITION_RETURN',data:{...common(),...d},observerCostNanos:1,observerCostScope:'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER'}});
const reached=(distance=10,close=0)=>record({condition:'REACHED_TARGET',result:distance<=close,reachedInvocationId:'compute:7:1:reached:1',operands:{scope:'ORIGINAL_PRIVATE_PREDICATE_RETURN_OPERANDS_NOT_COORDINATE_RECOMPUTATION',distanceStatus:'AVAILABLE',distanceReturn:distance,closeEnoughStatus:'AVAILABLE',closeEnoughReturn:close},resultScope:'ORIGINAL_PRIVATE_REACHED_TARGET_BOOLEAN_NOT_ARRIVAL'});
const path=()=>({present:true,className:'custom.Path',identity:{status:'AVAILABLE',allocator:'SNAPSHOT_REFERENCE',targetRevision:7,token:'path:7:1'}});
const can=()=>record({condition:'PATH_CAN_REACH',result:true,argumentPath:path(),cachedSinkPath:path(),argumentMatchesCachedSinkPath:true,referenceScope:'RAW_ARGUMENT_VS_CACHED_SINK_PATH_AFTER_ORIGINAL_RETURN',resultScope:'ORIGINAL_VIRTUAL_PATH_CAN_REACH_BOOLEAN_NOT_COMPUTE_SUCCESS_OR_ARRIVAL'});
test('actual compute predicates and returned operands are partial evaluation, never compute success or arrival',()=>{
 const records=[reached(),can()];assert.ok(records.every(validOriginalDecisionEvent));const stages={},capabilities={},timeline=[];appendOriginalDecisionEvents(records,stages,capabilities,timeline);assert.equal(stages.EVALUATION.facts.length,2);assert.equal(capabilities.brain_navigation.status,'PARTIAL');for(const k of ['CANDIDATE','SELECTION','EXECUTION','RESULT'])assert.equal(stages[k],undefined);
});
test('signed original integer operands preserve equality, negative overflow and actual comparator without mathematical replacement',()=>{
 assert.ok([reached(5,5),reached(-7,-8),reached(-2147483648,0)].every(validOriginalDecisionEvent));
 for(const mutate of [d=>d.result=!d.result,d=>d.operands.distanceReturn=2147483648,d=>d.operands.closeEnoughReturn=0.5,d=>d.operands.x=10,d=>d.operands.scope='CACHED_COORDINATE_DISTANCE',d=>d.resultScope='ARRIVED']){const r=reached();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);}
});
test('absent or ambiguous source operands remain unknown instead of reconstructing a source getter result',()=>{
 const r=reached();delete r.payload.data.operands.distanceReturn;r.payload.data.operands.distanceStatus='NOT_CAPTURED';assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.result=true;assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.operands.distanceReturn=10;assert.equal(validOriginalDecisionEvent(r),false);
});
test('reject unrelated or overflow reached scopes, extra reason fields and wrong root boundary semantics',()=>{
 for(const mutate of [d=>d.reachedInvocationId='compute:8:1:reached:1',d=>d.reachedInvocationId='compute:7:2:reached:1',d=>d.reachedInvocationId='compute:7:1:reached:9',d=>d.condition='ARRIVAL',d=>d.arrivalStatus='AVAILABLE',d=>d.shortCircuitReason='DISTANCE']){const r=reached();mutate(r.payload.data);assert.equal(validOriginalDecisionEvent(r),false);}
 const r=reached();r.payload.semantics='ORIGINAL_FIELD_WRITE_CHECKPOINT_ONLY';assert.equal(validOriginalDecisionEvent(r),false);
});
test('actual virtual Path boolean is independent of opaque cached fields while raw references stay consistent',()=>{
 const r=can();assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.result=false;assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.argumentMatchesCachedSinkPath=false;assert.equal(validOriginalDecisionEvent(r),false);
 r.payload.data.cachedSinkPath={present:false};assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.argumentPath={present:false};assert.equal(validOriginalDecisionEvent(r),false);
});
test('component and Path identity caps allow actual booleans without invented IDs or uncalled null methods',()=>{
 const r=can();delete r.payload.data.instanceIdentity;r.payload.data.instanceIdentityStatus='NOT_EXPOSED';for(const p of [r.payload.data.argumentPath,r.payload.data.cachedSinkPath])p.identity={status:'NOT_EXPOSED',allocator:'SNAPSHOT_REFERENCE',targetRevision:7,detail:'REFERENCE_LIMIT'};assert.equal(validOriginalDecisionEvent(r),true);r.payload.data.argumentPath.identity.token='path:7:2';assert.equal(validOriginalDecisionEvent(r),false);
});
