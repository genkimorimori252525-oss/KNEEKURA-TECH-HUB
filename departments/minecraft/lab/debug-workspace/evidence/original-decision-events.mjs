const KINDS = Object.freeze({
  GOAL_ELIGIBILITY_RETURN: ['EVALUATION','goal_eligibility'],
  GOAL_CONTINUATION_RETURN: ['EVALUATION','goal_eligibility'],
  GOAL_START_RETURN: ['EXECUTION','goal_lifecycle'],
  GOAL_STOP_RETURN: ['EXECUTION','goal_lifecycle'],
  BRAIN_TICK_RETURN: ['EXECUTION','brain_execution'],
  BEHAVIOR_TRY_START_RETURN: ['EVALUATION','behavior_execution'],
  BEHAVIOR_TICK_OR_STOP_RETURN: ['EXECUTION','behavior_execution'],
  BEHAVIOR_STOP_RETURN: ['EXECUTION','behavior_execution'],
  SENSOR_SCAN_RETURN: ['INPUT','sensor_execution'],
  CONTROL_TICK_RETURN: ['EXECUTION','movement_control'],
  BASE_MALUS_RETURN: ['EVALUATION','base_path_malus'],
  PATH_SEARCH_STATE: ['EVALUATION','path_search_frontier'],
  PATH_SEARCH_RESULT: ['RESULT','path_search_result'],
});
const text = value => typeof value === 'string' && value.length > 0 && value.length <= 512;
const integer = value => Number.isSafeInteger(value);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
function bounded(value, depth=0, budget={count:0}) {
  if (++budget.count > 8192 || depth > 12) return false;
  if (typeof value === 'string') return value.length <= 512;
  if (typeof value === 'number') return Number.isFinite(value);
  if (value === null || typeof value === 'boolean') return true;
  if (Array.isArray(value)) return value.length <= 64 && value.every(v=>bounded(v,depth+1,budget));
  if (!object(value)) return false;
  const entries=Object.entries(value);
  return entries.length <= 32 && entries.every(([k,v])=>k.length <= 128 && bounded(v,depth+1,budget));
}
function numberOrUnknown(data,key) {
  return Number.isFinite(data[key]) || (data[key] === undefined && data[key+'Status'] === 'NOT_EXPOSED');
}
function validInstanceIdentity(data,requiredStatus=false) {
  const status=data.instanceIdentityStatus;
  if(text(data.instanceIdentity))return status==='AVAILABLE'||(!requiredStatus&&status===undefined);
  // The real writer's Gson omits JsonNull fields. Missing identity remains unknown, never an ID.
  return data.instanceIdentity==null&&(status==='NOT_EXPOSED'||(!requiredStatus&&status===undefined));
}
export function originalDecisionData(record) {
  const data=structuredClone(record.payload.data),kind=record.payload.kind;
  if(kind.startsWith('GOAL_')||kind==='BRAIN_TICK_RETURN'||kind.startsWith('BEHAVIOR_')||kind==='SENSOR_SCAN_RETURN') {
    data.instanceIdentity??=null;
    data.instanceIdentityStatus=data.instanceIdentity===null?'NOT_EXPOSED':'AVAILABLE';
  }
  return data;
}
function validFrontier(section) {
  if (!object(section)) return false;
  if (section.status === 'NOT_EXPOSED') return section.detail === 'CUSTOM_NODE_EVALUATOR';
  if (!['AVAILABLE','PARTIAL'].includes(section.status)) return false;
  const d=section.data;
  return object(d) && Array.isArray(d.nodes) && d.nodes.length <= 64 && integer(d.cacheNodeCount) &&
    d.cacheNodeCount >= d.nodes.length && typeof d.truncated === 'boolean' &&
    d.truncated === (d.cacheNodeCount > d.nodes.length) &&
    section.status === (d.truncated ? 'PARTIAL' : 'AVAILABLE') &&
    d.phase === 'OUTER_BEFORE_DONE_AFTER_INNER_RETURN' &&
    d.neighborEvaluationTraceStatus === 'NOT_EXPOSED' && d.rejectionReasonStatus === 'NOT_EXPOSED' &&
    d.nodes.every(n=>object(n) && ['x','y','z'].every(k=>integer(n[k])) && text(n.pathType) &&
      ['g','h','f','costMalus','walkedDistance'].every(k=>numberOrUnknown(n,k)) &&
      typeof n.openAtReturn === 'boolean' && typeof n.closedAtReturn === 'boolean' &&
      n.cacheRole === (n.closedAtReturn ? 'CLOSED_AT_RETURN' : n.openAtReturn ? 'OPEN_AT_RETURN' : 'OTHER_CACHED') &&
      (n.parentX === undefined ? n.parentY === undefined && n.parentZ === undefined :
        ['parentX','parentY','parentZ'].every(k=>integer(n[k]))));
}
function validData(kind,d) {
  if (kind.startsWith('GOAL_')) {
    if (!['goal','target'].includes(d.selector) || !text(d.goalClass) || !integer(d.priority) ||
        !validInstanceIdentity(d,true)) return false;
    return kind.includes('ELIGIBILITY') || kind.includes('CONTINUATION')
      ? typeof d.result === 'boolean' && d.rejectionReasonStatus === 'NOT_EXPOSED' && d.callSiteStatus === 'NOT_EXPOSED'
      : typeof d.running === 'boolean' && d.reasonStatus === 'NOT_EXPOSED';
  }
  if (kind === 'BRAIN_TICK_RETURN') return text(d.brainClass) && typeof d.storedBrainMatch === 'boolean' && validInstanceIdentity(d);
  if (kind.startsWith('BEHAVIOR_')) return text(d.className) && validInstanceIdentity(d) &&
    ['RUNNING','STOPPED'].includes(d.cachedStatus) && d.reasonStatus === 'NOT_EXPOSED' &&
    (kind !== 'BEHAVIOR_TRY_START_RETURN' || typeof d.result === 'boolean');
  if (kind === 'SENSOR_SCAN_RETURN') return text(d.className) && validInstanceIdentity(d) && d.candidatePopulationStatus === 'NOT_EXPOSED';
  if (kind === 'CONTROL_TICK_RETURN') return ['move','look','jump'].includes(d.control) && object(d.cachedBaseFields) &&
    text(d.cachedBaseFields.className) && d.cachedBaseFields.fieldScope === 'BASE_CONTROL_FIELDS_ONLY';
  if (kind === 'BASE_MALUS_RETURN') return text(d.pathType) && numberOrUnknown(d,'returnedMalus') &&
    d.dispatchScope === 'BASE_METHOD_RETURN_NOT_CUSTOM_OVERRIDE_RESULT' && d.effectiveSourceStatus === 'NOT_EXPOSED';
  if (kind === 'PATH_SEARCH_STATE') return text(d.searchId) && validFrontier(d.frontier);
  if (kind === 'PATH_SEARCH_RESULT') return text(d.searchId) && typeof d.resultPresent === 'boolean' &&
    (!d.resultPresent || text(d.resultClass)) &&
    (d.canReach === undefined || typeof d.canReach === 'boolean') &&
    (d.resultNodeCount === undefined || (integer(d.resultNodeCount) && d.resultNodeCount >= 0));
  return false;
}

/** Validate retained output; no invocation, neighbor population or causal reason is reconstructed. */
export function validOriginalDecisionEvent(record) {
  const p=record.payload;
  return record.source?.side === 'SERVER' && p?.schema === 'kneekura.original-decision-event/v1' &&
    p.semantics === 'ORIGINAL_INVOCATION_RETURN_ONLY' && integer(p.targetRevision) && p.targetRevision > 0 &&
    integer(p.eventIndex) && p.eventIndex >= 1 && p.eventIndex <= 256 && text(p.burstId) &&
    Object.hasOwn(KINDS,p.kind) && object(p.data) && bounded(p) &&
    Number.isSafeInteger(p.observerCostNanos) && p.observerCostNanos >= 0 &&
    p.observerCostScope === 'BUILD_AND_FIRST_BYTE_CHECK_EXCLUDES_FINAL_ENCODING_WRITER' &&
    validData(p.kind,p.data) && new TextEncoder().encode(JSON.stringify(p)).length <= 32768;
}

export function appendOriginalDecisionEvents(records,stages,capabilities,timeline) {
  for (const record of records) {
    if (!validOriginalDecisionEvent(record)) continue;
    const p=record.payload;
    const data=originalDecisionData(record);
    const [stage,capability]=KINDS[p.kind];
    const algorithm=p.kind === 'PATH_SEARCH_STATE';
    const status=algorithm ? 'INSTRUMENTED_ALGORITHM_STATE' : 'DIRECT_OBSERVED';
    const relation=algorithm ? 'ALGORITHM_TRACE_RELATION' : 'DIRECT_RUNTIME_RELATION';
    stages[stage] ??= {facts:[]};
    stages[stage].facts.push({key:p.kind.toLowerCase(),value:data,epistemic_status:status,
      causal_relation:relation,source_observation_ids:[record.observationId],
      note:'Bounded original invocation only; no reason, complete decision history or adjacent-event causality is inferred.'});
    const unavailable=algorithm && p.data.frontier.status === 'NOT_EXPOSED';
    if (!unavailable) {
      const existing=capabilities[capability];
      capabilities[capability]={status:'PARTIAL',source_observation_ids:[...new Set([
        ...(existing?.source_observation_ids ?? []),record.observationId])],
        detail:'Finite opt-in capture of observed invocations; absent or suppressed invocations and causal reasons remain unknown.'};
    }
    timeline.push({event_id:record.observationId,tick:record.gameTime,stage,kind:p.kind,
      summary:{...data,burstId:p.burstId,eventIndex:p.eventIndex},epistemic_status:status,
      causal_relation:relation,source_observation_ids:[record.observationId]});
  }
}
