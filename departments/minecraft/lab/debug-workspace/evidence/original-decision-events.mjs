import twilightForestAnchor from './adapters/twilightforest-anchor.json' with {type:'json'};

const KINDS = Object.freeze({
  MOD_COORDINATION_RETURN: ['EXECUTION','mod_coordination'],
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
  CONTROL_TELEPORT_RETURN: ['RESULT','teleport_result'],
  CONTROL_PROJECTILE_SPAWN_RETURN: ['RESULT','related_projectile_spawn'],
  CONTROL_PROJECTILE_TICK_RETURN: ['EXECUTION','related_projectile_motion'],
  CONTROL_PROJECTILE_HIT_RETURN: ['RESULT','related_projectile_hit'],
  CONTROL_PROJECTILE_HURT_RETURN: ['RESULT','related_projectile_hurt'],
  BASE_MALUS_RETURN: ['EVALUATION','base_path_malus'],
  PATH_SEARCH_STATE: ['EVALUATION','path_search_frontier'],
  PATH_SEARCH_RESULT: ['RESULT','path_search_result'],
});
const text = value => typeof value === 'string' && value.length > 0 && value.length <= 512;
const integer = value => Number.isSafeInteger(value);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const uuid = value => typeof value==='string' && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
const vector = value => object(value)&&['x','y','z'].every(k=>Number.isFinite(value[k]));
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
function validKnightCoordination(d,record) {
  const knight='twilightforest.entity.boss.KnightPhantom';
  const goal='twilightforest.entity.ai.goal.PhantomUpdateFormationAndMoveGoal';
  const formations=['HOVER','LARGE_CLOCKWISE','SMALL_CLOCKWISE','LARGE_ANTICLOCKWISE','SMALL_ANTICLOCKWISE',
    'CHARGE_PLUSX','CHARGE_MINUSX','CHARGE_PLUSZ','CHARGE_MINUSZ','WAITING_FOR_LEADER','ATTACK_PLAYER_START','ATTACK_PLAYER_ATTACK'];
  const int32=v=>integer(v)&&v>=-2147483648&&v<=2147483647;
  const state=s=>object(s)&&Object.keys(s).length===3&&int32(s.number)&&int32(s.ticksProgress)&&formations.includes(s.currentFormation);
  const proof=d.sourceProof;
  const keys=['bossKind','methodOwner','methodName','sourceUuid','sourceStateAtReturn','sourceProof','originalListClass',
    'originalListCount','maxMembers','truncated','membersAtReturn','dispatchScope','memberStateScope','affectedMembersStatus',
    'leaderDecisionStatus','groupIdentityStatus'];
  return Object.keys(d).length===keys.length&&Object.keys(d).every(k=>keys.includes(k))&&
    d.bossKind==='KnightPhantom'&&d.methodOwner===goal&&d.methodName==='broadcastMyFormation'&&
    uuid(d.sourceUuid)&&d.sourceUuid===record.scope?.entityUuid&&state(d.sourceStateAtReturn)&&
    object(proof)&&Object.keys(proof).length===4&&proof.mappedArtifactSha256===twilightForestAnchor.mappedArtifactSha256&&
    proof.goalClassSha256==='bb1f3d4374a2f5926050c3fd9cf0dff142e47d81daf4d0f801d79b473f1fdaf1'&&
    proof.knightClassSha256===twilightForestAnchor.classHashes[knight]&&
    proof.compatibilityStatus==='MATCHED_DEVELOPMENT_RESOURCE_NOT_RESIDENT_ATTESTATION'&&
    d.originalListClass==='java.util.ArrayList'&&int32(d.originalListCount)&&d.originalListCount>=0&&
    integer(d.maxMembers)&&d.maxMembers>=1&&d.maxMembers<=16&&
    Array.isArray(d.membersAtReturn)&&d.membersAtReturn.length===Math.min(d.originalListCount,d.maxMembers)&&
    d.truncated===(d.originalListCount>d.maxMembers)&&
    d.membersAtReturn.every((m,i)=>object(m)&&m.listIndex===i&&text(m.entityClass)&&
      (m.stateStatus==='AVAILABLE'?Object.keys(m).length===5&&m.entityClass===knight&&uuid(m.entityUuid)&&state(m.cachedState):
        Object.keys(m).length===4&&m.stateStatus==='NOT_EXPOSED'&&m.detail==='UNSUPPORTED_MEMBER_CLASS'&&
        m.entityUuid===undefined&&m.cachedState===undefined))&&
    d.dispatchScope==='ORIGINAL_PASSED_LIST_AFTER_BROADCAST'&&d.memberStateScope==='CACHED_FIELDS_AT_RETURN'&&
    ['affectedMembersStatus','leaderDecisionStatus','groupIdentityStatus'].every(k=>d[k]==='NOT_EXPOSED');
}
function validData(kind,d,record) {
  if (kind === 'MOD_COORDINATION_RETURN') return validKnightCoordination(d,record);
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
  if (kind === 'CONTROL_TELEPORT_RETURN') return typeof d.result === 'boolean' &&
    [d.requestedPosition,d.returnedPosition].every(p=>object(p)&&['x','y','z'].every(k=>Number.isFinite(p[k]))) &&
    d.dispatchScope === 'BASE_RANDOM_TELEPORT_RETURN' && d.reasonStatus === 'NOT_EXPOSED';
  if (kind.startsWith('CONTROL_PROJECTILE_')) {
    if(!uuid(d.ownerUuid)||d.ownerUuid!==record.scope?.entityUuid||!uuid(d.projectileUuid)||d.projectileUuid===d.ownerUuid||
      !text(d.projectileClass)||!integer(d.spawnEventIndex)||d.spawnEventIndex<1||d.spawnEventIndex>record.payload.eventIndex||
      d.relationshipScope!=='ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER')return false;
    if(kind==='CONTROL_PROJECTILE_SPAWN_RETURN')return typeof d.result==='boolean'&&d.trackingLimit===16&&
      d.spawnEventIndex===record.payload.eventIndex&&vector(d.position)&&vector(d.velocity)&&d.dispatchScope==='SERVER_ADD_FRESH_ENTITY_RETURN';
    if(d.spawnEventIndex>=record.payload.eventIndex)return false;
    if(kind==='CONTROL_PROJECTILE_TICK_RETURN')return vector(d.position)&&vector(d.velocity)&&typeof d.removed==='boolean'&&
      text(d.dimension)&&d.dispatchScope==='SERVER_NON_PASSENGER_ORIGINAL_TICK_AFTER';
    if(kind==='CONTROL_PROJECTILE_HIT_RETURN')return ['ENTITY','BLOCK'].includes(d.hitType)&&vector(d.hitPosition)&&
      (d.hitType==='ENTITY'?uuid(d.targetUuid):d.targetUuid==null)&&
      d.dispatchScope==='BASE_PROJECTILE_ON_HIT_RETURN'&&d.damageOutcomeStatus==='NOT_EXPOSED';
    if(kind==='CONTROL_PROJECTILE_HURT_RETURN')return uuid(d.targetUuid)&&typeof d.result==='boolean'&&Number.isFinite(d.requestedDamage)&&
      Number.isSafeInteger(d.preCallObserverCostNanos)&&d.preCallObserverCostNanos>=0&&
      d.requestedDamage>=0&&d.dispatchScope==='ARROW_OR_FIREBALL_ORIGINAL_ENTITY_HURT_CALL'&&d.damageReasonStatus==='NOT_EXPOSED'&&
      (d.healthStatus==='NOT_EXPOSED'?
        d.healthBefore===undefined&&d.healthAfter===undefined&&d.healthDelta===undefined&&d.healthScope==='NON_LIVING_OR_UNAVAILABLE':
        d.healthStatus==='AVAILABLE'&&['healthBefore','healthAfter','healthDelta'].every(k=>Number.isFinite(d[k]))&&
        d.healthScope==='BASE_LIVING_DATA_HEALTH_ACROSS_ORIGINAL_CALL'&&
        Math.abs(d.healthDelta-(d.healthBefore-d.healthAfter))<=1e-5);
    return false;
  }
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
    validData(p.kind,p.data,record) && new TextEncoder().encode(JSON.stringify(p)).length <= 32768;
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
