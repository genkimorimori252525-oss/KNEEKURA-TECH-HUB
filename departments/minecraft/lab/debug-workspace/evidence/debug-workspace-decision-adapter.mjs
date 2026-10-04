import { createDecisionObservation } from './decision-observation.mjs';
import { buildSampledMotionTrace } from '../../simlab/motion-trace.mjs';
import { validOriginalDecisionEvent, appendOriginalDecisionEvents } from './original-decision-events.mjs';
import {validTerrainGroundQuery} from './terrain-ground-query.mjs';
import {registeredModDecisionAdapters} from './adapters/registered-mod-adapters.mjs';

const SUPPORTED_LANES = new Set([
  'SERVER_ENTITY_STATE',
  'SERVER_TARGET_TRACKED',
  'AI_TARGET',
  'BRAIN_MEMORY',
  'RUNNING_BEHAVIORS',
  'BEHAVIOR_TRANSITION',
  'NAVIGATION',
  'AI_DECISION',
]);

function contextOf(record) {
  return {
    debug_session_id: record.debugSessionId ?? null,
    run_id: record.runId ?? null,
    run_snapshot_id: record.runSnapshotId ?? null,
    process_epoch: record.processEpoch ?? null,
    arena_epoch: record.arenaEpoch ?? null,
  };
}
function sameContext(a, b) {
  return a.debug_session_id === b.debug_session_id &&
    a.run_id === b.run_id &&
    a.run_snapshot_id === b.run_snapshot_id &&
    a.process_epoch === b.process_epoch &&
    a.arena_epoch === b.arena_epoch;
}
function matchesRequestedContext(record, identity = {}) {
  const expected = {
    debugSessionId: identity.debug_session_id ?? identity.debugSessionId,
    runId: identity.run_id ?? identity.runId,
    runSnapshotId: identity.run_snapshot_id ?? identity.runSnapshotId,
    processEpoch: identity.process_epoch ?? identity.processEpoch,
    arenaEpoch: identity.arena_epoch ?? identity.arenaEpoch,
  };
  return Object.entries(expected).every(([key, value]) => value == null || record[key] === value);
}
function exactSubjectRecord(record, subjectUuid) {
  return record &&
    record.kind === 'observation' &&
    SUPPORTED_LANES.has(record.lane) &&
    record.scope?.kind === 'ENTITY_UUID' &&
    record.scope?.entityUuid === subjectUuid &&
    record.epistemicStatus === 'OBSERVED' &&
    record.completeness?.complete === true &&
    typeof record.observationId === 'string' &&
    Number.isInteger(record.gameTime);
}
export function selectDecisionRecords(observations, subjectUuid, identity, endTick = Infinity) {
  if (!Array.isArray(observations)) throw new TypeError('observations must be an array');
  const selected = observations
    .filter(r => exactSubjectRecord(r, subjectUuid))
    .filter(r => matchesRequestedContext(r, identity))
    .filter(r => r.gameTime <= endTick)
    .sort((a,b) => a.gameTime - b.gameTime || (a.writerSeq ?? 0) - (b.writerSeq ?? 0));
  if (selected.length > 1) {
    const base = contextOf(selected[0]);
    for (const record of selected) {
      if (!sameContext(base, contextOf(record))) {
        throw new Error('DECISION_EVIDENCE_CONTEXT_CHANGED: refusing to combine records across run/process/arena identity');
      }
    }
    const revisions = new Set(selected.map(r => r.payload?.targetRevision ?? null));
    if (revisions.size > 1) {
      throw new Error('DECISION_SELECTION_CHANGED: refusing to combine different or unknown target revisions');
    }
  }
  return selected;
}
function latestByLane(records) {
  const out = new Map();
  for (const record of records) out.set(record.lane, record);
  return out;
}
function refs(record) {
  return record ? [record.observationId] : [];
}
function sampledFact(record, key, value, note = null) {
  return {
    key,
    value,
    epistemic_status: 'SAMPLED_OBSERVED',
    causal_relation: 'UNKNOWN_CAUSALITY',
    source_observation_ids: refs(record),
    note,
  };
}
function capability(record, detail = null) {
  return record
    ? { status: 'AVAILABLE', source_observation_ids: refs(record), detail }
    : { status: 'NOT_CAPTURED', source_observation_ids: [], detail };
}
function compactEntityState(payload = {}) {
  const out = {};
  for (const key of ['dimension','x','y','z','vx','vy','vz','yaw','pitch','onGround','alive','removed','noGravity','health','maxHealth']) {
    if (payload[key] !== undefined) out[key] = payload[key];
  }
  return out;
}
function compactTarget(payload = {}) {
  const out = { present: payload.present === true };
  for (const key of ['targetUuid','targetEntityId','targetType','targetAlive','distanceSqr','lineOfSight']) {
    if (payload[key] !== undefined) out[key] = payload[key];
  }
  return out;
}
function compactNavigation(payload = {}) {
  const out = {};
  for (const key of ['navigationDone','pathPresent','pathDone','canReach','nodeCount','nextNodeIndex','nextNodeX','nextNodeY','nextNodeZ']) {
    if (payload[key] !== undefined) out[key] = payload[key];
  }
  return out;
}
function compactBrain(payload = {}) {
  const out = {};
  for (const key of [
    'attackTargetPresent','attackTargetUuid','attackTargetEntityId','attackTargetType',
    'walkTargetPresent','walkTargetX','walkTargetY','walkTargetZ','walkTargetSpeedModifier','walkTargetCloseEnoughDist',
    'lookTargetPresent','lookTargetX','lookTargetY','lookTargetZ',
    'pathMemoryPresent','pathMemoryDone','pathMemoryCanReach','pathMemoryNodeCount','pathMemoryNextNodeIndex',
    'cantReachSincePresent','cantReachSinceGameTime','attackCoolingDown',
    'tlmTargetPosPresent','tlmTargetPosX','tlmTargetPosY','tlmTargetPosZ',
  ]) {
    if (payload[key] !== undefined) out[key] = payload[key];
  }
  return out;
}

const SNAPSHOT_SECTIONS = ['goal_scheduler','brain_memory','brain_activities','navigation_path','movement_control'];
export function validDecisionSnapshot(payload) {
  if (payload?.schema !== 'kneekura.vanilla-decision-snapshot/v1' ||
      !Number.isSafeInteger(payload.targetRevision) || payload.targetRevision < 1 ||
      payload.semantics !== 'MOB_COMPONENT_SNAPSHOT_ONLY' || !payload.sections) return false;
  // Check bounded structure before serialization, including unknown fields.
  let values = 0;
  function bounded(value, depth=0) {
    if (++values > 8192 || depth > 12) return false;
    if (typeof value === 'string') return value.length <= 512;
    if (typeof value === 'number') return Number.isFinite(value);
    if (value === null || typeof value === 'boolean') return true;
    if (Array.isArray(value)) return value.length <= 64 && value.every(v => bounded(v,depth+1));
    if (!value || typeof value !== 'object') return false;
    const entries = Object.entries(value);
    return entries.length <= 32 && entries.every(([k,v]) => k.length <= 128 && bounded(v,depth+1));
  }
  if (!bounded(payload)) return false;
  for (const name of SNAPSHOT_SECTIONS) {
    const section = payload.sections[name];
    if (!section || !['AVAILABLE','PARTIAL','NOT_EXPOSED'].includes(section.status)) return false;
    if (section.status !== 'NOT_EXPOSED' &&
        (!section.data || typeof section.data !== 'object' || Array.isArray(section.data))) return false;
  }
  return new TextEncoder().encode(JSON.stringify(payload)).length <= 65536;
}

function sampledGoalChanges(records) {
  const events = [];
  let previous = null;
  for (const record of records.filter(r => r.lane === 'AI_DECISION')) {
    const section = record.payload.sections.goal_scheduler;
    const data = section.data;
    const complete = section.status === 'AVAILABLE' && ['goal','target'].every(name =>
      Array.isArray(data?.[name]?.entries) && data[name].truncated === false &&
      data[name].entries.every(e => typeof e.instanceIdentity === 'string' && typeof e.running === 'boolean'));
    if (!complete) { previous = null; continue; }
    const running = new Set(['goal','target'].flatMap(name =>
      data[name].entries.filter(e => e.running).map(e => name + ':' + e.instanceIdentity)));
    if (previous) {
      const started = [...running].filter(token => !previous.running.has(token));
      const stopped = [...previous.running].filter(token => !running.has(token));
      if (started.length || stopped.length) events.push({
        event_id: record.observationId + ':goal-delta',tick:record.gameTime,stage:'EXECUTION',
        kind:'GOAL_RUNNING_SET_CHANGED_BETWEEN_SAMPLES',
        summary:{started,stopped,interval:{start_tick:previous.record.gameTime,end_tick:record.gameTime},
          exactTransitionTickKnown:false,reasonKnown:false},
        epistemic_status:'DERIVED_FROM_OBSERVED',causal_relation:'TEMPORAL_ASSOCIATION',
        source_observation_ids:[previous.record.observationId,record.observationId],
      });
    }
    previous = {record,running};
  }
  return events;
}

export function observeDebugWorkspaceDecision({
  observations,
  subjectUuid,
  subjectType = null,
  identity = {},
  tick = Infinity,
} = {}) {
  if (typeof subjectUuid !== 'string' || !subjectUuid) throw new TypeError('subjectUuid is required');
  if (tick !== Infinity && !Number.isInteger(tick)) throw new TypeError('tick must be an integer or Infinity');

  const records = selectDecisionRecords(observations, subjectUuid, identity, tick)
    .filter(r => r.lane !== 'AI_DECISION' || validDecisionSnapshot(r.payload) || validOriginalDecisionEvent(r) || validTerrainGroundQuery(r) || registeredModDecisionAdapters.acceptsSnapshot(r) || registeredModDecisionAdapters.acceptsBurst(r));
  const snapshotRecords=records.filter(r=>r.lane === 'AI_DECISION' && validDecisionSnapshot(r.payload));
  const originalRecords=records.filter(validOriginalDecisionEvent);
  const terrain=records.filter(validTerrainGroundQuery).at(-1)??null;
  const modSnapshot=registeredModDecisionAdapters.captureSnapshot(records);
  const modBurst=registeredModDecisionAdapters.captureBurst(records);
  const latest = latestByLane(records.filter(r=>r.lane !== 'AI_DECISION' || validDecisionSnapshot(r.payload)));
  const state = latest.get('SERVER_ENTITY_STATE') ?? null;
  const target = latest.get('AI_TARGET') ?? null;
  const brain = latest.get('BRAIN_MEMORY') ?? null;
  const running = latest.get('RUNNING_BEHAVIORS') ?? null;
  const navigation = latest.get('NAVIGATION') ?? null;
  const snapshot = latest.get('AI_DECISION') ?? null;

  const capabilities = {
    server_entity_state: capability(state),
    ai_target: capability(target),
    brain_memory: capability(brain, brain ? 'Existing public Brain memory lane; absence of a memory is not a guessed reason.' : null),
    running_behaviors: capability(running, running ? 'Sampled running behavior set; not a complete Goal/Behavior eligibility trace.' : null),
    navigation: capability(navigation, navigation ? 'Current PathNavigation state only; open/closed search frontier is not captured.' : null),
    goal_scheduler: { status: 'NOT_EXPOSED', source_observation_ids: [], detail: 'GoalSelector lifecycle capture is not established by these lanes.' },
    goal_eligibility: { status: 'NOT_EXPOSED', source_observation_ids: [], detail: 'Snapshot does not replay canUse/canContinue or capture every original eligibility invocation.' },
    path_search_frontier: { status: 'NOT_EXPOSED', source_observation_ids: [], detail: 'Open/closed/cost search internals require bounded deep instrumentation.' },
    movement_control: { status: 'NOT_EXPOSED', source_observation_ids: [], detail: 'MoveControl/custom controller internals are not present in the selected lanes.' },
    terrain_ground: {status:terrain?terrain.payload.data.status:'NOT_CAPTURED',source_observation_ids:refs(terrain),
      detail:'Explicit loaded ground query only; cached own overrides/defaults are not effective navigation costs or evaluated neighbors.'},
  };

  const stages = {};
  const stateFacts = [];
  if (state) stateFacts.push(sampledFact(state, 'server_entity_state', compactEntityState(state.payload)));
  if (brain) stateFacts.push(sampledFact(brain, 'brain_memory', compactBrain(brain.payload), 'Only explicitly exposed memories are represented.'));
  if (target) stateFacts.push(sampledFact(target, 'mob_target', compactTarget(target.payload)));
  if (stateFacts.length) stages.STATE = { facts: stateFacts };
  if(modSnapshot) {
    Object.assign(capabilities,modSnapshot.capabilities);
    stages.STATE??={facts:[]};stages.STATE.facts.push(...modSnapshot.facts);
    const evidenceIds=[...new Set(modSnapshot.facts.flatMap(f=>f.source_observation_ids))];
    if(evidenceIds.length)stages.STATE.facts.push({key:modSnapshot.descriptor.namespace+':adapter_source',value:modSnapshot.descriptor,
      epistemic_status:'SAMPLED_OBSERVED',causal_relation:'UNKNOWN_CAUSALITY',source_observation_ids:evidenceIds,
      adapter_namespace:modSnapshot.descriptor.namespace,note:'Matched development resource; not transformed resident-byte attestation.'});
  }
  if(terrain) {
    stages.STATE??={facts:[]};
    stages.STATE.facts.push({key:'terrain_ground',value:terrain.payload.data,epistemic_status:'DIRECT_OBSERVED',
      causal_relation:'UNKNOWN_CAUSALITY',source_observation_ids:refs(terrain),
      note:'Observer queried ground; not selected evaluator admission, live effective malus or pathfinder evaluation.'});
  }

  if (running) {
    stages.EXECUTION = { facts: [sampledFact(
      running,
      'running_behaviors',
      {
        count: running.payload?.count ?? null,
        running: Array.isArray(running.payload?.running) ? running.payload.running : [],
        instanceIdentityScope: running.payload?.instanceIdentityScope ?? null,
      },
      'Running set is sampled state; this does not prove why an entry was selected.'
    )] };
  }
  if (navigation) {
    if (!stages.EXECUTION) stages.EXECUTION = { facts: [] };
    stages.EXECUTION.facts.push(sampledFact(
      navigation,
      'navigation',
      compactNavigation(navigation.payload),
      'PathNavigation current state; not a path-search candidate/frontier trace.'
    ));
  }

  if (snapshot) {
    for (const name of SNAPSHOT_SECTIONS) {
      const section = snapshot.payload.sections[name];
      capabilities[name] = {
        status: section.status,
        source_observation_ids: section.status === 'NOT_EXPOSED' ? [] : refs(snapshot),
        detail: section.detail ?? 'Bounded sampled component state; no eligibility or causal claim.',
      };
      if (section.status === 'NOT_EXPOSED') continue;
      const stage = ['navigation_path','movement_control'].includes(name) ? 'EXECUTION' : 'STATE';
      stages[stage] ??= { facts: [] };
      stages[stage].facts.push(sampledFact(snapshot,name,section.data,
        section.status === 'PARTIAL' ? 'Partial component capture; missing entries remain unknown.' : null));
    }
    stages.STATE ??= { facts: [] };
    stages.STATE.facts.push(sampledFact(snapshot,'observation_context',{
      ...contextOf(snapshot),target_revision:snapshot.payload.targetRevision,
    }));
  }

  const timeline = records
    .filter(r => r.lane === 'BEHAVIOR_TRANSITION')
    .map(r => ({
      event_id: r.observationId,
      tick: r.gameTime,
      stage: 'EXECUTION',
      kind: 'BEHAVIOR_RUNNING_SET_CHANGED',
      summary: {
        started: r.payload?.started ?? [],
        stopped: r.payload?.stopped ?? [],
        transitionSemantics: r.payload?.transitionSemantics ?? null,
        exactTransitionTickKnown: r.payload?.exactTransitionTickKnown ?? false,
        reasonKnown: r.payload?.reasonKnown ?? false,
      },
      epistemic_status: 'DERIVED_FROM_OBSERVED',
      causal_relation: 'TEMPORAL_ASSOCIATION',
      source_observation_ids: [r.observationId],
    }));
  timeline.push(...sampledGoalChanges(snapshotRecords));
  appendOriginalDecisionEvents(originalRecords,stages,capabilities,timeline);
  if(modBurst) {
    Object.assign(capabilities,modBurst.capabilities);
    stages.EXECUTION??={facts:[]};stages.EXECUTION.facts.push(...modBurst.facts);
    for(const fact of modBurst.facts)timeline.push({tick:fact.value.tick,stage:'EXECUTION',kind:'MOD_TRANSITION_METHOD_RETURN',
      summary:{methodOwner:fact.value.methodOwner,methodName:fact.value.methodName,stateChangeStatus:'NOT_EXPOSED',reasonStatus:'NOT_EXPOSED'},
      epistemic_status:fact.epistemic_status,causal_relation:fact.causal_relation,source_observation_ids:fact.source_observation_ids});
  }

  const context = records.length ? contextOf(records[0]) : {
    debug_session_id: identity.debug_session_id ?? null,
    run_id: identity.run_id ?? null,
    run_snapshot_id: identity.run_snapshot_id ?? null,
    process_epoch: identity.process_epoch ?? null,
    arena_epoch: identity.arena_epoch ?? null,
  };
  const currentTick = tick === Infinity
    ? (records.length ? records[records.length - 1].gameTime : null)
    : tick;

  return createDecisionObservation({
    subject: { id: subjectUuid, type: subjectType },
    identity: {
      run_id: context.run_id,
      run_snapshot_id: context.run_snapshot_id,
      arena_epoch: context.arena_epoch,
      tick: currentTick,
    },
    adapter: {
      id: 'debug-workspace:exact-subject',
      version: '1',
      family: 'GENERIC_MOB_BASELINE',
      provenance: 'SERVER_ENTITY_STATE/AI_TARGET/BRAIN_MEMORY/RUNNING_BEHAVIORS/BEHAVIOR_TRANSITION/NAVIGATION/AI_DECISION',
      observer_effect_risk: terrain ? 'BOUNDED_GROUND_QUERY_OBSERVER' : originalRecords.length||modBurst ? 'BOUNDED_INSTRUMENTED_OBSERVER' : 'BOUNDED_SAMPLED_OBSERVER',
    },
    capabilities,
    stages,
    timeline,
    availableDrilldowns: [
      ...(state ? ['motion_trace'] : []),
      ...(brain ? ['brain_memory'] : []),
      ...(running ? ['running_behaviors'] : []),
      ...(navigation ? ['navigation'] : []),
      ...(snapshot ? SNAPSHOT_SECTIONS.filter(name => snapshot.payload.sections[name].status !== 'NOT_EXPOSED') : []),
      ...(originalRecords.length ? ['original_decision_events'] : []),
      ...(originalRecords.some(r=>r.payload.kind==='PATH_NEIGHBORS_RETURN') ? ['path_neighbors'] : []),
      ...(originalRecords.some(r=>r.payload.kind==='EFFECTIVE_MALUS_RETURN') ? ['effective_malus'] : []),
      ...(terrain ? ['terrain_ground'] : []),
      ...(modSnapshot ? ['mod_state'] : []),
      ...(modBurst ? ['mod_returns'] : []),
    ],
  });
}

export function buildDebugWorkspaceMotionTrace({
  observations,
  subjectUuid,
  subjectType = null,
  identity = {},
  window = {},
  maxSamples = 4096,
  maxGapTicks = null,
  explicitDiscontinuities = [],
} = {}) {
  if (typeof subjectUuid !== 'string' || !subjectUuid) throw new TypeError('subjectUuid is required');
  const start = window.start_tick ?? window.startTick ?? -Infinity;
  const end = window.end_tick ?? window.endTick ?? Infinity;
  const selected = selectDecisionRecords(observations, subjectUuid, identity, end).filter(r=>r.gameTime>=start);
  const records = selected
    .filter(r => r.lane === 'SERVER_ENTITY_STATE')
    .filter(r => r.gameTime >= start);

  const classes=new Set(records.map(r=>r.payload?.motionTraceClass??'MOB_ACTUAL'));
  if(classes.size>1||[...classes].some(c=>!['MOB_ACTUAL','PROJECTILE_ACTUAL'].includes(c)))throw new Error('MOTION_TRACE_CLASS_CHANGED_OR_UNSUPPORTED');

  const points = records.map(r => ({
    tick: r.gameTime,
    x: r.payload?.x,
    y: r.payload?.y,
    z: r.payload?.z,
    vx: r.payload?.vx,
    vy: r.payload?.vy,
    vz: r.payload?.vz,
    source_observation_id: r.observationId,
    source_kind: 'DEBUG_WORKSPACE_SERVER_ENTITY_STATE',
    run_id: r.runId ?? null,
    run_snapshot_id: r.runSnapshotId ?? null,
    arena_epoch: r.arenaEpoch ?? null,
    dimension_id: r.payload?.dimension ?? null,
  }));

  const absent=selected.filter(r=>r.lane==='SERVER_TARGET_TRACKED'&&r.source?.side==='SERVER'&&r.payload?.tracked===false);
  const teleports=selected.filter(r=>validOriginalDecisionEvent(r)&&r.payload.kind==='CONTROL_TELEPORT_RETURN'&&r.payload.data.result===true);
  const before=(a,b)=>a.gameTime<b.gameTime || (a.gameTime===b.gameTime &&
    typeof a.writerId==='string'&&a.writerId.length>0&&a.writerId===b.writerId&&
    Number.isSafeInteger(a.writerSeq)&&Number.isSafeInteger(b.writerSeq)&&a.writerSeq<b.writerSeq);
  const breaks=[...explicitDiscontinuities];
  for(let i=1;i<records.length;i++){
    const a=records[i-1],b=records[i],missing=absent.find(r=>r.gameTime>a.gameTime&&r.gameTime<b.gameTime);
    if(missing)breaks.push({after_tick:a.gameTime,before_tick:b.gameTime,kind:'MISSING_SELECTED_ENTITY',source_observation_id:missing.observationId});
    const teleport=teleports.find(r=>before(a,r)&&before(r,b));
    if(teleport)breaks.push({after_tick:a.gameTime,before_tick:b.gameTime,kind:'EXPLICIT_TELEPORT',source_observation_id:teleport.observationId});
  }

  return buildSampledMotionTrace({
    traceClass: [...classes][0]??'MOB_ACTUAL',
    subject: { id: subjectUuid, type: subjectType },
    observations: points,
    identity,
    window: {
      start_tick: Number.isFinite(start) ? start : null,
      end_tick: Number.isFinite(end) ? end : null,
    },
    maxSamples,
    maxGapTicks,
    explicitDiscontinuities:breaks,
  });
}

/** Independently identified related projectiles; spawn/impact callbacks never become motion samples. */
export function buildDebugWorkspaceRelatedProjectileTraces({observations,subjectUuid,identity={},window={},maxSamples=128,maxGapTicks=10}={}) {
  if(typeof subjectUuid!=='string'||!subjectUuid)throw new TypeError('subjectUuid is required');
  if(!Array.isArray(observations)||observations.length>50000)throw new TypeError('BOUNDED_RETAINED_OBSERVATIONS_REQUIRED');
  if(!Number.isSafeInteger(maxSamples)||maxSamples<1||maxSamples>128)throw new TypeError('BOUNDED_PROJECTILE_SAMPLES_REQUIRED');
  if(!Number.isSafeInteger(maxGapTicks)||maxGapTicks<1||maxGapTicks>100)throw new TypeError('BOUNDED_PROJECTILE_GAP_REQUIRED');
  const start=window.start_tick??window.startTick??-Infinity,end=window.end_tick??window.endTick??Infinity;
  const records=selectDecisionRecords(observations,subjectUuid,identity,end).filter(validOriginalDecisionEvent);
  const groups=new Map(),seenIds=new Set(),seenEvents=new Set();
  for(const record of records) {
    const p=record.payload,d=p.data;
    if(!p.kind.startsWith('CONTROL_PROJECTILE_'))continue;
    if(typeof record.writerId!=='string'||!record.writerId||!Number.isSafeInteger(record.writerSeq))continue;
    const eventKey=JSON.stringify([record.writerId,p.burstId,p.eventIndex]);
    if(seenIds.has(record.observationId)||seenEvents.has(eventKey))throw new Error('RELATED_PROJECTILE_DUPLICATE_OBSERVATION');
    seenIds.add(record.observationId);seenEvents.add(eventKey);
    const key=JSON.stringify([record.writerId,p.burstId,d.projectileUuid,d.spawnEventIndex]);
    if(p.kind==='CONTROL_PROJECTILE_SPAWN_RETURN') {
      if(d.result!==true||groups.size>=16||groups.has(key))continue;
      groups.set(key,{spawn:record,points:[],terminal:null});continue;
    }
    const group=groups.get(key);
    if(!group||group.terminal||p.eventIndex<=group.spawn.payload.eventIndex||
      record.gameTime<group.spawn.gameTime||record.writerSeq<=group.spawn.writerSeq||d.projectileClass!==group.spawn.payload.data.projectileClass)continue;
    if(p.kind!=='CONTROL_PROJECTILE_TICK_RETURN')continue;
    if(d.removed){group.terminal=record;continue;}
    if(record.gameTime<start)continue;
    group.points.push({tick:record.gameTime,...d.position,vx:d.velocity.x,vy:d.velocity.y,vz:d.velocity.z,
      source_observation_id:record.observationId,source_kind:'DEBUG_WORKSPACE_RELATED_PROJECTILE_ORIGINAL_TICK',
      run_id:record.runId,run_snapshot_id:record.runSnapshotId,arena_epoch:record.arenaEpoch,dimension_id:d.dimension});
  }
  // One global position budget, not sixteen separate 128-sample allocations.
  const retainedIds=new Set([...groups.values()].flatMap(g=>g.points).sort((a,b)=>a.tick-b.tick).slice(-maxSamples).map(p=>p.source_observation_id));
  return [...groups.values()].map(g=>({...g,retained:g.points.filter(p=>retainedIds.has(p.source_observation_id))})).filter(g=>g.retained.length).map(g=>({
    owner_uuid:subjectUuid,relationship_scope:'ACCEPTED_FRESH_SPAWN_SELECTED_CACHED_OWNER',
    spawn_source_observation_ids:[g.spawn.observationId],terminal_source_observation_ids:g.terminal?[g.terminal.observationId]:[],
    samples_truncated:g.points.length>g.retained.length,
    trace:buildSampledMotionTrace({traceClass:'PROJECTILE_ACTUAL',subject:{id:g.spawn.payload.data.projectileUuid,type:g.spawn.payload.data.projectileClass},
      observations:g.retained,identity,maxSamples,maxGapTicks,
      window:{start_tick:Number.isFinite(start)?start:null,end_tick:Number.isFinite(end)?end:null}}),
  }));
}
