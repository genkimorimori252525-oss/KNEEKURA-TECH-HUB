import test from 'node:test';
import assert from 'node:assert/strict';
import { RouteMode, makeRouteResult } from '../contracts.mjs';
import { TierAHeroFlyer } from '../tier-a.mjs';

const hero = (overrides = {}) => new TierAHeroFlyer({ selfId: 'hero', position: [0, 80, 0], maxRecoveryAttempts: 3, ...overrides });

test('Tier A chooses direct route before path fallback', () => {
  const flyer = hero();
  flyer.issueIntent({ purpose: 'CHASE', targetPosition: [20, 90, 0], targetId: 'target' });
  const direct = flyer.planRoute({ directClear: true, pathAvailable: true, pathPoints: [[5, 82, 0], [20, 90, 0]] });
  assert.equal(direct.mode, RouteMode.DIRECT);
  assert.equal(flyer.snapshot().lastReason, 'ROUTE_DIRECT');
});

test('Tier A falls back to path when direct corridor is blocked', () => {
  const flyer = hero();
  flyer.issueIntent({ purpose: 'CHASE', targetPosition: [20, 90, 0], targetId: 'target' });
  const route = flyer.planRoute({ directClear: false, pathAvailable: true, pathPoints: [[4, 88, 3], [20, 90, 0]] });
  assert.equal(route.mode, RouteMode.PATH);
  assert.equal(route.points.length, 2);
});

test('stale async route is rejected after objective generation changes', () => {
  const flyer = hero();
  flyer.issueIntent({ purpose: 'CHASE', targetPosition: [20, 90, 0], targetId: 'target' });
  const stale = makeRouteResult({ generation: flyer.routeGeneration, mode: RouteMode.PATH, points: [[20, 90, 0]] });
  flyer.issueIntent({ purpose: 'FLEE', targetPosition: [-20, 90, 0], targetId: 'target' });
  assert.equal(flyer.acceptAsyncRoute(stale), false);
  assert.equal(flyer.snapshot().lastReason, 'STALE_ROUTE_REJECTED');
});

test('landing is rejected when support is invalid at reservation time', () => {
  const flyer = hero();
  assert.equal(flyer.requestLanding({ id: 'pad', position: [0, 65, 0], supportId: 'air', supportValid: false, now: 10 }), false);
  assert.equal(flyer.snapshot().airState, 'AIRBORNE');
});

test('landing support removal cancels approach and resumes airborne state', () => {
  const flyer = hero();
  assert.equal(flyer.requestLanding({ id: 'pad', position: [0, 65, 0], supportId: 'stone', supportValid: true, now: 10 }), true);
  assert.equal(flyer.snapshot().airState, 'LANDING_APPROACH');
  assert.equal(flyer.revalidateLanding({ now: 15, supportId: 'stone', supportValid: false }), 'INVALID_SUPPORT');
  assert.equal(flyer.snapshot().airState, 'AIRBORNE');
});

test('landing cannot complete before contact and requires touchdown handoff', () => {
  const flyer = hero();
  flyer.requestLanding({ id: 'pad', position: [0, 65, 0], supportId: 'stone', supportValid: true, now: 10 });
  assert.equal(flyer.revalidateLanding({ now: 15, supportId: 'stone', supportValid: true, contact: false }), 'VALID');
  assert.equal(flyer.completeTouchdown(), false);
  assert.equal(flyer.revalidateLanding({ now: 16, supportId: 'stone', supportValid: true, contact: true }), 'CONTACT');
  assert.equal(flyer.snapshot().airState, 'TOUCHDOWN');
  assert.equal(flyer.completeTouchdown(), true);
  assert.equal(flyer.snapshot().airState, 'GROUNDED');
});

test('landing reservation expiry cancels approach', () => {
  const flyer = hero({ defaultLandingTtlTicks: 5 });
  flyer.requestLanding({ id: 'pad', position: [0, 65, 0], supportId: 'stone', supportValid: true, now: 10 });
  assert.equal(flyer.revalidateLanding({ now: 16, supportId: 'stone', supportValid: true }), 'EXPIRED');
  assert.equal(flyer.snapshot().airState, 'AIRBORNE');
});

test('route recovery is bounded and refuses retries when exhausted', () => {
  const flyer = hero({ maxRecoveryAttempts: 2 });
  flyer.issueIntent({ purpose: 'CRUISE', targetPosition: [30, 90, 0] });
  assert.equal(flyer.planRoute({ directClear: false, pathAvailable: false }), null);
  assert.equal(flyer.snapshot().recoveryAttempts, 1);
  assert.equal(flyer.retryAfterRecovery({ directClear: false, pathAvailable: false }), null);
  assert.equal(flyer.snapshot().terminalFailure, true);
  assert.equal(flyer.retryAfterRecovery({ directClear: true, pathAvailable: true }), null);
  assert.equal(flyer.snapshot().lastReason, 'RECOVERY_RETRY_REFUSED');
});

test('Tier A LOS memory searches for a bounded time and can reacquire', () => {
  const flyer = hero({ searchTicks: 20 });
  flyer.observeTarget({ targetId: 'target', position: [10, 80, 0], visible: true, now: 100 });
  flyer.observeTarget({ targetId: 'target', position: [11, 80, 0], visible: false, now: 105 });
  assert.equal(flyer.targetStatus(119), 'SEARCH');
  flyer.observeTarget({ targetId: 'target', position: [12, 80, 0], visible: true, now: 118 });
  assert.equal(flyer.targetStatus(200), 'VISIBLE');
});

test('Tier A clamps intent altitude at the final command boundary', () => {
  const flyer = hero({ maxAltitude: 120 });
  const intent = flyer.issueIntent({ purpose: 'CHASE', targetPosition: [0, 999, 0], targetId: 'target' });
  assert.deepEqual(intent.targetPosition, [0, 120, 0]);
});
