import {selectDecisionRecords,validDecisionSnapshot} from './debug-workspace-decision-adapter.mjs';
import {validOriginalDecisionEvent,originalDecisionData} from './original-decision-events.mjs';
import {validTerrainGroundQuery} from './terrain-ground-query.mjs';
import {registeredModDecisionAdapters} from './adapters/registered-mod-adapters.mjs';

const CHANNELS=new Set(['path_search','path_neighbors','path_heap_operations','goal_transitions','brain_memory_changes','movement_control','base_malus','effective_malus','sensor_execution','terrain_ground','mod_state','mod_returns']);
const safe=Number.isSafeInteger;
function normalize(subjectUuid,identity,request) {
  if(typeof subjectUuid!=='string'||! /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(subjectUuid))throw new TypeError('EXACT_SUBJECT_UUID_REQUIRED');
  if(!identity||Object.keys(identity).sort().join(',')!=='arenaEpoch,debugSessionId,processEpoch,runId,runSnapshotId,targetRevision'||
    ['debugSessionId','runId','runSnapshotId'].some(k=>typeof identity[k]!=='string'||!identity[k].length||identity[k].length>512)||
    !safe(identity.processEpoch)||identity.processEpoch<1||!safe(identity.arenaEpoch)||identity.arenaEpoch<0||
    !safe(identity.targetRevision)||identity.targetRevision<1)throw new TypeError('COMPLETE_DECISION_IDENTITY_REQUIRED');
  if(!request||!CHANNELS.has(request.channel)||Object.keys(request).some(k=>!['channel','startTick','endTick','limit','maxNodes','maxGapTicks'].includes(k))||
    !safe(request.startTick)||request.startTick<0||!safe(request.endTick)||request.endTick<request.startTick||request.endTick-request.startTick>10000||
    !safe(request.limit)||request.limit<1||request.limit>256||!safe(request.maxNodes)||request.maxNodes<1||request.maxNodes>64||
    (request.maxGapTicks!==undefined&&(!safe(request.maxGapTicks)||request.maxGapTicks<1||request.maxGapTicks>100)))throw new TypeError('BOUNDED_READ_ONLY_DECISION_QUERY_REQUIRED');
  return {...request,maxGapTicks:request.maxGapTicks??10};
}
function pathSearch(records,maxNodes) {
  const searches=new Map();
  for(const record of records) {
    const {kind,data}=record.payload;
    if(!['PATH_SEARCH_STATE','PATH_SEARCH_RESULT'].includes(kind))continue;
    let item=searches.get(data.searchId);
    if(!item){item={searchId:data.searchId,tick:record.gameTime,frontier:null,frontierStatus:'NOT_CAPTURED',
      result:null,resultStatus:'NOT_CAPTURED',queryNodesTruncated:false,neighborEvaluationTraceStatus:'NOT_EXPOSED',
      source_observation_ids:[]};searches.set(data.searchId,item);}
    item.source_observation_ids.push(record.observationId);
    if(kind==='PATH_SEARCH_STATE') {
      item.frontier=structuredClone(data.frontier);item.frontierStatus=data.frontier.status;
      if(item.frontier.data?.nodes.length>maxNodes) {
        item.frontier.data.nodes=item.frontier.data.nodes.slice(0,maxNodes);item.queryNodesTruncated=true;
      }
    }else {item.result=structuredClone(data);item.resultStatus='AVAILABLE';}
  }
  return [...searches.values()];
}
function directEvent(record) {
  return {tick:record.gameTime,kind:record.payload.kind,data:originalDecisionData(record),reasonKnown:false,
    epistemic_status:'DIRECT_OBSERVED',causal_relation:'DIRECT_RUNTIME_RELATION',source_observation_ids:[record.observationId]};
}
function memoryMap(record) {
  if(!validDecisionSnapshot(record.payload))return null;
  const section=record.payload.sections.brain_memory;
  if(section.status!=='AVAILABLE'||section.data?.truncated!==false||!Array.isArray(section.data.entries))return null;
  const result=new Map();
  for(const entry of section.data.entries) {
    if(typeof entry.key!=='string'||! /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(entry.key)||
      typeof entry.registered!=='boolean'||typeof entry.present!=='boolean'||result.has(entry.key))return null;
    // TTL countdown is not misrepresented as a change of the stored memory value.
    const data={registered:entry.registered,present:entry.present,value:entry.value??null};
    result.set(entry.key,data);
  }
  return result;
}
function memoryChanges(records,request) {
  let previous=null;const items=[];
  for(const record of records.filter(r=>r.payload?.schema==='kneekura.vanilla-decision-snapshot/v1')) {
    const memories=memoryMap(record);
    if(!memories){previous=null;continue;}
    if(previous&&record.gameTime-previous.record.gameTime<=request.maxGapTicks&&record.gameTime>=request.startTick) {
      for(const key of new Set([...previous.memories.keys(),...memories.keys()])) {
        const before=previous.memories.get(key)??null,after=memories.get(key)??null;
        if(JSON.stringify(before)!==JSON.stringify(after))items.push({key,tick:record.gameTime,before,after,
          interval:{startTick:previous.record.gameTime,endTick:record.gameTime},exactChangeTickKnown:false,
          epistemic_status:'DERIVED_FROM_OBSERVED',causal_relation:'TEMPORAL_ASSOCIATION',
          source_observation_ids:[previous.record.observationId,record.observationId]});
      }
    }
    previous={record,memories};
  }
  return items;
}

/** Typed retained-evidence read. No free text, world query, owner action or AI call. */
export function queryDecisionDrilldown({observations,subjectUuid,identity,request}={}) {
  const query=normalize(subjectUuid,identity,request);
  if(!Array.isArray(observations)||observations.length>50000)throw new TypeError('BOUNDED_RETAINED_OBSERVATIONS_REQUIRED');
  const matching=observations.filter(r=>r.payload?.targetRevision===identity.targetRevision);
  const selected=selectDecisionRecords(matching,subjectUuid,identity,query.endTick);
  if(new Set(selected.map(r=>r.observationId)).size!==selected.length)throw new Error('DECISION_OBSERVATION_DUPLICATED');
  const events=selected.filter(r=>r.gameTime>=query.startTick&&validOriginalDecisionEvent(r));
  let items;
  switch(query.channel) {
    case 'path_search':items=pathSearch(events,query.maxNodes);break;
    case 'path_heap_operations':items=events.filter(r=>r.payload.kind==='PATH_HEAP_OPERATION_RETURN').map(directEvent);break;
    case 'path_neighbors':items=events.filter(r=>r.payload.kind==='PATH_NEIGHBORS_RETURN').map(r=>{
      const item=directEvent(r);item.queryNodesTruncated=item.data.neighbors.length>query.maxNodes;
      item.data.neighbors=item.data.neighbors.slice(0,query.maxNodes);return item;
    });break;
    case 'goal_transitions':items=events.filter(r=>['GOAL_START_RETURN','GOAL_STOP_RETURN'].includes(r.payload.kind)).map(directEvent);break;
    case 'brain_memory_changes':items=memoryChanges(selected,query);break;
    case 'terrain_ground':items=selected.filter(r=>r.gameTime>=query.startTick&&validTerrainGroundQuery(r)).map(r=>({
      tick:r.gameTime,data:structuredClone(r.payload.data),epistemic_status:'DIRECT_OBSERVED',
      causal_relation:'UNKNOWN_CAUSALITY',source_observation_ids:[r.observationId]}));break;
    case 'mod_state': {
      const retained=selected.filter(r=>r.gameTime>=query.startTick&&registeredModDecisionAdapters.acceptsSnapshot(r));
      const snapshot=registeredModDecisionAdapters.captureSnapshot(retained);
      items=snapshot?[{tick:retained.at(-1).gameTime,...snapshot}]:[];break;
    }
    case 'mod_returns': {
      const retained=selected.filter(r=>r.gameTime>=query.startTick&&registeredModDecisionAdapters.acceptsBurst(r));
      const burst=registeredModDecisionAdapters.captureBurst(retained);
      items=burst?[{tick:retained.at(-1).gameTime,...burst}]:[];break;
    }
    default: {
      const kind={movement_control:'CONTROL_TICK_RETURN',base_malus:'BASE_MALUS_RETURN',effective_malus:'EFFECTIVE_MALUS_RETURN',sensor_execution:'SENSOR_SCAN_RETURN'}[query.channel];
      items=events.filter(r=>r.payload.kind===kind).map(directEvent);
    }
  }
  const total=items.length;items=items.slice(Math.max(0,total-query.limit));
  return {schema:'kneekura.decision-drilldown/v1',identity:{...identity,subjectUuid},request:query,
    status:total?'PARTIAL':'NOT_CAPTURED',totalMatchingItems:total,items,truncated:total>items.length,
    semantics:{readOnlyRetainedEvidence:true,adjacentEventsProveCausality:false,
      missingResultImpliesUnreachable:false,cacheEntriesImplyEvaluatedNeighbors:false,
      queriedTerrainImpliesPathfinderEvaluation:false,
      missingMemoryChangesProveNoChange:false}};
}
