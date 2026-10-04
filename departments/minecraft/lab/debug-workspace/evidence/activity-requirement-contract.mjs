import {exactObjectKeys as exact} from './cached-path-contract.mjs';
export function validActivityRequirement(d,record){
 const rev=record.payload.targetRevision,id=(v,p,max)=>typeof v==='string'&&v.startsWith(p+':'+rev+':')&&v.split(':').length===3&&/^[1-9][0-9]{0,2}$/.test(v.split(':').at(-1))&&Number(v.split(':').at(-1))<=max;
 if(!exact(d,['brainClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'activityInvocationId','dispatchScope','fieldScope','behaviorStopStatus','movementOutcomeStatus','requirementInvocationId','callerSite','requestedActivityStatus',...(d.requestedActivity==null?[]:['requestedActivity']),'mapContains','result','checks','checksTruncated','checkScope'])||
   typeof d.brainClass!=='string'||d.brainClass.length<1||d.brainClass.length>512||!id(d.activityInvocationId,'activity',256)||!id(d.requirementInvocationId,'activity-requirement',256)||
   !(d.instanceIdentity==null?d.instanceIdentityStatus==='NOT_EXPOSED':d.instanceIdentityStatus==='AVAILABLE'&&id(d.instanceIdentity,'component',128))||
   d.dispatchScope!=='UPDATE_ACTIVITY_FROM_SCHEDULE_ORIGINAL_VIRTUAL_CALL'||d.fieldScope!=='BASE_BRAIN_CACHED_FIELDS_ONLY'||['behaviorStopStatus','movementOutcomeStatus'].some(k=>d[k]!=='NOT_EXPOSED')||
   !['IF_POSSIBLE','FIRST_VALID'].includes(d.callerSite)||
   !(d.requestedActivity==null?d.requestedActivityStatus==='NOT_EXPOSED':d.requestedActivityStatus==='AVAILABLE'&&['CORE','IDLE','REST','WORK','MEET','PLAY','FIGHT'].includes(d.requestedActivity))||
   typeof d.mapContains!=='boolean'||typeof d.result!=='boolean'||typeof d.checksTruncated!=='boolean'||!Array.isArray(d.checks)||d.checks.length>8||d.checksTruncated&&d.checks.length!==8||!d.mapContains&&(d.checks.length!==0||d.checksTruncated)||
   d.checkScope!=='ORIGINAL_ACTIVITY_REQUIREMENT_MAP_AND_VIRTUAL_CHECK_RETURNS_PREFIX_NOT_ALL_ELIGIBILITY_REASONS')return false;
 return d.checks.every((c,i)=>c!==null&&typeof c==='object'&&!Array.isArray(c)&&exact(c,['checkIndex','memoryModuleStatus',...(c.memoryModule==null?[]:['memoryModule']),'requestedMemoryStatus','result'])&&c.checkIndex===i+1&&typeof c.result==='boolean'&&
   (c.memoryModule==null?c.memoryModuleStatus==='NOT_EXPOSED':c.memoryModuleStatus==='AVAILABLE'&&['PATH','WALK_TARGET','CANT_REACH_WALK_TARGET_SINCE'].includes(c.memoryModule))&&['REGISTERED','VALUE_PRESENT','VALUE_ABSENT','NOT_EXPOSED'].includes(c.requestedMemoryStatus));
}
