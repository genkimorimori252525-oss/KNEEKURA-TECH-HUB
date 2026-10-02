export const SAMPLED_MOTION_TRACE_VERSION=1;
export const SAMPLED_MOTION_TRACE_EPISTEMIC='DERIVED_FROM_SAMPLED_OBSERVATIONS';
export const SAMPLED_SEGMENT_SEMANTICS='SAMPLED_ENDPOINT_CONNECTION';
export const DISPLAY_DERIVED_CONTINUITY='DISPLAY_DERIVED';
export const MOTION_TRACE_CLASSES=Object.freeze(['MOB_ACTUAL','PROJECTILE_ACTUAL','NAVIGATION_DECLARED']);
export const MOTION_TRACE_GAP_REASONS=Object.freeze([
  'SOURCE_GAP_EXCEEDED','DIMENSION_CHANGED','RUN_IDENTITY_CHANGED',
  'PROCESS_EPOCH_CHANGED','ARENA_EPOCH_CHANGED','RESOURCE_EPOCH_CHANGED',
  'ENTITY_UNAVAILABLE','EXPLICIT_TELEPORT','RESET_BOUNDARY',
  'SOURCE_CONTINUITY_NOT_RETAINED'
]);

const obj=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
const finite=v=>typeof v==='number'&&Number.isFinite(v);
const copy=v=>v==null?v:structuredClone(v);
function str(v,n,nullable=false){
  if(nullable&&v==null)return null;
  if(typeof v!=='string'||!v.trim())throw new TypeError(n+' must be a non-empty string');
  return v.trim();
}
function tick(v,n='tick'){
  if(!Number.isSafeInteger(v)||v<0)throw new TypeError(n+' must be a safe integer >= 0');
  return v;
}
function vec(v,n){
  if(!Array.isArray(v)||v.length!==3||!v.every(finite))throw new TypeError(n+' must be finite [x,y,z]');
  return [...v];
}
function sameRun(a,b){
  return a.debugSessionId===b.debugSessionId&&a.runId===b.runId&&
    (a.runSnapshotId??null)===(b.runSnapshotId??null);
}
function dist(a,b){return Math.hypot(b.position[0]-a.position[0],b.position[1]-a.position[1],b.position[2]-a.position[2]);}
function markerBetween(m,a,b){return Number.isSafeInteger(m.tick)&&m.tick>a.tick&&m.tick<=b.tick;}
function boundary(a,b,markers,max){
  if(b.tick<=a.tick)return 'SOURCE_CONTINUITY_NOT_RETAINED';
  if(!sameRun(a.identity,b.identity))return 'RUN_IDENTITY_CHANGED';
  if(a.identity.processEpoch!==b.identity.processEpoch)return 'PROCESS_EPOCH_CHANGED';
  if(a.identity.arenaEpoch!==b.identity.arenaEpoch)return 'ARENA_EPOCH_CHANGED';
  if(a.identity.resourceEpoch!==b.identity.resourceEpoch)return 'RESOURCE_EPOCH_CHANGED';
  if((a.identity.dimension??null)!==(b.identity.dimension??null))return 'DIMENSION_CHANGED';
  const m=markers.find(x=>markerBetween(x,a,b));
  if(m)return m.reason;
  return b.tick-a.tick>max?'SOURCE_GAP_EXCEEDED':null;
}
function normalizeMarker(m,i){
  if(!obj(m))throw new TypeError('discontinuity marker must be an object');
  const reason=str(m.reason,'marker.reason');
  if(!MOTION_TRACE_GAP_REASONS.includes(reason))throw new TypeError('unsupported gap reason: '+reason);
  return {markerId:m.markerId==null?'marker:'+i:str(m.markerId,'marker.markerId'),
    tick:tick(m.tick,'marker.tick'),reason,sourceId:str(m.sourceId,'marker.sourceId',true),
    detail:m.detail==null?null:copy(m.detail)};
}
export function normalizeMotionSample(s,i=0){
  if(!obj(s)||!obj(s.identity)||!obj(s.source))throw new TypeError('motion sample identity/source must be objects');
  const id=s.identity,sourceId=str(s.source.sourceId,'sample.source.sourceId');
  return {
    sampleId:s.sampleId==null?'sample:'+sourceId:str(s.sampleId,'sample.sampleId'),
    tick:tick(s.tick,'sample.tick'),observedAt:str(s.observedAt,'sample.observedAt',true),
    position:vec(s.position,'sample.position'),velocity:s.velocity==null?null:vec(s.velocity,'sample.velocity'),
    identity:{debugSessionId:str(id.debugSessionId,'identity.debugSessionId'),runId:str(id.runId,'identity.runId'),
      runSnapshotId:str(id.runSnapshotId,'identity.runSnapshotId',true),processEpoch:tick(id.processEpoch,'identity.processEpoch'),
      arenaEpoch:tick(id.arenaEpoch,'identity.arenaEpoch'),resourceEpoch:tick(id.resourceEpoch,'identity.resourceEpoch'),
      dimension:str(id.dimension,'identity.dimension',true)},
    source:{sourceId,kind:str(s.source.kind,'sample.source.kind'),lane:str(s.source.lane,'sample.source.lane',true),
      side:str(s.source.side,'sample.source.side',true),method:str(s.source.method,'sample.source.method',true),
      writerId:str(s.source.writerId,'sample.source.writerId',true),
      writerSeq:s.source.writerSeq==null?null:tick(s.source.writerSeq,'sample.source.writerSeq'),
      epistemicStatus:str(s.source.epistemicStatus,'sample.source.epistemicStatus',true),
      completeness:s.source.completeness==null?null:copy(s.source.completeness)},ordinal:i};
}
function metrics(samples,segments,gaps){
  const counts={};for(const g of gaps)counts[g.reason]=(counts[g.reason]||0)+1;
  if(!samples.length)return {sampleCount:0,segmentCount:0,firstTick:null,lastTick:null,durationTicks:0,
    netDisplacement:null,sampledPolylineLength:0,minAltitude:null,maxAltitude:null,directlyObservedSpeed:null,
    gapCount:gaps.length,gapReasons:counts};
  const first=samples[0],last=samples.at(-1),speeds=samples.filter(s=>s.velocity).map(s=>Math.hypot(...s.velocity));
  return {sampleCount:samples.length,segmentCount:segments.length,firstTick:first.tick,lastTick:last.tick,
    durationTicks:last.tick-first.tick,netDisplacement:dist(first,last),netDisplacementSemantics:'ENDPOINT_DISTANCE_ONLY',
    sampledPolylineLength:segments.reduce((n,s)=>n+s.distance,0),
    sampledPolylineSemantics:'SUM_OF_CONNECTED_SAMPLED_ENDPOINT_SEGMENTS',
    minAltitude:Math.min(...samples.map(s=>s.position[1])),maxAltitude:Math.max(...samples.map(s=>s.position[1])),
    directlyObservedSpeed:speeds.length?{sampleCount:speeds.length,min:Math.min(...speeds),max:Math.max(...speeds),
      mean:speeds.reduce((a,b)=>a+b,0)/speeds.length,semantics:'DIRECTLY_OBSERVED_VELOCITY_MAGNITUDE'}:null,
    gapCount:gaps.length,gapReasons:counts};
}
export function buildSampledMotionTrace(input){
  if(!obj(input)||!obj(input.subject))throw new TypeError('motion trace input/subject must be objects');
  const traceClass=str(input.traceClass,'traceClass');
  if(!MOTION_TRACE_CLASSES.includes(traceClass))throw new TypeError('unsupported motion trace class: '+traceClass);
  const entityUuid=str(input.subject.entityUuid,'subject.entityUuid');
  const entityType=str(input.subject.entityType,'subject.entityType',true);
  const max=input.maxContinuityTicks==null?100:tick(input.maxContinuityTicks,'maxContinuityTicks');
  if(max<1)throw new TypeError('maxContinuityTicks must be >= 1');
  if(!Array.isArray(input.samples||[])||(input.samples||[]).length>4096)throw new TypeError('samples must be an array of at most 4096');
  if(!Array.isArray(input.discontinuities||[])||(input.discontinuities||[]).length>1024)throw new TypeError('discontinuities must be an array of at most 1024');
  const samples=(input.samples||[]).map(normalizeMotionSample).sort((a,b)=>a.tick-b.tick||a.ordinal-b.ordinal);
  const ids=new Set();for(const s of samples){if(ids.has(s.sampleId))throw new TypeError('duplicate sample id: '+s.sampleId);ids.add(s.sampleId);}
  const markers=(input.discontinuities||[]).map(normalizeMarker).sort((a,b)=>a.tick-b.tick||a.markerId.localeCompare(b.markerId));
  const segments=[],gaps=[];
  for(let i=1;i<samples.length;i++){
    const a=samples[i-1],b=samples[i],reason=boundary(a,b,markers,max);
    if(reason){
      const m=markers.find(x=>x.reason===reason&&markerBetween(x,a,b));
      gaps.push({gapId:'gap:'+gaps.length,fromSampleId:a.sampleId,toSampleId:b.sampleId,fromTick:a.tick,toTick:b.tick,
        reason,markerId:m?.markerId??null,sourceId:m?.sourceId??null,detail:m?.detail??null});
    }else segments.push({segmentId:'segment:'+segments.length,fromSampleId:a.sampleId,toSampleId:b.sampleId,
      fromTick:a.tick,toTick:b.tick,elapsedTicks:b.tick-a.tick,distance:dist(a,b),
      semantics:SAMPLED_SEGMENT_SEMANTICS,continuity:DISPLAY_DERIVED_CONTINUITY});
  }
  for(const m of markers){
    if(gaps.some(g=>g.markerId===m.markerId))continue;
    const prev=[...samples].reverse().find(s=>s.tick<=m.tick),next=samples.find(s=>s.tick>m.tick);
    gaps.push({gapId:'gap:'+gaps.length,fromSampleId:prev?.sampleId??null,toSampleId:next?.sampleId??null,
      fromTick:prev?.tick??null,toTick:next?.tick??null,reason:m.reason,markerId:m.markerId,sourceId:m.sourceId,detail:m.detail});
  }
  const sourceIds=[...new Set(samples.map(s=>s.source.sourceId))];
  for(const m of markers)if(m.sourceId&&!sourceIds.includes(m.sourceId))sourceIds.push(m.sourceId);
  const trace={schema:'kneekura.sampled_motion_trace',version:1,kind:'SampledMotionTrace',
    epistemicLabel:SAMPLED_MOTION_TRACE_EPISTEMIC,traceClass,subject:{entityUuid,entityType},
    request:{startTick:input.startTick==null?null:tick(input.startTick,'startTick'),
      endTick:input.endTick==null?null:tick(input.endTick,'endTick'),maxContinuityTicks:max},
    sourcePolicy:{sourceOfTruth:str(input.sourceOfTruth||'RETAINED_POSITION_OBSERVATIONS','sourceOfTruth'),
      continuousPathClaimed:false,interpolationClaimed:false,segmentSemantics:SAMPLED_SEGMENT_SEMANTICS,
      continuity:DISPLAY_DERIVED_CONTINUITY},
    samples:samples.map(({ordinal,...s})=>s),segments,gaps,metrics:metrics(samples,segments,gaps),
    provenance:{sourceIds,sourceCount:sourceIds.length},
    limitations:['Segments connect retained sampled endpoints for presentation only.',
      'No segment proves the exact continuous path between samples.',...(input.limitations||[])]};
  return assertValidSampledMotionTrace(trace);
}
function num(p,k){if(!finite(p?.[k]))throw new TypeError('SERVER_ENTITY_STATE payload missing finite '+k);return p[k];}
function exactRun(r,q){
  return (q.debugSessionId==null||r.debugSessionId===q.debugSessionId)&&(q.runId==null||r.runId===q.runId)&&
    (!Object.hasOwn(q,'runSnapshotId')||(r.runSnapshotId??null)===(q.runSnapshotId??null));
}
function stateSample(r){
  const p=r.payload,v=['vx','vy','vz'].every(k=>finite(p?.[k]))?[p.vx,p.vy,p.vz]:null;
  return normalizeMotionSample({sampleId:'sample:'+r.observationId,tick:tick(r.gameTime,'observation.gameTime'),
    observedAt:r.observedAt??null,position:[num(p,'x'),num(p,'y'),num(p,'z')],velocity:v,
    identity:{debugSessionId:r.debugSessionId,runId:r.runId,runSnapshotId:r.runSnapshotId??null,
      processEpoch:r.processEpoch,arenaEpoch:r.arenaEpoch,resourceEpoch:r.resourceEpoch,dimension:p?.dimension??null},
    source:{sourceId:r.observationId,kind:'DEBUG_WORKSPACE_OBSERVATION',lane:r.lane,side:r.source?.side??null,
      method:r.source?.method??null,writerId:r.writerId??null,writerSeq:r.writerSeq??null,
      epistemicStatus:r.epistemicStatus??null,completeness:r.completeness??null}});
}
function markers(rows,uuid,start,end){
  const out=[];
  for(const r of rows){
    if(!Number.isSafeInteger(r.gameTime)||r.gameTime<start||r.gameTime>end)continue;
    if(r.lane==='SERVER_TARGET_TRACKED'&&r.scope?.kind==='ENTITY_UUID'&&r.scope.entityUuid===uuid&&r.payload?.tracked===false)
      out.push({markerId:'marker:unavailable:'+r.observationId,tick:r.gameTime,reason:'ENTITY_UNAVAILABLE',
        sourceId:r.observationId,detail:{reason:r.payload?.reason??null}});
    else if(r.lane==='ACTION_APPLIED'&&r.payload?.subjectUuid===uuid&&r.payload?.measuredPose!=null)
      out.push({markerId:'marker:teleport:'+r.observationId,tick:r.gameTime,reason:'EXPLICIT_TELEPORT',
        sourceId:r.observationId,detail:{actionId:r.payload?.actionId??null,measuredPose:copy(r.payload.measuredPose)}});
    else if(r.lane==='ARENA_RESET')
      out.push({markerId:'marker:reset:'+r.observationId,tick:r.gameTime,reason:'RESET_BOUNDARY',
        sourceId:r.observationId,detail:{arenaId:r.payload?.arenaId??null,beforeEpoch:r.payload?.beforeEpoch??null,afterEpoch:r.payload?.afterEpoch??null}});
  }return out;
}
function observedType(rows,uuid){
  return rows.find(r=>r.lane==='SERVER_TARGET_TRACKED'&&r.scope?.kind==='ENTITY_UUID'&&
    r.scope.entityUuid===uuid&&r.payload?.tracked===true&&typeof r.payload?.type==='string')?.payload.type??null;
}
export function extractSampledMotionTraceFromObservations(observations,request){
  if(!Array.isArray(observations)||!obj(request))throw new TypeError('observations/request invalid');
  const uuid=str(request.entityUuid,'request.entityUuid'),traceClass=str(request.traceClass||'MOB_ACTUAL','request.traceClass');
  if(!['MOB_ACTUAL','PROJECTILE_ACTUAL'].includes(traceClass))
    throw new TypeError('SERVER_ENTITY_STATE extraction supports MOB_ACTUAL or PROJECTILE_ACTUAL');
  const start=request.startTick==null?0:tick(request.startTick,'request.startTick');
  const end=request.endTick==null?Number.MAX_SAFE_INTEGER:tick(request.endTick,'request.endTick');
  if(end<start)throw new TypeError('request.endTick precedes startTick');
  const rows=observations.filter(r=>exactRun(r,request));
  const samples=rows.filter(r=>r.lane==='SERVER_ENTITY_STATE'&&r.scope?.kind==='ENTITY_UUID'&&
    r.scope.entityUuid===uuid&&Number.isSafeInteger(r.gameTime)&&r.gameTime>=start&&r.gameTime<=end).map(stateSample);
  return buildSampledMotionTrace({traceClass,subject:{entityUuid:uuid,entityType:request.entityType??observedType(rows,uuid)},
    startTick:start,endTick:end===Number.MAX_SAFE_INTEGER?null:end,maxContinuityTicks:request.maxContinuityTicks??100,
    sourceOfTruth:'DEBUG_WORKSPACE_SERVER_ENTITY_STATE',samples,discontinuities:markers(rows,uuid,start,end),
    limitations:['Debug Workspace SERVER_ENTITY_STATE is sampled every five server ticks and delta/keyframe retained.',
      'Absence between retained rows is not converted into invented intermediate positions.']});
}
export async function extractSampledMotionTraceFromEvidenceStore(store,request){
  if(!store||typeof store.readObservations!=='function')throw new TypeError('store.readObservations() is required');
  return extractSampledMotionTraceFromObservations(await store.readObservations(),request);
}
export function assertValidSampledMotionTrace(trace){
  if(!obj(trace)||trace.schema!=='kneekura.sampled_motion_trace'||trace.version!==1||trace.kind!=='SampledMotionTrace')
    throw new TypeError('motion trace contract mismatch');
  if(trace.epistemicLabel!==SAMPLED_MOTION_TRACE_EPISTEMIC||!MOTION_TRACE_CLASSES.includes(trace.traceClass))
    throw new TypeError('motion trace epistemic/class mismatch');
  str(trace.subject?.entityUuid,'trace.subject.entityUuid');
  if(!Array.isArray(trace.samples)||!Array.isArray(trace.segments)||!Array.isArray(trace.gaps))
    throw new TypeError('trace samples/segments/gaps must be arrays');
  const byId=new Map();
  for(const s of trace.samples){const n=normalizeMotionSample(s);if(byId.has(n.sampleId))throw new TypeError('duplicate trace sample id');byId.set(n.sampleId,n);}
  for(const s of trace.segments){
    if(s.semantics!==SAMPLED_SEGMENT_SEMANTICS||s.continuity!==DISPLAY_DERIVED_CONTINUITY)
      throw new TypeError('segment semantics/continuity invalid');
    const a=byId.get(s.fromSampleId),b=byId.get(s.toSampleId);
    if(!a||!b)throw new TypeError('segment references missing sample endpoint');
    if(s.fromTick!==a.tick||s.toTick!==b.tick||s.elapsedTicks!==b.tick-a.tick||!finite(s.distance)||s.distance<0)
      throw new TypeError('segment endpoint metrics invalid');
  }
  for(const g of trace.gaps){
    if(!MOTION_TRACE_GAP_REASONS.includes(g.reason))throw new TypeError('gap reason invalid');
    if(g.fromSampleId!=null&&!byId.has(g.fromSampleId))throw new TypeError('gap references missing fromSampleId');
    if(g.toSampleId!=null&&!byId.has(g.toSampleId))throw new TypeError('gap references missing toSampleId');
  }
  if(trace.sourcePolicy?.continuousPathClaimed!==false||trace.sourcePolicy?.interpolationClaimed!==false)
    throw new TypeError('sampled motion trace may not claim exact continuous path');
  return trace;
}
