import {exactObjectKeys as exact} from './cached-path-contract.mjs';
export const BRAIN_START_KINDS=Object.freeze(['BRAIN_PATH_START_CONDITION_RETURN','BRAIN_PATH_START_DISPATCH_RETURN','BRAIN_PATH_TRY_START_RETURN']);
const long=v=>typeof v==='string'&&/^(0|-[1-9][0-9]*|[1-9][0-9]*)$/.test(v)&&v.length<=20&&BigInt(v)>=-9223372036854775808n&&BigInt(v)<=9223372036854775807n;
export function validBrainStart(kind,d,record){
 const rev=record.payload.targetRevision,id=(v,p,max)=>typeof v==='string'&&v.startsWith(p+':'+rev+':')&&v.split(':').length===3&&/^[1-9][0-9]{0,2}$/.test(v.split(':').at(-1))&&Number(v.split(':').at(-1))<=max;
 const common=['sinkClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'tryStartInvocationId','gameTimeArgument','dispatchScope','operandReasonStatus','arrivalStatus','searchRelationStatus'];
 if(d.sinkClass!=='net.minecraft.world.entity.ai.behavior.MoveToTargetSink'||!id(d.tryStartInvocationId,'try-start',256)||!long(d.gameTimeArgument)||
   !(d.instanceIdentity==null?d.instanceIdentityStatus==='NOT_EXPOSED':d.instanceIdentityStatus==='AVAILABLE'&&id(d.instanceIdentity,'component',128))||
   d.dispatchScope!=='ORIGINAL_BRAIN_NON_RUNNING_BEHAVIOR_INTERFACE_CALL_EXACT_SINK'||['operandReasonStatus','arrivalStatus','searchRelationStatus'].some(k=>d[k]!=='NOT_EXPOSED'))return false;
 const children=(ids,truncated,p)=>Array.isArray(ids)&&ids.length<=8&&typeof truncated==='boolean'&&(!truncated||ids.length===8)&&ids.every((v,i)=>id(v,p,256)&&(i===0||Number(v.split(':').at(-1))>Number(ids[i-1].split(':').at(-1))));
 if(kind==='BRAIN_PATH_START_CONDITION_RETURN')return exact(d,[...common,'condition','result','capturedComputeInvocationIds','capturedComputeInvocationsTruncated','childScope','resultScope'])&&
   ['HAS_REQUIRED_MEMORIES','CHECK_EXTRA_START'].includes(d.condition)&&typeof d.result==='boolean'&&children(d.capturedComputeInvocationIds,d.capturedComputeInvocationsTruncated,'compute')&&
   (d.condition==='CHECK_EXTRA_START'||d.capturedComputeInvocationIds.length===0&&!d.capturedComputeInvocationsTruncated)&&
   d.childScope==='DIRECT_CAPTURED_PRIVATE_COMPUTE_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN'&&d.resultScope==='ORIGINAL_VIRTUAL_START_CONDITION_BOOLEAN_NOT_INDIVIDUAL_MEMORY_REASONS';
 if(kind==='BRAIN_PATH_START_DISPATCH_RETURN')return exact(d,[...common,'branch','capturedSinkInvocationIds','capturedSinkInvocationsTruncated','childScope','returnScope'])&&d.branch==='START'&&
   children(d.capturedSinkInvocationIds,d.capturedSinkInvocationsTruncated,'sink')&&d.childScope==='DIRECT_CAPTURED_CONCRETE_CALL_SCOPES_NOT_COMPLETION_OR_FULL_CHILDREN'&&d.returnScope==='NORMAL_ORIGINAL_START_VOID_NOT_NAVIGATION_SUCCESS_OR_ARRIVAL';
 return kind==='BRAIN_PATH_TRY_START_RETURN'&&exact(d,[...common,'result','resultScope'])&&typeof d.result==='boolean'&&d.resultScope==='ORIGINAL_INTERFACE_TRY_START_BOOLEAN_NOT_NAVIGATION_SUCCESS_OR_ARRIVAL';
}
