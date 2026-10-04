import {exactObjectKeys as exact,validPathReferenceFact,validCachedPathFact,consistentRawPathMatch} from './cached-path-contract.mjs';
export const BRAIN_COMPUTE_KINDS=Object.freeze(['BRAIN_PATH_COMPUTE_RETURN','BRAIN_PATH_CREATE_RETURN','BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT','BRAIN_PATH_FINDER_RETURN']);
const text=v=>typeof v==='string'&&v.length>0&&v.length<=512;
const integer=v=>Number.isSafeInteger(v);
const long=v=>{try{return typeof v==='string'&&/^-?(0|[1-9][0-9]*)$/.test(v)&&BigInt(v)>=-(1n<<63n)&&BigInt(v)<(1n<<63n);}catch{return false;}};
const finite=(d,k)=>Number.isFinite(d[k])?d[k+'Status']===undefined:d[k]===undefined&&d[k+'Status']==='NOT_EXPOSED';
const scalarKey=(d,k)=>Number.isFinite(d[k])?k:k+'Status';
function argumentsValid(d){
 if(d?.kind==='DDD_I')return exact(d,['kind','accuracy',...['x','y','z'].map(k=>scalarKey(d,k))])&&integer(d.accuracy)&&['x','y','z'].every(k=>finite(d,k));
 if(d?.kind!=='BLOCK_POS_I'||!integer(d.accuracy)||typeof d.present!=='boolean')return false;
 if(!d.present)return exact(d,['kind','accuracy','present']);
 const known=['net.minecraft.core.BlockPos','net.minecraft.core.BlockPos$MutableBlockPos'].includes(d.className);
 return text(d.className)&&d.positionStatus===(known?'AVAILABLE':'NOT_EXPOSED')&&exact(d,['kind','accuracy','present','className','positionStatus',...(known?['x','y','z']:[])])&&(!known||['x','y','z'].every(k=>integer(d[k])&&d[k]>=-2147483648&&d[k]<=2147483647));
}
export function validBrainCompute(kind,d,record){
 const rev=record.payload.targetRevision;
 const id=(v,p,max)=>typeof v==='string'&&v.startsWith(p+':'+rev+':')&&/^[1-9][0-9]{0,2}$/.test(v.split(':').at(-1))&&v.split(':').length===3&&Number(v.split(':').at(-1))<=max;
 const child=(v,parent,name)=>typeof v==='string'&&v.startsWith(parent+':'+name+':')&&v.split(':').length===parent.split(':').length+2&&/^[1-8]$/.test(v.split(':').at(-1));
 const optional=(key,p)=>d[key+'Status']==='AVAILABLE'?id(d[key+'Id'],p,256):d[key+'Status']==='NOT_CAPTURED'&&d[key+'Id']===undefined;
 const common=['sinkClass','instanceIdentityStatus',...(d.instanceIdentity==null?[]:['instanceIdentity']),'computeInvocationId','callSite','gameTimeArgument','walkTargetClass','enclosingSinkInvocationStatus',...(d.enclosingSinkInvocationStatus==='AVAILABLE'?['enclosingSinkInvocationId']:[]),'enclosingTickStopInvocationStatus',...(d.enclosingTickStopInvocationStatus==='AVAILABLE'?['enclosingTickStopInvocationId']:[]),'parentScope','fieldScope','arrivalStatus','operandReasonStatus'];
 if(d.sinkClass!=='net.minecraft.world.entity.ai.behavior.MoveToTargetSink'||!id(d.computeInvocationId,'compute',256)||!text(d.walkTargetClass)||!long(d.gameTimeArgument)||!['CHECK_EXTRA_START','TICK_RECOMPUTE'].includes(d.callSite)||
   !(d.instanceIdentity==null?d.instanceIdentityStatus==='NOT_EXPOSED':d.instanceIdentityStatus==='AVAILABLE'&&id(d.instanceIdentity,'component',128))||
   !optional('enclosingSinkInvocation','sink')||!optional('enclosingTickStopInvocation','tick-stop')||d.parentScope!=='CAPTURED_ENCLOSING_SOURCE_SCOPES_NOT_IMMEDIATE_CAUSE_OR_ADOPTION'||d.fieldScope!=='BASE_CACHED_FIELDS_AT_DECLARED_CAPTURE_BOUNDARY'||d.arrivalStatus!=='NOT_EXPOSED'||d.operandReasonStatus!=='NOT_EXPOSED')return false;
 const relation=['createReturnStatus',...(d.createReturnStatus==='AVAILABLE'?['lastCreateInvocationId','createdPath','createdMatchesSinkPath']:[]),'referenceScope'];
 const validRelation=()=>d.referenceScope==='RAW_RETURNED_VS_CACHED_PATH_REFERENCE_EQUALITY'&&
   (d.createReturnStatus==='NOT_CAPTURED'?d.lastCreateInvocationId===undefined&&d.createdPath===undefined&&d.createdMatchesSinkPath===undefined:
    d.createReturnStatus==='AVAILABLE'&&child(d.lastCreateInvocationId,d.computeInvocationId,'create')&&validPathReferenceFact(d.createdPath,rev)&&typeof d.createdMatchesSinkPath==='boolean'&&consistentRawPathMatch(d.createdMatchesSinkPath,d.createdPath,d.sinkPath));
 if(kind==='BRAIN_PATH_COMPUTE_RETURN')return exact(d,[...common,'result','resultScope','sinkPath','navigationPath',...relation])&&typeof d.result==='boolean'&&d.resultScope==='ORIGINAL_PRIVATE_COMPUTE_BOOLEAN_NOT_CAN_REACH_ADOPTION_OR_ARRIVAL'&&validCachedPathFact(d.sinkPath,rev)&&validPathReferenceFact(d.navigationPath,rev)&&validRelation();
 if(kind==='BRAIN_PATH_COMPUTE_PATH_WRITE_CHECKPOINT')return exact(d,[...common,'writeSite','writeScope','sinkPath',...relation])&&['INITIAL','FALLBACK'].includes(d.writeSite)&&d.writeScope==='AFTER_ORIGINAL_SINK_PATH_PUTFIELD_NOT_NAVIGATION_ADOPTION'&&validCachedPathFact(d.sinkPath,rev)&&validRelation();
 if(!child(d.createInvocationId,d.computeInvocationId,'create')||!['INITIAL','FALLBACK'].includes(d.createSite)||!validCachedPathFact(d.returnedPath,rev))return false;
 if(kind==='BRAIN_PATH_CREATE_RETURN'){
   const ids=d.capturedFinderInvocationIds;
   return exact(d,[...common,'createInvocationId','createSite','arguments','returnedPath','navigationPath','returnedMatchesNavigationPath','capturedFinderInvocationIds','capturedFinderInvocationsTruncated','searchScope','returnScope'])&&argumentsValid(d.arguments)&&d.arguments.kind===(d.createSite==='INITIAL'?'BLOCK_POS_I':'DDD_I')&&validPathReferenceFact(d.navigationPath,rev)&&typeof d.returnedMatchesNavigationPath==='boolean'&&consistentRawPathMatch(d.returnedMatchesNavigationPath,d.returnedPath,d.navigationPath)&&Array.isArray(ids)&&ids.length<=8&&ids.every((v,i)=>child(v,d.createInvocationId,'finder')&&(i===0||Number(v.split(':').at(-1))>Number(ids[i-1].split(':').at(-1))))&&typeof d.capturedFinderInvocationsTruncated==='boolean'&&(!d.capturedFinderInvocationsTruncated||ids.length===8)&&d.searchScope==='CAPTURED_ORIGINAL_BASE_NAVIGATION_FINDER_CALLS_ONLY_EMPTY_IS_NOT_NO_SEARCH_PROOF'&&d.returnScope==='ORIGINAL_CREATE_PATH_NORMAL_RETURN_NOT_ADOPTION_OR_ARRIVAL';
 }
 if(kind!=='BRAIN_PATH_FINDER_RETURN')return false;
 return exact(d,[...common,'createInvocationId','createSite','finderInvocationId','finderClass',...(d.targetSetClass==null?[]:['targetSetClass']),'targetContentsStatus',scalarKey(d,'followRange'),'accuracy',scalarKey(d,'maxVisitedNodesMultiplier'),'returnedPath','searchIdStatus',...(d.searchIdStatus==='AVAILABLE'?['searchId']:[]),'returnScope'])&&child(d.finderInvocationId,d.createInvocationId,'finder')&&text(d.finderClass)&&(d.targetSetClass==null||text(d.targetSetClass))&&d.targetContentsStatus==='NOT_EXPOSED'&&finite(d,'followRange')&&integer(d.accuracy)&&finite(d,'maxVisitedNodesMultiplier')&&
   (d.searchIdStatus==='NOT_CAPTURED'?d.searchId===undefined:d.searchIdStatus==='AVAILABLE'&&typeof d.searchId==='string'&&new RegExp('^search:'+rev+':[1-9][0-9]*$').test(d.searchId)&&integer(Number(d.searchId.split(':').at(-1))))&&d.returnScope==='ORIGINAL_NAVIGATION_SOURCE_FINDER_NORMAL_RETURN_NOT_ADOPTION_OR_ARRIVAL';
}
