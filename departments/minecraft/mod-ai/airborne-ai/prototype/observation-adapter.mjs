export const AIRBORNE_MODEL_OBSERVATION_SCHEMA = 'kneekura.airborne-model-observation/v1';

export const AirborneModelStatus = Object.freeze({
  MODEL_STATE: 'MODEL_STATE',
  NOT_APPLICABLE: 'NOT_APPLICABLE',
  NOT_MODELED: 'NOT_MODELED',
  UNKNOWN: 'UNKNOWN',
});

export const AirborneCapabilityStatus = Object.freeze({
  AVAILABLE: 'AVAILABLE',
  PARTIAL: 'PARTIAL',
  NOT_APPLICABLE: 'NOT_APPLICABLE',
  NOT_MODELED: 'NOT_MODELED',
  UNKNOWN: 'UNKNOWN',
});

export const DecisionStage = Object.freeze({
  INPUT: 'INPUT',
  STATE: 'STATE',
  CANDIDATE: 'CANDIDATE',
  EVALUATION: 'EVALUATION',
  SELECTION: 'SELECTION',
  EXECUTION: 'EXECUTION',
  RESULT: 'RESULT',
});

const TIERS = new Set(['A', 'B']);
const STATUSES = new Set(Object.values(AirborneModelStatus));
const CAPABILITY_STATUSES = new Set(Object.values(AirborneCapabilityStatus));
const STAGES = Object.values(DecisionStage);

function object(value, name) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(`${name} must be an object`);
  }
  return value;
}

function nonEmptyString(value, name) {
  if (typeof value !== 'string' || value.length === 0) {
    throw new TypeError(`${name} must be a non-empty string`);
  }
  return value;
}

function finiteIntegerOrNull(value, name) {
  if (value === null || value === undefined) return null;
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new TypeError(`${name} must be null or a non-negative safe integer`);
  }
  return value;
}

function finiteVec3OrNull(value, name) {
  if (value === null || value === undefined) return null;
  if (!Array.isArray(value) || value.length !== 3 || value.some(v => typeof v !== 'number' || !Number.isFinite(v))) {
    throw new TypeError(`${name} must be null or a finite [x,y,z] array`);
  }
  return [...value];
}

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) deepFreeze(child);
    Object.freeze(value);
  }
  return value;
}

function fact(key, value, status = AirborneModelStatus.MODEL_STATE, note = null) {
  nonEmptyString(key, 'fact.key');
  if (!STATUSES.has(status)) throw new TypeError(`unsupported model status: ${status}`);
  return {
    key,
    value: structuredClone(value),
    model_status: status,
    runtime_epistemic_status: 'NOT_RUNTIME_EVIDENCE',
    causal_relation: 'NO_RUNTIME_CAUSALITY_CLAIM',
    source_observation_ids: [],
    note,
  };
}

function stage(status, facts = []) {
  if (!['MODEL_STATE', 'PARTIAL', 'NOT_APPLICABLE', 'NOT_MODELED', 'UNKNOWN'].includes(status)) {
    throw new TypeError(`unsupported stage status: ${status}`);
  }
  return { status, facts };
}

function capability(status, detail) {
  if (!CAPABILITY_STATUSES.has(status)) throw new TypeError(`unsupported capability status: ${status}`);
  return { status, detail, source_observation_ids: [] };
}

function tierAObservation(snapshot) {
  const routeGeneration = finiteIntegerOrNull(snapshot.routeGeneration, 'snapshot.routeGeneration');
  const recoveryAttempts = finiteIntegerOrNull(snapshot.recoveryAttempts, 'snapshot.recoveryAttempts');
  return {
    capabilities: {
      'airborne:air_ground_state': capability(AirborneCapabilityStatus.AVAILABLE, 'OFFLINE_TIER_A_MODEL_STATE'),
      'airborne:tactical_intent': capability(AirborneCapabilityStatus.AVAILABLE, 'OFFLINE_TIER_A_MODEL_STATE'),
      'airborne:route': capability(AirborneCapabilityStatus.AVAILABLE, 'OFFLINE_TIER_A_DIRECT_PATH_RECOVERY_MODEL'),
      'airborne:landing': capability(AirborneCapabilityStatus.AVAILABLE, 'OFFLINE_TIER_A_RESERVATION_STATE_ONLY'),
      'airborne:target_memory': capability(AirborneCapabilityStatus.PARTIAL, 'VISIBLE_FLAG_ONLY_IN_SNAPSHOT; SEARCH_DEADLINE_NOT_EXPORTED'),
      'airborne:recovery': capability(AirborneCapabilityStatus.AVAILABLE, 'OFFLINE_TIER_A_MODEL_STATE'),
      'airborne:actual_motion': capability(AirborneCapabilityStatus.NOT_MODELED, 'NO_MINECRAFT_ENTITY_MOTION_SAMPLES'),
    },
    stages: {
      INPUT: stage('NOT_MODELED'),
      STATE: stage('MODEL_STATE', [
        fact('airborne:air_ground_state', snapshot.airState ?? null),
        fact('airborne:target_id', snapshot.targetId ?? null),
        snapshot.targetVisible === null || snapshot.targetVisible === undefined
          ? fact('airborne:target_visible', null, AirborneModelStatus.NOT_MODELED, 'TIER_A_SNAPSHOT_HAS_NO_CURRENT_VISIBILITY_VALUE')
          : fact('airborne:target_visible', Boolean(snapshot.targetVisible)),
        fact('airborne:terminal_failure', Boolean(snapshot.terminalFailure)),
      ]),
      CANDIDATE: stage('PARTIAL', [
        fact('airborne:landing_reservation_id', snapshot.landingId ?? null, AirborneModelStatus.MODEL_STATE,
          'NULL_MEANS_NO_ACTIVE_MODEL_RESERVATION; NOT_A_WORLD_TOUCHDOWN_CANDIDATE'),
      ]),
      EVALUATION: stage('NOT_MODELED', [
        fact('airborne:world_clearance_evaluation', null, AirborneModelStatus.NOT_MODELED,
          'REAL_AABB_VOXEL_CLEARANCE_NOT_RUN'),
      ]),
      SELECTION: stage('MODEL_STATE', [
        fact('airborne:intent_purpose', snapshot.intentPurpose ?? null),
        fact('airborne:route_generation', routeGeneration),
      ]),
      EXECUTION: stage('PARTIAL', [
        fact('airborne:route_mode', snapshot.routeMode ?? null, AirborneModelStatus.MODEL_STATE,
          'MODEL_ROUTE_MODE_NOT_DECLARED_MINECRAFT_NAVIGATION'),
        fact('airborne:recovery_attempts', recoveryAttempts),
      ]),
      RESULT: stage('MODEL_STATE', [
        fact('airborne:last_reason', snapshot.lastReason ?? null),
        fact('airborne:terminal_failure', Boolean(snapshot.terminalFailure)),
      ]),
    },
  };
}

function tierBObservation(snapshot) {
  const recoveryAttempts = finiteIntegerOrNull(snapshot.recoveryAttempts, 'snapshot.recoveryAttempts');
  const blockedTicks = finiteIntegerOrNull(snapshot.blockedTicks, 'snapshot.blockedTicks');
  const targetPosition = finiteVec3OrNull(snapshot.targetPosition, 'snapshot.targetPosition');
  const velocity = finiteVec3OrNull(snapshot.velocity, 'snapshot.velocity');
  return {
    capabilities: {
      'airborne:air_ground_state': capability(AirborneCapabilityStatus.NOT_APPLICABLE, 'TIER_B_MODEL_DOES_NOT_IMPLEMENT_AIR_GROUND_TRANSITIONS'),
      'airborne:tactical_intent': capability(AirborneCapabilityStatus.PARTIAL, 'CHASE_CHARGE_COMBAT_STATE_ONLY'),
      'airborne:route': capability(AirborneCapabilityStatus.NOT_APPLICABLE, 'TIER_B_USES_DIRECT_STEERING_WITHOUT_ROUTE_OBJECTS'),
      'airborne:landing': capability(AirborneCapabilityStatus.NOT_APPLICABLE, 'TIER_B_MODEL_HAS_NO_LANDING_RESERVATION'),
      'airborne:target_memory': capability(AirborneCapabilityStatus.NOT_MODELED, 'TIER_B_MODEL_HAS_NO_LOS_MEMORY'),
      'airborne:recovery': capability(AirborneCapabilityStatus.AVAILABLE, 'OFFLINE_TIER_B_BOUNDED_RECOVERY_STATE'),
      'airborne:actual_motion': capability(AirborneCapabilityStatus.NOT_MODELED, 'VELOCITY_IS_MODEL_COMMAND_NOT_MINECRAFT_MOTION_SAMPLE'),
    },
    stages: {
      INPUT: stage('NOT_MODELED'),
      STATE: stage('MODEL_STATE', [
        fact('airborne:combat_state', snapshot.combatState ?? null),
        fact('airborne:target_id', snapshot.targetId ?? null),
        fact('airborne:target_position', targetPosition),
        fact('airborne:blocked_ticks', blockedTicks),
        fact('airborne:terminal_failure', Boolean(snapshot.terminalFailure)),
      ]),
      CANDIDATE: stage('NOT_APPLICABLE'),
      EVALUATION: stage('PARTIAL', [
        fact('airborne:collision_probe_result', null, AirborneModelStatus.UNKNOWN,
          'LATEST_BOOLEAN_PROBE_IS_NOT_RETAINED_IN_TIER_B_SNAPSHOT'),
      ]),
      SELECTION: stage('PARTIAL', [
        fact('airborne:combat_state', snapshot.combatState ?? null, AirborneModelStatus.MODEL_STATE,
          'CHASE_OR_CHARGE_IS_MODEL_SELECTION_STATE'),
      ]),
      EXECUTION: stage('PARTIAL', [
        fact('airborne:command_velocity', velocity, AirborneModelStatus.MODEL_STATE,
          'MODEL_COMMAND_NOT_ACTUAL_MOTION'),
        fact('airborne:recovery_attempts', recoveryAttempts),
      ]),
      RESULT: stage('MODEL_STATE', [
        fact('airborne:last_reason', snapshot.lastReason ?? null),
        fact('airborne:terminal_failure', Boolean(snapshot.terminalFailure)),
      ]),
    },
  };
}

export function createAirborneModelObservation(snapshot, {
  tier,
  tick = null,
  subjectType = null,
  adapterVersion = '1',
} = {}) {
  object(snapshot, 'snapshot');
  if (!TIERS.has(tier)) throw new TypeError('tier must be A or B');
  if (tick !== null && (!Number.isSafeInteger(tick) || tick < 0)) {
    throw new TypeError('tick must be null or a non-negative safe integer');
  }
  nonEmptyString(adapterVersion, 'adapterVersion');
  const subjectId = nonEmptyString(snapshot.selfId, 'snapshot.selfId');
  const specific = tier === 'A' ? tierAObservation(snapshot) : tierBObservation(snapshot);
  const stages = Object.fromEntries(STAGES.map(name => [name, specific.stages[name] ?? stage('UNKNOWN')]));

  return deepFreeze({
    schema: AIRBORNE_MODEL_OBSERVATION_SCHEMA,
    version: 1,
    identity: {
      model_tick: tick,
      route_generation: tier === 'A' ? finiteIntegerOrNull(snapshot.routeGeneration, 'snapshot.routeGeneration') : null,
      run_id: null,
      run_snapshot_id: null,
      arena_id: null,
      arena_epoch: null,
      world_id: null,
      dimension_id: null,
    },
    subject: {
      id: subjectId,
      type: subjectType,
      source_tier: tier,
    },
    adapter: {
      id: 'kneekura:airborne_offline_model',
      version: adapterVersion,
      family: 'AIRBORNE_FOUNDATION_PREVIEW',
      provenance: 'PR86_OFFLINE_CONTRACT_PROTOTYPE',
      observer_effect_risk: 'NOT_APPLICABLE_NO_RUNTIME_OBSERVER',
    },
    capabilities: specific.capabilities,
    stages,
    semantics: {
      source_semantics: 'OFFLINE_MODEL_STATE_ONLY',
      runtime_evidence: false,
      retained_evidence: false,
      source_observation_ids_permitted: false,
      temporal_adjacency_proves_causality: false,
      model_state_proves_minecraft_behavior: false,
      declared_model_route_proves_navigation_adoption: false,
      command_velocity_proves_actual_motion: false,
      missing_or_unmodeled_state_is_not_invented: true,
      read_only_transform: true,
      future_runtime_mapping_requires_source_proven_adapter: true,
    },
  });
}

export function createAirborneModelPacket(observation) {
  object(observation, 'observation');
  if (observation.schema !== AIRBORNE_MODEL_OBSERVATION_SCHEMA) {
    throw new TypeError('airborne model observation required');
  }
  return deepFreeze(structuredClone({
    schema: 'kneekura.airborne-model-packet/v1',
    version: 1,
    identity: observation.identity,
    subject: observation.subject,
    adapter: observation.adapter,
    capabilities: observation.capabilities,
    stages: observation.stages,
    semantics: observation.semantics,
  }));
}
