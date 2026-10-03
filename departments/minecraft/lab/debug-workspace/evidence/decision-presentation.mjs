import {DECISION_OBSERVATION_V1} from './decision-observation.mjs';
import {selectDecisionRecords,observeDebugWorkspaceDecision,buildDebugWorkspaceMotionTrace,buildDebugWorkspaceRelatedProjectileTraces,validDecisionSnapshot} from './debug-workspace-decision-adapter.mjs';
import {queryDecisionDrilldown} from './decision-drilldown.mjs';

const bytes=value=>Buffer.byteLength(JSON.stringify(value)??'null');
function integer(value,min,max,name) {
  if(!Number.isSafeInteger(value)||value<min||value>max)throw new TypeError('BOUNDED_'+name+'_REQUIRED');
  return value;
}
function compact(value,max=512) {
  return bytes(value)<=max?structuredClone(value):null;
}
function evidenceRefs(ids=[]) {
  if(ids.some(id=>typeof id!=='string'||id.length>512))throw new TypeError('BOUNDED_SOURCE_REFERENCE_REQUIRED');
  return {source_observation_ids:ids.slice(-4),sourceReferencesTruncated:ids.length>4};
}

/** Latest distinct facts, not a replacement for the retained detailed evidence. */
export function buildDecisionOverviewPacket(observation,{factLimit=4,timelineLimit=32}={}) {
  if(observation?.schema!==DECISION_OBSERVATION_V1.observationSchema)throw new TypeError('DECISION_OBSERVATION_REQUIRED');
  integer(factLimit,1,8,'FACT_LIMIT');integer(timelineLimit,0,64,'TIMELINE_LIMIT');
  const stages={};
  for(const name of DECISION_OBSERVATION_V1.stages) {
    const stage=observation.stages[name],latest=new Map();
    for(const fact of stage?.facts??[]) {
      const key=JSON.stringify([fact.adapter_namespace,fact.key]);latest.delete(key);latest.set(key,fact);
    }
    stages[name]={status:stage?.status??'NOT_CAPTURED',totalObservedFacts:stage?.facts.length??0,
      totalDistinctFactKeys:latest.size,factsTruncated:latest.size>factLimit,
      facts:[...latest.values()].slice(-factLimit).map(fact=>{
        const value=compact(fact.value);
        return {key:fact.key,adapter_namespace:fact.adapter_namespace,value,
          valuePresentationStatus:value===null&&fact.value!==null?'OMITTED_BYTE_BUDGET':'RETAINED',
          epistemic_status:fact.epistemic_status,causal_relation:fact.causal_relation,...evidenceRefs(fact.source_observation_ids)};
      })};
  }
  const packet={schema:'kneekura.decision-overview/v1',identity:structuredClone(observation.identity),
    subject:structuredClone(observation.subject),stages,
    timeline:observation.timeline.slice(observation.timeline.length-timelineLimit).map(event=>({tick:event.tick,
      stage:event.stage,kind:event.kind,summary:compact(event.summary),epistemic_status:event.epistemic_status,
      causal_relation:event.causal_relation,...evidenceRefs(event.source_observation_ids)})),
    timelineTruncated:observation.timeline.length>timelineLimit,
    semantics:{readOnlyRetainedEvidence:true,latestDistinctFactsOnly:true,temporalAdjacencyProvesCausality:false}};
  if(bytes(packet)>65536)throw new RangeError('DECISION_OVERVIEW_BYTE_BUDGET_EXCEEDED');
  return packet;
}

export function buildRetainedDecisionPresentation({observations,subjectUuid,identity,request}={}) {
  const allowed=['startTick','endTick','maxSamples','maxNodes','maxGapTicks','maxSegmentDistance','factLimit','timelineLimit'];
  if(!request||Object.keys(request).some(k=>!allowed.includes(k)))throw new TypeError('BOUNDED_PRESENTATION_REQUEST_REQUIRED');
  const limits={maxSamples:integer(request.maxSamples??128,1,128,'SAMPLES'),maxNodes:integer(request.maxNodes??64,1,64,'NODES'),
    maxGapTicks:integer(request.maxGapTicks??10,1,100,'GAP'),maxSegmentDistance:integer(request.maxSegmentDistance??16,1,256,'DISTANCE'),
    factLimit:integer(request.factLimit??4,1,8,'FACT_LIMIT'),timelineLimit:integer(request.timelineLimit??32,1,64,'TIMELINE_LIMIT')};
  const query=channel=>({channel,startTick:request.startTick,endTick:request.endTick,limit:1,maxNodes:limits.maxNodes,maxGapTicks:limits.maxGapTicks});
  // Reuse the strict full identity/window/input bounds and duplicate-ID refusal.
  queryDecisionDrilldown({observations,subjectUuid,identity,request:query('path_search')});
  const records=selectDecisionRecords(observations.filter(r=>r?.source?.side==='SERVER'&&r.payload?.targetRevision===identity.targetRevision),
    subjectUuid,identity,request.endTick).filter(r=>r.gameTime>=request.startTick);
  const path=queryDecisionDrilldown({observations:records,subjectUuid,identity,request:query('path_search')}).items.at(-1);
  const terrain=queryDecisionDrilldown({observations:records,subjectUuid,identity,request:query('terrain_ground')}).items.at(-1);
  const dimensions=new Set(records.map(r=>r.payload?.dimension).filter(d=>typeof d==='string'));
  if(terrain?.data.dimension)dimensions.add(terrain.data.dimension);
  if(dimensions.size>1)throw new Error('DECISION_PRESENTATION_DIMENSION_BOUNDARY: narrow the retained window');
  const state=records.filter(r=>r.lane==='SERVER_ENTITY_STATE');
  const hasPosition=r=>r.payload.alive!==false&&r.payload.removed!==true&&['x','y','z'].every(k=>Number.isFinite(r.payload[k]));
  const valid=state.filter(hasPosition),retained=valid.slice(-limits.maxSamples),discontinuities=[];
  for(let i=1;i<retained.length;i++) {
    const a=retained[i-1],b=retained[i],absent=records.find(r=>r.lane==='SERVER_TARGET_TRACKED'&&r.payload?.tracked===false&&r.gameTime>a.gameTime&&r.gameTime<b.gameTime),
      missing=state.find(r=>r.gameTime>a.gameTime&&r.gameTime<b.gameTime&&!hasPosition(r));
    const distance=Math.hypot(...['x','y','z'].map(k=>b.payload[k]-a.payload[k]));
    if(absent||missing||distance>limits.maxSegmentDistance)discontinuities.push({after_tick:a.gameTime,before_tick:b.gameTime,
      kind:absent?'MISSING_SELECTED_ENTITY':missing?'MISSING_RETAINED_POSITION':'DERIVED_DISTANCE_THRESHOLD_BREAK',source_observation_id:absent?.observationId??missing?.observationId??b.observationId});
  }
  const trace=buildDebugWorkspaceMotionTrace({observations:[...retained,...records.filter(r=>r.lane!=='SERVER_ENTITY_STATE')],subjectUuid,identity,window:request,
    maxSamples:limits.maxSamples,maxGapTicks:limits.maxGapTicks,explicitDiscontinuities:discontinuities});
  const snapshot=records.filter(r=>r.lane==='AI_DECISION'&&validDecisionSnapshot(r.payload)).at(-1);
  const navigation=snapshot?.payload.sections.navigation_path;
  const navData=navigation?.data,navEntries=navData?.entries;
  const validNav=navigation?.status==='AVAILABLE'&&navData?.pathPresent===true&&Array.isArray(navEntries)&&
    navEntries.length<=64&&navEntries.every(n=>Number.isSafeInteger(n.index)&&['x','y','z'].every(k=>Number.isFinite(n[k])));
  const overview=buildDecisionOverviewPacket(observeDebugWorkspaceDecision({observations:records,subjectUuid,identity,tick:request.endTick}),limits);
  const related=buildDebugWorkspaceRelatedProjectileTraces({observations:records,subjectUuid,identity,window:request,maxSamples:limits.maxSamples,maxGapTicks:limits.maxGapTicks});
  const result={schema:'kneekura.retained-decision-presentation/v1',identity:{...identity,subjectUuid},
    request:{startTick:request.startTick,endTick:request.endTick,...limits},overview,
    layers:{motion:{enabledByDefault:false,status:retained.length?'AVAILABLE':'NOT_CAPTURED',trace,
      samplesTruncated:valid.length>retained.length,missingPositionRows:state.length-valid.length},
      relatedProjectiles:{enabledByDefault:false,status:related.length?'PARTIAL':'NOT_CAPTURED',traces:related,
        semantics:'FINITE_ACCEPTED_SPAWN_AND_COMPLETED_TICK_ONLY_NOT_ALL_OWNER_PROJECTILES'},
      terrain:{enabledByDefault:false,status:terrain?.data.status??'NOT_CAPTURED',tick:terrain?.tick??null,
        cells:terrain?.data.cells??[],data:terrain?.data??null,source_observation_ids:terrain?.source_observation_ids??[]},
      pathCache:{enabledByDefault:false,status:path?.frontierStatus??'NOT_CAPTURED',tick:path?.tick??null,
        nodes:path?.frontier?.data?.nodes??[],data:path??null,source_observation_ids:path?.source_observation_ids??[]},
      declaredNavigation:{enabledByDefault:false,status:validNav?'AVAILABLE':'NOT_CAPTURED',tick:validNav?snapshot.gameTime:null,
        nodes:validNav?structuredClone(navEntries.slice(0,limits.maxNodes)):[],
        nodesTruncated:validNav&&(navData.truncated===true||navEntries.length>limits.maxNodes),
        semantics:'DECLARED_ROUTE_NOT_ACTUAL_MOTION_OR_FRONTIER',source_observation_ids:validNav?[snapshot.observationId]:[]}},
    semantics:{readOnlyRetainedEvidence:true,temporalAdjacencyProvesCausality:false,distanceBreakProvesTeleport:false,
      terrainIsPathfinderEvaluation:false,pathCacheContainsAllNeighbors:false,missingPositionsAreInterpolated:false,
      elevationUsesTickAndHeight:true}};
  if(bytes(result)>262144)throw new RangeError('DECISION_PRESENTATION_BYTE_BUDGET_EXCEEDED');
  return result;
}
