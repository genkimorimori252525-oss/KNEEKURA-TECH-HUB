import {createHash} from 'node:crypto';
import {validOriginalDecisionEvent} from './original-decision-events.mjs';
import {requireTankIdentity,requireTankObservations,sameTankIdentity,boundedTankPacket} from './tank-contract.mjs';
const safe=Number.isSafeInteger;
const hash=v=>createHash('sha256').update(JSON.stringify(v)).digest('hex');
const metric=(value,rows,limitations=[])=>({status:rows.length?'DERIVED_FROM_RETAINED_SAMPLES':'NOT_CAPTURED',value,
  sourceObservationIds:rows.slice(0,32).map(r=>r.observationId),sourceReferenceCount:rows.length,sourceReferencesOmitted:Math.max(0,rows.length-32),
  sourceObservationIdsHash:hash(rows.map(r=>r.observationId)),observedTick:rows.at(-1)?.gameTime??null,limitations});

/** Input is canonical evidence, never a cursor, bookmark or presentation subset. */
export function buildExperimentDigest({request,actionReceipts=[],observations,identity,window,limits={}}={}) {
  requireTankIdentity(identity);requireTankObservations(observations);
  if(!safe(identity.targetRevision)||identity.targetRevision<1||!Array.isArray(request?.subjects)||request.subjects.length>64
    ||!Array.isArray(request.assertions)||request.assertions.length>128||!Array.isArray(actionReceipts)||actionReceipts.length>128
    ||!safe(window?.startTick)||window.startTick<0||!safe(window?.endTick)||window.endTick<window.startTick||window.endTick-window.startTick>10000)throw new TypeError('BOUNDED_EXPERIMENT_REQUIRED');
  const subject=request.subjects.find(s=>s.uuid===identity.subjectUuid);
  if(!subject||request.subjects.filter(s=>s.uuid===identity.subjectUuid).length!==1)throw new TypeError('REGISTERED_SUBJECT_MAPPING_REQUIRED');
  const interval=limits.observer?.sampleIntervalTicks??1,maxDistance=limits.maxSegmentDistance??16;
  if(!safe(interval)||interval<1||interval>100||!Number.isFinite(maxDistance)||maxDistance<1||maxDistance>256)throw new TypeError('BOUNDED_METRIC_LIMITS');
  const seen=new Set();for(const r of observations){
    if(!sameTankIdentity(r,identity))throw new TypeError('CANONICAL_EXPERIMENT_IDENTITY_MISMATCH');
    if(typeof r?.observationId!=='string'||r.observationId.length>512||seen.has(r.observationId))throw new TypeError('DUPLICATE_OR_INVALID_OBSERVATION_ID');seen.add(r.observationId);
    if(r.kind!=='observation'||!safe(r.gameTime)||r.gameTime<0)throw new TypeError('CANONICAL_EXPERIMENT_OBSERVATION_REQUIRED');
  }
  const inWindow=observations.filter(r=>r.gameTime>=window.startTick&&r.gameTime<=window.endTick);
  const subjectRows=inWindow.filter(r=>r.scope?.kind==='ENTITY_UUID'&&r.scope.entityUuid===identity.subjectUuid
    &&r.source?.side==='SERVER'&&r.payload?.targetRevision===identity.targetRevision).toSorted((a,b)=>a.gameTime-b.gameTime);
  const complete=r=>r.epistemicStatus==='OBSERVED'&&r.completeness?.complete===true;
  const state=subjectRows.filter(r=>r.lane==='SERVER_ENTITY_STATE');
  const position=r=>complete(r)&&r.payload?.alive!==false&&r.payload?.removed!==true&&typeof r.payload.dimension==='string'
    &&['x','y','z'].every(k=>Number.isFinite(r.payload[k])&&Math.abs(r.payload[k])<=30000000);
  const boundaries=subjectRows.filter(r=>(r.lane==='SERVER_ENTITY_STATE'&&!position(r))
    ||(r.lane==='SERVER_TARGET_TRACKED'&&r.payload?.tracked===false)||(r.lane==='AI_DECISION'&&validOriginalDecisionEvent(r)&&r.payload?.kind==='CONTROL_TELEPORT_RETURN'));
  const samples=state.filter(position),gaps=[],used=[],stationary=[];let distance=0,boundaryIndex=0;
  for(let i=1;i<samples.length;i++){
    const a=samples[i-1],b=samples[i],dt=b.gameTime-a.gameTime,d=Math.hypot(...['x','y','z'].map(k=>b.payload[k]-a.payload[k]));
    while(boundaryIndex<boundaries.length&&boundaries[boundaryIndex].gameTime<a.gameTime)boundaryIndex++;
    const intervening=boundaryIndex<boundaries.length&&boundaries[boundaryIndex].gameTime<=b.gameTime;
    if(dt<=0||dt>interval||a.payload.dimension!==b.payload.dimension||d>maxDistance||intervening){gaps.push({afterTick:a.gameTime,beforeTick:b.gameTime,sourceObservationIds:[a.observationId,b.observationId],reason:dt<=0?'AMBIGUOUS_SAME_TICK':dt>interval?'SAMPLING_GAP':intervening?'TERMINAL_MISSING_OR_TELEPORT_BOUNDARY':a.payload.dimension!==b.payload.dimension?'DIMENSION_BOUNDARY':'DISTANCE_THRESHOLD_NOT_PROOF_OF_TELEPORT'});continue;}
    distance+=d;used.push(a,b);if(d===0)stationary.push({startTick:a.gameTime,endTick:b.gameTime,sourceObservationIds:[a.observationId,b.observationId]});
  }
  const events=subjectRows.filter(r=>complete(r)&&validOriginalDecisionEvent(r));
  const kinds=['CONTROL_PROJECTILE_SPAWN_RETURN','CONTROL_PROJECTILE_HIT_RETURN','CONTROL_PROJECTILE_HURT_RETURN'];
  const eventCounts=Object.fromEntries(kinds.map(kind=>[kind,metric(events.filter(r=>r.payload.kind===kind).length,events.filter(r=>r.payload.kind===kind),['RETAINED_VALID_CALLBACKS_NOT_ALL_ATTACKS_OR_SUCCESSFUL_HITS'])]));
  const arrivalAssertions=request.assertions.filter(a=>a.kind==='structured'&&a.subject_id===subject.subject_id&&a.field==='position'&&a.operator==='equals'
    &&Array.isArray(a.expected)&&a.expected.length===3&&a.expected.every(Number.isFinite));
  const arrivals=arrivalAssertions.map(a=>{
    const index=samples.findIndex(r=>['x','y','z'].every((k,i)=>r.payload[k]===a.expected[i])),found=samples[index],prior=index>0?samples[index-1]:null;
    return {assertionId:a.assertion_id,status:found?'RECORDED_POSITION_MATCH':'NOT_CAPTURED',observedInterval:found?{afterTick:prior?.gameTime??null,atOrBeforeTick:found.gameTime}:null,
      sourceObservationIds:found?[...(prior?[prior.observationId]:[]),found.observationId]:[],limitations:['MATCHED_ORIGINAL_SAMPLE_NOT_CONTINUOUS_ARRIVAL_OR_ASSERTION_PASS']};
  });
  const health=limits.health??{},startCaptured=samples.some(r=>r.gameTime===window.startTick),endCaptured=samples.some(r=>r.gameTime===window.endTick);
  const expectedSamples=Math.floor((window.endTick-window.startTick)/interval)+1;
  const knownHealth=['dropped','errors','trailingPartialFiles','partialCaptures'].every(k=>safe(health[k])&&health[k]===0);
  const samplingComplete=startCaptured&&endCaptured&&samples.length===expectedSamples&&!gaps.length&&state.length===samples.length&&knownHealth
    &&limits.sourceBinding?.verifiedCanonical===true&&limits.observer?.sampleIntervalTicks===interval;
  const conditions={baselineHash:request.arena?.baseline_hash??null,fixtureHash:limits.worldBinding?.fixtureHash??null,
    worldBinding:limits.worldBinding??null,sourceBinding:request.target??null,
    subject:{subjectId:subject.subject_id??null,entityType:subject.entity_type??null,uuid:subject.uuid},
    observer:limits.observer??null,presentation:limits.presentation??null,alignment:limits.alignment??null,
    initialState:request.initial_state??null,actions:request.actions??null,assertions:request.assertions,
    windowDurationTicks:window.endTick-window.startTick};
  for(const r of actionReceipts)if(typeof r?.action_id!=='string'||!['ACCEPTED','REQUESTED','APPLIED','VERIFIED','REJECTED','FAILED','NOT_RUN','UNKNOWN'].includes(r.status))throw new TypeError('ACTION_RECEIPT_STATUS_REQUIRED');
  return boundedTankPacket({schema:'kneekura.experiment-digest/v1',identity:structuredClone(identity),question:request.question??request.experiment_id,
    registeredAssertions:request.assertions.map(a=>({assertion_id:a.assertion_id,status:'INCONCLUSIVE',registered:a,evidenceRefs:[],limitations:['REGISTERED_ASSERTION_EVALUATION_REQUIRED_NOT_INFERRED_FROM_DISTANCE']})),
    conditions,actions:structuredClone(actionReceipts),executionEffect:'NOT_ESTABLISHED',
    metrics:{positionSamples:metric(samples.length,samples),observedDistance:metric(samples.length?distance:null,[...new Set(used)],['POINT_TO_POINT_SUM_ONLY_NOT_CONTINUOUS_PATH']),
      sameCoordinateIntervals:metric({totalObservedTicks:stationary.reduce((s,i)=>s+i.endTick-i.startTick,0),intervals:stationary},samples,['SAME_RECORDED_COORDINATES_NOT_CONTINUOUS_STOP_OR_CAUSE']),
      arrival:{status:arrivals.some(a=>a.status==='RECORDED_POSITION_MATCH')?'DERIVED_FROM_RETAINED_SAMPLES':'NOT_CAPTURED',value:arrivals.length?arrivals:null,
        sourceObservationIds:arrivals.flatMap(a=>a.sourceObservationIds),observedTick:null,limitations:['ONLY_EXACT_REGISTERED_POSITION_EQUALS_TARGETS_NO_INFERRED_DESTINATION']},
      retainedEventCounts:eventCounts,attackCount:{status:'NOT_EXPOSED',value:null,sourceObservationIds:[],observedTick:null,limitations:['PROJECTILE_CALLBACK_IS_NOT_AN_ATTACK_COUNT']}},
    quality:{status:samplingComplete?'SAMPLING_GRID_COMPLETE':'INCONCLUSIVE',coverage:{requestedWindow:window,observedWindow:samples.length?{startTick:samples[0].gameTime,endTick:samples.at(-1).gameTime}:null,
      capturedCount:inWindow.length,eligibleCount:samples.length,expectedSampleCount:expectedSamples,samplingIntervalTicks:interval,intervalSource:limits.observer?'EXPLICIT_PROFILE':'CONSERVATIVE_DEFAULT_NOT_VERIFIED_PROFILE',startCaptured,endCaptured,gapCount:gaps.length,gaps,
      health:structuredClone(health),sourceBinding:limits.sourceBinding??null,continuousCoverage:'NOT_ESTABLISHED',allEventsCaptured:'NOT_ESTABLISHED'}},
    retainedEvents:events.map(r=>({observationId:r.observationId,tick:r.gameTime,kind:r.payload.kind,evidenceRefs:[r.observationId],imageStatus:'NOT_CAPTURED'})),
    cleanup:limits.cleanup??'UNKNOWN',evidenceRefs:{identity:requireTankIdentity(identity),sourceObservationCount:subjectRows.length,
      sourceObservationIds:subjectRows.slice(0,32).map(r=>r.observationId),omittedReferenceCount:Math.max(0,subjectRows.length-32),canonicalBinding:limits.sourceBinding??null},
    semantics:{displaySelectionAffectsMetrics:false,readOnlyRetainedEvidence:true,temporalAdjacencyProvesCausality:false}});
}
