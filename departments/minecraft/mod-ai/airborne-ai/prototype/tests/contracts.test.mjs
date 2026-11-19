import test from 'node:test';
import assert from 'node:assert/strict';
import {
  AirGroundState,
  FlightPurpose,
  RouteMode,
  assertAirGroundState,
  assertTargetIdentity,
  assertVec3,
  clampPositionAltitude,
  landingReservationStatus,
  makeFlightIntent,
  makeLandingReservation,
  makeRouteResult,
  makeTargetMemory,
  routeMatchesGeneration,
  targetMemoryStatus,
  updateTargetMemory,
} from '../contracts.mjs';

test('finite-vector contract rejects NaN and Infinity', () => {
  assert.throws(() => assertVec3([0, Number.NaN, 1]), /finite/);
  assert.throws(() => assertVec3([0, 1, Infinity]), /finite/);
});

test('self-target is forbidden', () => {
  assert.throws(() => assertTargetIdentity('flyer', 'flyer'), /self-target/);
  assert.equal(assertTargetIdentity('flyer', 'target'), 'target');
});

test('flight intent is immutable and generation-scoped', () => {
  const intent = makeFlightIntent({
    purpose: FlightPurpose.CHASE,
    targetPosition: [1, 70, 2],
    targetId: 'target',
    speed: 1.25,
    generation: 3,
  });
  assert.equal(intent.generation, 3);
  assert.equal(intent.purpose, 'CHASE');
  assert.ok(Object.isFrozen(intent));
});

test('altitude policy clamps final destination', () => {
  assert.deepEqual(clampPositionAltitude([1, 500, 2], 5, 128), [1, 128, 2]);
  assert.deepEqual(clampPositionAltitude([1, -20, 2], 5, 128), [1, 5, 2]);
});

test('route results are accepted only for the current generation', () => {
  const route = makeRouteResult({ generation: 7, mode: RouteMode.PATH, points: [[0, 70, 0], [5, 72, 0]] });
  assert.equal(routeMatchesGeneration(route, 7), true);
  assert.equal(routeMatchesGeneration(route, 8), false);
});

test('landing reservation requires same live support and TTL', () => {
  const reservation = makeLandingReservation({
    id: 'pad-a', position: [0, 65, 0], supportId: 'stone@0,64,0', now: 10, ttlTicks: 20,
  });
  assert.equal(landingReservationStatus(reservation, { now: 20, supportId: 'stone@0,64,0', supportValid: true }), 'VALID');
  assert.equal(landingReservationStatus(reservation, { now: 20, supportId: 'air@0,64,0', supportValid: true }), 'SUPPORT_CHANGED');
  assert.equal(landingReservationStatus(reservation, { now: 20, supportId: 'stone@0,64,0', supportValid: false }), 'INVALID_SUPPORT');
  assert.equal(landingReservationStatus(reservation, { now: 31, supportId: 'stone@0,64,0', supportValid: true }), 'EXPIRED');
});

test('LOS loss enters bounded search and visible reacquire extends memory', () => {
  const memory = makeTargetMemory({ selfId: 'flyer', targetId: 'target', position: [10, 70, 10], visible: true, now: 100, searchTicks: 40 });
  updateTargetMemory(memory, { position: [11, 70, 10], visible: false, now: 110, searchTicks: 40 });
  assert.equal(targetMemoryStatus(memory, 130), 'SEARCH');
  assert.equal(targetMemoryStatus(memory, 141), 'EXPIRED');
  updateTargetMemory(memory, { position: [12, 70, 10], visible: true, now: 135, searchTicks: 40 });
  assert.equal(targetMemoryStatus(memory, 160), 'VISIBLE');
  assert.equal(memory.searchUntilTick, 175);
});

test('air/ground state contract rejects illegal states', () => {
  assert.equal(assertAirGroundState(AirGroundState.AIRBORNE), 'AIRBORNE');
  assert.throws(() => assertAirGroundState('HOVERING_BUT_MAYBE_GROUNDED'), /unsupported/);
});
