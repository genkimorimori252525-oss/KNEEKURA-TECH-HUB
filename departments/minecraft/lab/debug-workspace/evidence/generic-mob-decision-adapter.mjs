import { createDecisionObservation } from './decision-observation.mjs';

function positionValue(row) {
  if (!row) return null;
  const value = { x: row.x, y: row.y, z: row.z };
  for (const key of ['vx','vy','vz','yaw','pitch','hp']) if (typeof row[key] === 'number') value[key] = row[key];
  return value;
}

/**
 * Conservative exact-subject baseline adapter for retained SimLab data.
 *
 * This intentionally does not infer Vanilla Goal/Brain/path state. It proves the
 * common DecisionObservationModel can represent a selected known or unknown Mob
 * while leaving unsupported decision channels explicit.
 */
export function observeGenericMobFromSimStore({
  store,
  entityId,
  tick,
  identity = {},
  adapterId = 'simlab:generic_mob',
  adapterVersion = '1',
} = {}) {
  if (!store || typeof store.trackOf !== 'function') throw new TypeError('store.trackOf is required');
  if (!Number.isInteger(tick)) throw new TypeError('tick must be an integer');
  const entity = store.entities?.get ? store.entities.get(entityId) : null;
  const track = store.trackOf(entityId);
  const latestSample = track && typeof track.sampleAtOrBefore === 'function'
    ? track.sampleAtOrBefore(tick)
    : null;

  const capabilities = {
    generic_entity_state: {
      status: latestSample ? 'PARTIAL' : 'NOT_CAPTURED',
      source_observation_ids: latestSample ? [latestSample.source_observation_id] : [],
      detail: latestSample ? 'Conservative retained position state only; no scheduler/path semantics inferred.' : 'No retained position sample for the selected subject.',
    },
    position: {
      status: latestSample ? 'AVAILABLE' : 'NOT_CAPTURED',
      source_observation_ids: latestSample ? [latestSample.source_observation_id] : [],
    },
    motion_trace: {
      status: track && typeof track.samples === 'function' ? 'AVAILABLE' : 'NOT_CAPTURED',
      source_observation_ids: latestSample ? [latestSample.source_observation_id] : [],
    },
    vanilla_goal: { status: 'NOT_EXPOSED' },
    vanilla_brain: { status: 'NOT_EXPOSED' },
    vanilla_pathfinding: { status: 'NOT_EXPOSED' },
    movement_control: { status: 'NOT_EXPOSED' },
    custom_decision: { status: 'NOT_EXPOSED' },
  };

  const stages = {};
  if (latestSample) {
    const atTick = typeof store.stateAt === 'function' ? store.stateAt('pos', entityId, tick) : latestSample;
    const exact = latestSample.tick === tick;
    stages.STATE = { facts: [{
      key: 'position',
      value: positionValue(atTick || latestSample),
      epistemic_status: exact ? 'SAMPLED_OBSERVED' : 'DERIVED_FROM_OBSERVED',
      causal_relation: 'UNKNOWN_CAUSALITY',
      source_observation_ids: [latestSample.source_observation_id],
      note: exact ? 'Retained sampled point at requested tick.' : 'State at requested tick is forward-filled from the latest retained position point; it is not promoted to a sampled observation.',
    }] };
  }

  return createDecisionObservation({
    subject: {
      id: entity?.uuid ?? entityId,
      type: entity?.type ?? null,
      mod_id: entity?.type && String(entity.type).includes(':') ? String(entity.type).split(':',1)[0] : null,
    },
    identity: { ...identity, tick },
    adapter: {
      id: adapterId,
      version: adapterVersion,
      family: 'GENERIC_MOB_BASELINE',
      provenance: 'SIMLAB_RETAINED_POSITION_STATE',
      observer_effect_risk: 'NONE_READ_ONLY_RETAINED_DATA',
    },
    capabilities,
    stages,
    timeline: [],
    availableDrilldowns: capabilities.motion_trace.status === 'AVAILABLE' ? ['motion_trace'] : [],
  });
}
