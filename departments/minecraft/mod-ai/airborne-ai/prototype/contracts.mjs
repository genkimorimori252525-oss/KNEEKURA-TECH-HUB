export const AirGroundState = Object.freeze({
  GROUNDED: 'GROUNDED',
  TAKEOFF: 'TAKEOFF',
  AIRBORNE: 'AIRBORNE',
  LANDING_APPROACH: 'LANDING_APPROACH',
  TOUCHDOWN: 'TOUCHDOWN',
  RECOVERY: 'RECOVERY',
});

export const FlightPurpose = Object.freeze({
  CRUISE: 'CRUISE',
  CHASE: 'CHASE',
  ORBIT: 'ORBIT',
  STRAFE: 'STRAFE',
  DIVE: 'DIVE',
  FLEE: 'FLEE',
  RETURN_HOME: 'RETURN_HOME',
  LAND: 'LAND',
  PERCH: 'PERCH',
  TAKEOFF: 'TAKEOFF',
});

export const RouteMode = Object.freeze({
  DIRECT: 'DIRECT',
  PATH: 'PATH',
  RECOVERY: 'RECOVERY',
});

const PURPOSES = new Set(Object.values(FlightPurpose));
const AIR_STATES = new Set(Object.values(AirGroundState));
const ROUTE_MODES = new Set(Object.values(RouteMode));

export function assertFiniteNumber(value, name = 'value') {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`);
  }
  return value;
}

export function assertNonNegativeInteger(value, name = 'value') {
  if (!Number.isInteger(value) || value < 0) {
    throw new TypeError(`${name} must be a non-negative integer`);
  }
  return value;
}

export function assertVec3(value, name = 'vec3') {
  if (!Array.isArray(value) || value.length !== 3) {
    throw new TypeError(`${name} must be a [x,y,z] array`);
  }
  return value.map((component, index) => assertFiniteNumber(component, `${name}[${index}]`));
}

export function clamp(value, min, max) {
  assertFiniteNumber(value, 'value');
  assertFiniteNumber(min, 'min');
  assertFiniteNumber(max, 'max');
  if (min > max) throw new RangeError('min must be <= max');
  return Math.max(min, Math.min(max, value));
}

export function clampPositionAltitude(position, minAltitude, maxAltitude) {
  const [x, y, z] = assertVec3(position, 'position');
  return [x, clamp(y, minAltitude, maxAltitude), z];
}

export function makeFlightIntent({
  purpose,
  targetPosition,
  targetId = null,
  speed = 1,
  generation,
  arrival = 'BRAKE',
}) {
  if (!PURPOSES.has(purpose)) throw new TypeError(`unsupported flight purpose: ${purpose}`);
  assertVec3(targetPosition, 'targetPosition');
  assertFiniteNumber(speed, 'speed');
  if (speed < 0) throw new RangeError('speed must be >= 0');
  assertNonNegativeInteger(generation, 'generation');
  if (targetId !== null && (typeof targetId !== 'string' || targetId.length === 0)) {
    throw new TypeError('targetId must be null or a non-empty string');
  }
  if (typeof arrival !== 'string' || arrival.length === 0) {
    throw new TypeError('arrival must be a non-empty string');
  }
  return Object.freeze({ purpose, targetPosition: [...targetPosition], targetId, speed, generation, arrival });
}

export function assertTargetIdentity(selfId, targetId) {
  if (targetId == null) return null;
  if (typeof selfId !== 'string' || selfId.length === 0) throw new TypeError('selfId must be a non-empty string');
  if (typeof targetId !== 'string' || targetId.length === 0) throw new TypeError('targetId must be a non-empty string');
  if (selfId === targetId) throw new RangeError('self-target is forbidden');
  return targetId;
}

export function makeTargetMemory({
  selfId,
  targetId,
  position,
  visible,
  now,
  searchTicks,
}) {
  assertTargetIdentity(selfId, targetId);
  assertVec3(position, 'position');
  assertNonNegativeInteger(now, 'now');
  assertNonNegativeInteger(searchTicks, 'searchTicks');
  if (typeof visible !== 'boolean') throw new TypeError('visible must be boolean');
  return {
    targetId,
    visible,
    lastKnownPosition: [...position],
    lastSeenTick: visible ? now : null,
    searchUntilTick: now + searchTicks,
  };
}

export function updateTargetMemory(memory, { position, visible, now, searchTicks }) {
  if (!memory || typeof memory !== 'object') throw new TypeError('memory is required');
  assertVec3(position, 'position');
  assertNonNegativeInteger(now, 'now');
  assertNonNegativeInteger(searchTicks, 'searchTicks');
  if (typeof visible !== 'boolean') throw new TypeError('visible must be boolean');
  memory.lastKnownPosition = [...position];
  memory.visible = visible;
  if (visible) {
    memory.lastSeenTick = now;
    memory.searchUntilTick = now + searchTicks;
  }
  return memory;
}

export function targetMemoryStatus(memory, now) {
  if (!memory) return 'NONE';
  assertNonNegativeInteger(now, 'now');
  if (memory.visible) return 'VISIBLE';
  return now <= memory.searchUntilTick ? 'SEARCH' : 'EXPIRED';
}

export function makeRouteResult({ generation, mode, points = [] }) {
  assertNonNegativeInteger(generation, 'generation');
  if (!ROUTE_MODES.has(mode)) throw new TypeError(`unsupported route mode: ${mode}`);
  if (!Array.isArray(points)) throw new TypeError('points must be an array');
  return Object.freeze({ generation, mode, points: points.map((point, index) => assertVec3(point, `points[${index}]`)) });
}

export function routeMatchesGeneration(route, generation) {
  if (!route) return false;
  assertNonNegativeInteger(generation, 'generation');
  return route.generation === generation;
}

export function makeLandingReservation({
  id,
  position,
  supportId,
  now,
  ttlTicks,
  valid = true,
}) {
  if (typeof id !== 'string' || id.length === 0) throw new TypeError('landing id must be a non-empty string');
  assertVec3(position, 'position');
  if (typeof supportId !== 'string' || supportId.length === 0) throw new TypeError('supportId must be a non-empty string');
  assertNonNegativeInteger(now, 'now');
  assertNonNegativeInteger(ttlTicks, 'ttlTicks');
  if (typeof valid !== 'boolean') throw new TypeError('valid must be boolean');
  return {
    id,
    position: [...position],
    supportId,
    reservedAt: now,
    expiresAt: now + ttlTicks,
    valid,
  };
}

export function landingReservationStatus(reservation, { now, supportId, supportValid }) {
  if (!reservation) return 'NONE';
  assertNonNegativeInteger(now, 'now');
  if (supportValid !== true) return 'INVALID_SUPPORT';
  if (supportId !== reservation.supportId) return 'SUPPORT_CHANGED';
  if (!reservation.valid) return 'INVALID';
  if (now > reservation.expiresAt) return 'EXPIRED';
  return 'VALID';
}

export function assertAirGroundState(state) {
  if (!AIR_STATES.has(state)) throw new TypeError(`unsupported air/ground state: ${state}`);
  return state;
}

export function normalize2Or3D(vector) {
  const [x, y, z] = assertVec3(vector, 'vector');
  const length = Math.hypot(x, y, z);
  if (length < 1e-9) return [0, 0, 0];
  return [x / length, y / length, z / length];
}

export function subtract(a, b) {
  const va = assertVec3(a, 'a');
  const vb = assertVec3(b, 'b');
  return [va[0] - vb[0], va[1] - vb[1], va[2] - vb[2]];
}

export function scale(vector, factor) {
  const v = assertVec3(vector, 'vector');
  assertFiniteNumber(factor, 'factor');
  return v.map(component => component * factor);
}

export function add(a, b) {
  const va = assertVec3(a, 'a');
  const vb = assertVec3(b, 'b');
  return [va[0] + vb[0], va[1] + vb[1], va[2] + vb[2]];
}
