import {exactObjectKeys as exact} from './cached-path-contract.mjs';
export function validBrainStartLoop(d,record){
 const rev=record.payload.targetRevision,obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
 const id=(v,p,max)=>typeof v==='string'&&v.startsWith(p+':'+rev+':')&&v.split(':').length===3&&/^[1-9][0-9]{0,2}$/.test(v.split(':').at(-1))&&Number(v.split(':').at(-1))<=max;
 const long=v=>typeof v==='string'&&/^(0|-[1-9][0-9]*|[1-9][0-9]*)$/.test(v)&&v.length<=20&&BigInt(v)>=-9223372036854775808n&&BigInt(v)<=9223372036854775807n;
 const identity=c=>c.instanceIdentity==null?c.instanceIdentityStatus==='NOT_EXPOSED':c.instanceIdentityStatus==='AVAILABLE'&&id(c.instanceIdentity,'component',128);
 const label=v=>typeof v==='string'&&v.length>0&&v.length<=512;
 if(!exact(d,['brainClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'loopInvocationId','sourceGameTimeStatus',...(d.gameTimeArgument==null?[]:['gameTimeArgument']),'priorityStatus','activities','activitiesTruncated','iterationScope','returnScope','eligibilityReasonStatus','arrivalStatus'])||
   !label(d.brainClass)||!identity(d)||!id(d.loopInvocationId,'start-loop',256)||
   !(d.gameTimeArgument==null?d.sourceGameTimeStatus==='NOT_CAPTURED':d.sourceGameTimeStatus==='AVAILABLE'&&long(d.gameTimeArgument))||
   ['priorityStatus','eligibilityReasonStatus','arrivalStatus'].some(k=>d[k]!=='NOT_EXPOSED')||
   d.iterationScope!=='ORIGINAL_ACTIVITY_AND_CONTROL_RETURN_PREFIX_NOT_ALL_ELIGIBILITY_REASONS'||d.returnScope!=='NORMAL_ORIGINAL_PRIVATE_START_LOOP_NOT_ALL_STARTS_OR_ARRIVAL'||
   !Array.isArray(d.activities)||d.activities.length>8||typeof d.activitiesTruncated!=='boolean'||d.activitiesTruncated&&d.activities.length!==8)return false;
 return d.activities.every((a,i)=>obj(a)&&exact(a,['activityIndex','activityStatus',...(a.activity==null?[]:['activity']),'result','controls','controlsTruncated'])&&a.activityIndex===i+1&&typeof a.result==='boolean'&&
   (a.activity==null?a.activityStatus==='NOT_EXPOSED':a.activityStatus==='AVAILABLE'&&['CORE','IDLE','REST','WORK','MEET','PLAY','FIGHT'].includes(a.activity))&&
   Array.isArray(a.controls)&&a.controls.length<=8&&typeof a.controlsTruncated==='boolean'&&(!a.controlsTruncated||a.controls.length===8)&&
   (a.result||a.controls.length===0&&!a.controlsTruncated)&&a.controls.every((c,j)=>obj(c)&&exact(c,['controlIndex','controlClass','instanceIdentityStatus',...(c.instanceIdentity==null?[]:['instanceIdentity']),'status','tryStartStatus',...(c.tryStartResult==null?[]:['tryStartResult']),...(c.capturedTryStartInvocationId==null?[]:['capturedTryStartInvocationId'])])&&
     c.controlIndex===j+1&&label(c.controlClass)&&identity(c)&&['STOPPED','RUNNING','NOT_EXPOSED'].includes(c.status)&&
     (c.status==='STOPPED'?c.tryStartStatus==='NORMAL_RETURN'&&typeof c.tryStartResult==='boolean'&&d.sourceGameTimeStatus==='AVAILABLE':c.tryStartStatus==='NOT_CALLED'&&c.tryStartResult===undefined&&c.capturedTryStartInvocationId===undefined)&&
     (c.capturedTryStartInvocationId===undefined||c.controlClass==='net.minecraft.world.entity.ai.behavior.MoveToTargetSink'&&id(c.capturedTryStartInvocationId,'try-start',256))))&&
   (d.sourceGameTimeStatus==='NOT_CAPTURED'||d.activitiesTruncated||d.activities.some(a=>a.controlsTruncated||a.controls.some(c=>c.status==='STOPPED')));
}
