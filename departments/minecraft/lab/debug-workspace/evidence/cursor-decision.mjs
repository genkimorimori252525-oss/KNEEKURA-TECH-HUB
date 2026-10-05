import {buildRetainedDecisionPresentation} from './decision-presentation.mjs';
import {requireTankIdentity,requireTankObservations,sameTankIdentity,boundedTankPacket} from './tank-contract.mjs';

export function buildCursorDecisionPacket({observations,identity,subjectUuid,window,cursorTick,maxGapTicks=10}={}) {
  requireTankIdentity(identity);requireTankObservations(observations);
  if(!window||!Number.isSafeInteger(window.startTick)||!Number.isSafeInteger(window.endTick)
      ||!Number.isSafeInteger(cursorTick)||cursorTick<window.startTick||cursorTick>window.endTick)throw new TypeError('BOUNDED_CURSOR_REQUIRED');
  const request={startTick:window.startTick,endTick:cursorTick,maxGapTicks};
  const view=buildRetainedDecisionPresentation({observations,identity,subjectUuid,request});
  const source=new Map(observations.filter(r=>sameTankIdentity(r,identity)&&r.gameTime<=cursorTick).map(r=>[r.observationId,r]));
  for(const stage of Object.values(view.overview.stages))for(const fact of stage.facts) {
    const ticks=fact.source_observation_ids.map(id=>source.get(id)?.gameTime).filter(Number.isSafeInteger);
    fact.observedTick=ticks.length?Math.max(...ticks):null;
    fact.ageTicks=fact.observedTick===null?null:cursorTick-fact.observedTick;
    fact.tickSemantics='ORIGINAL_RETAINED_SOURCE_NOT_CURSOR_OBSERVATION';
  }
  const eligible=observations.filter(r=>sameTankIdentity(r,identity)&&r.kind==='observation'&&r.lane==='SERVER_ENTITY_STATE'
    &&r.source?.side==='SERVER'&&r.scope?.entityUuid===subjectUuid&&r.payload?.targetRevision===identity.targetRevision
    &&r.epistemicStatus==='OBSERVED'&&r.completeness?.complete===true&&r.gameTime>=window.startTick&&r.gameTime<=cursorTick
    &&r.payload.alive!==false&&r.payload.removed!==true&&['x','y','z'].every(k=>Number.isFinite(r.payload[k]))).length;
  const shown=view.layers.motion.trace.samples.length;
  const dimensions=new Set(observations.filter(r=>sameTankIdentity(r,identity)&&r.scope?.entityUuid===subjectUuid
    &&r.source?.side==='SERVER'&&r.payload?.targetRevision===identity.targetRevision&&r.gameTime>=window.startTick&&r.gameTime<=cursorTick)
    .map(r=>r.payload?.dimension).filter(d=>typeof d==='string'));
  for(const d of [view.layers.returnedPath.data?.dimension,view.layers.terrain.data?.dimension])if(typeof d==='string')dimensions.add(d);
  return boundedTankPacket({schema:'kneekura.cursor-decision/v1',identity:{...view.identity},cursorTick,window:structuredClone(window),
    dimension:dimensions.size===1?[...dimensions][0]:null,overview:view.overview,layers:view.layers,quality:{status:'RETAINED_SAMPLES_ONLY',gaps:view.layers.motion.trace.gaps,
      gapScope:'DISPLAYED_SUBSET_NOT_COMPLETE_WINDOW',continuousCoverage:'NOT_ESTABLISHED'},
    displaySelection:{motion:{eligibleCount:eligible,displayedCount:shown,omittedCount:eligible-shown,selectionPolicy:'LATEST_128_REAL_SAMPLES'}},
    evidenceRefs:[...new Set(view.layers.motion.trace.source_observation_ids??[])],
    semantics:{futureEvidenceIncluded:false,metricsMustUseCanonicalEvidence:true,readOnlyRetainedEvidence:true}});
}

export function selectTankCursorTicks({observations,identity,subjectUuid,window,maxCursors=32}) {
  requireTankIdentity(identity);requireTankObservations(observations);
  if(!Number.isSafeInteger(maxCursors)||maxCursors<2||maxCursors>256||!Number.isSafeInteger(window?.startTick)
      ||!Number.isSafeInteger(window?.endTick)||window.startTick<0||window.endTick<window.startTick||window.endTick-window.startTick>10000)throw new TypeError('TANK_CURSOR_SELECTION_BOUND');
  const eligible=[...new Set([window.startTick,window.endTick,...observations.filter(r=>sameTankIdentity(r,identity)
    &&r.scope?.entityUuid===subjectUuid&&r.payload?.targetRevision===identity.targetRevision&&r.epistemicStatus==='OBSERVED'
    &&r.completeness?.complete===true&&Number.isSafeInteger(r.gameTime)&&r.gameTime>=window.startTick&&r.gameTime<=window.endTick).map(r=>r.gameTime)])].toSorted((a,b)=>a-b);
  const ticks=eligible.length<=maxCursors?eligible:Array.from({length:maxCursors},(_,i)=>eligible[Math.round(i*(eligible.length-1)/(maxCursors-1))]);
  return {ticks,eligibleCount:eligible.length,displayedCount:ticks.length,omittedCount:eligible.length-ticks.length,
    selectionPolicy:'EVENLY_SELECTED_RETAINED_TICKS_AND_REQUESTED_ENDPOINTS',endpointsAreCursorBoundsNotObservations:true};
}
