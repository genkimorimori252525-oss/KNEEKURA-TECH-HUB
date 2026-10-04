import {exactObjectKeys as exact} from './cached-path-contract.mjs';
export function validBrainMemorySource(d,record){
 const rev=record.payload.targetRevision,id=(v,p,max=256)=>typeof v==='string'&&v.startsWith(p+':'+rev+':')&&v.split(':').length===3&&/^[1-9][0-9]{0,2}$/.test(v.split(':').at(-1))&&Number(v.split(':').at(-1))<=max;
 const activity=record.payload.kind==='BRAIN_ACTIVITY_MEMORY_SOURCE_RETURN',called=d.presenceStatus==='NORMAL_RETURN';
 if(!exact(d,['brainClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'memorySourceInvocationId','requirementInvocationId',activity?'activityInvocationId':'tryStartInvocationId','checkIndex','memoryModuleStatus',...(d.memoryModule==null?[]:['memoryModule']),'requestedMemoryStatus','slotStatus','presenceStatus',...(called?['presenceSite','presenceResult']:[]),'baseResult','result','sourceScope'])||
 typeof d.brainClass!=='string'||d.brainClass.length<1||d.brainClass.length>512||!id(d.memorySourceInvocationId,'memory-source')||!id(d.requirementInvocationId,activity?'activity-requirement':'memory-requirement')||!id(activity?d.activityInvocationId:d.tryStartInvocationId,activity?'activity':'try-start')||
 !(d.instanceIdentity==null?d.instanceIdentityStatus==='NOT_EXPOSED':d.instanceIdentityStatus==='AVAILABLE'&&id(d.instanceIdentity,'component',128))||!Number.isSafeInteger(d.checkIndex)||d.checkIndex<1||d.checkIndex>8||
 !(d.memoryModule==null?d.memoryModuleStatus==='NOT_EXPOSED':d.memoryModuleStatus==='AVAILABLE'&&['PATH','WALK_TARGET','CANT_REACH_WALK_TARGET_SINCE'].includes(d.memoryModule))||!['REGISTERED','VALUE_PRESENT','VALUE_ABSENT','NOT_EXPOSED'].includes(d.requestedMemoryStatus)||
 !['NULL','NON_NULL'].includes(d.slotStatus)||!['NOT_CALLED','NORMAL_RETURN'].includes(d.presenceStatus)||typeof d.baseResult!=='boolean'||typeof d.result!=='boolean'||d.sourceScope!=='ORIGINAL_BASE_MAP_PRESENCE_AND_RETURN_WITH_VIRTUAL_RESULT_NOT_ALL_ELIGIBILITY_REASONS')return false;
 if(called)return d.slotStatus==='NON_NULL'&&['VALUE_PRESENT','VALUE_ABSENT'].includes(d.presenceSite)&&d.presenceSite===d.requestedMemoryStatus&&typeof d.presenceResult==='boolean';
 return d.slotStatus==='NULL'||['REGISTERED','NOT_EXPOSED'].includes(d.requestedMemoryStatus);
}
