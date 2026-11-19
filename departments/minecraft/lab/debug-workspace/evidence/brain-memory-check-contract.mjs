import {exactObjectKeys as exact} from './cached-path-contract.mjs';
export function validBrainMemoryRequirement(d,record){
 const rev=record.payload.targetRevision,id=(v,p,max)=>typeof v==='string'&&v.startsWith(p+':'+rev+':')&&v.split(':').length===3&&/^[1-9][0-9]{0,2}$/.test(v.split(':').at(-1))&&Number(v.split(':').at(-1))<=max;
 const long=v=>typeof v==='string'&&/^(0|-[1-9][0-9]*|[1-9][0-9]*)$/.test(v)&&v.length<=20&&BigInt(v)>=-9223372036854775808n&&BigInt(v)<=9223372036854775807n;
 const common=['sinkClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'tryStartInvocationId','gameTimeArgument','dispatchScope','operandReasonStatus','arrivalStatus','searchRelationStatus'];
 if(!exact(d,[...common,'requirementInvocationId','condition','result','checks','checksTruncated','checkScope'])||
   d.sinkClass!=='net.minecraft.world.entity.ai.behavior.MoveToTargetSink'||!id(d.tryStartInvocationId,'try-start',256)||!id(d.requirementInvocationId,'memory-requirement',256)||!long(d.gameTimeArgument)||
   !(d.instanceIdentity==null?d.instanceIdentityStatus==='NOT_EXPOSED':d.instanceIdentityStatus==='AVAILABLE'&&id(d.instanceIdentity,'component',128))||
   d.dispatchScope!=='ORIGINAL_BRAIN_NON_RUNNING_BEHAVIOR_INTERFACE_CALL_EXACT_SINK'||['operandReasonStatus','arrivalStatus','searchRelationStatus'].some(k=>d[k]!=='NOT_EXPOSED')||
   d.condition!=='HAS_REQUIRED_MEMORIES'||typeof d.result!=='boolean'||typeof d.checksTruncated!=='boolean'||!Array.isArray(d.checks)||d.checks.length<1||d.checks.length>8||d.checksTruncated&&d.checks.length!==8||
   d.checkScope!=='ORIGINAL_VIRTUAL_CHECK_MEMORY_RETURNS_PREFIX_NOT_REPLAY_OR_ALL_ELIGIBILITY_REASONS')return false;
 return d.checks.every((c,i)=>c!==null&&typeof c==='object'&&!Array.isArray(c)&&exact(c,['checkIndex','memoryModuleStatus',...(c.memoryModule==null?[]:['memoryModule']),'requestedMemoryStatus','result'])&&c.checkIndex===i+1&&typeof c.result==='boolean'&&
   (c.memoryModule==null?c.memoryModuleStatus==='NOT_EXPOSED':c.memoryModuleStatus==='AVAILABLE'&&['PATH','WALK_TARGET','CANT_REACH_WALK_TARGET_SINCE'].includes(c.memoryModule))&&
   ['REGISTERED','VALUE_PRESENT','VALUE_ABSENT','NOT_EXPOSED'].includes(c.requestedMemoryStatus));
}
