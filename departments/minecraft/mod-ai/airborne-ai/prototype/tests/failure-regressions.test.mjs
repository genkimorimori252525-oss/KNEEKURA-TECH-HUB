import test from 'node:test';
import assert from 'node:assert/strict';
import { makeRouteResult, RouteMode } from '../contracts.mjs';
import { TierAHeroFlyer } from '../tier-a.mjs';
import { TierBCommonFlyer } from '../tier-b.mjs';

const hero = (overrides = {}) => new TierAHeroFlyer({ selfId: 'hero', position: [0, 80, 0], ...overrides });
const common = (overrides = {}) => new TierBCommonFlyer({ selfId: 'mob', position: [0, 70, 0], ...overrides });

test('regression: Dragon Fix-style non-finite command is rejected before movement', () => {
  const flyer = hero();
  assert.throws(() => flyer.issueIntent({ purpose: 'CHASE', targetPosition: [0, Number.NaN, 0], targetId: 'target' }), /finite/);
  assert.equal(flyer.snapshot().routeGeneration, 0);
});

test('regression: Dragon Fix-style self-target is rejected', () => {
  const flyer = common();
  assert.throws(() => flyer.setTarget({ targetId: 'mob', position: [1, 70, 0] }), /self-target/);
  assert.equal(flyer.snapshot().targetId, null);
});

test('regression: cave/ceiling altitude request is bounded before route planning', () => {
  const flyer = hero({ maxAltitude: 96 });
  const intent = flyer.issueIntent({ purpose: 'CRUISE', targetPosition: [0, 400, 0] });
  assert.equal(intent.targetPosition[1], 96);
  const route = flyer.planRoute({ directClear: true });
  assert.equal(route.points[0][1], 96);
});

test('regression: Cosy-style invalid landing support is refused', () => {
  const flyer = hero();
  assert.equal(flyer.requestLanding({ id: 'bad', position: [0, 65, 0], supportId: 'shape:none', supportValid: false, now: 0 }), false);
  assert.equal(flyer.snapshot().airState, 'AIRBORNE');
});

test('regression: removed landing support invalidates an accepted reservation', () => {
  const flyer = hero();
  flyer.requestLanding({ id: 'pad', position: [0, 65, 0], supportId: 'stone@0,64,0', supportValid: true, now: 0, ttlTicks: 50 });
  assert.equal(flyer.revalidateLanding({ now: 5, supportId: 'air@0,64,0', supportValid: true }), 'SUPPORT_CHANGED');
  assert.equal(flyer.snapshot().landingId, null);
  assert.equal(flyer.snapshot().airState, 'AIRBORNE');
});

test('regression: stale async route cannot overwrite a newer objective', () => {
  const flyer = hero();
  flyer.issueIntent({ purpose: 'CHASE', targetPosition: [10, 80, 0], targetId: 'target' });
  const stale = makeRouteResult({ generation: 1, mode: RouteMode.PATH, points: [[10, 80, 0]] });
  flyer.issueIntent({ purpose: 'FLEE', targetPosition: [-10, 80, 0], targetId: 'target' });
  assert.equal(flyer.acceptAsyncRoute(stale), false);
  assert.equal(flyer.snapshot().intentPurpose, 'FLEE');
  assert.equal(flyer.snapshot().routeMode, null);
});

test('regression: route retries terminate instead of looping forever', () => {
  const flyer = hero({ maxRecoveryAttempts: 2 });
  flyer.issueIntent({ purpose: 'CRUISE', targetPosition: [20, 90, 0] });
  flyer.planRoute({ directClear: false, pathAvailable: false });
  flyer.retryAfterRecovery({ directClear: false, pathAvailable: false });
  assert.equal(flyer.snapshot().terminalFailure, true);
  assert.equal(flyer.snapshot().recoveryAttempts, 2);
});

test('regression: LOS loss uses bounded SEARCH and does not become omniscient or instant-forget', () => {
  const flyer = hero({ searchTicks: 10 });
  flyer.observeTarget({ targetId: 'target', position: [10, 80, 0], visible: true, now: 100 });
  flyer.observeTarget({ targetId: 'target', position: [12, 80, 0], visible: false, now: 101 });
  assert.equal(flyer.targetStatus(109), 'SEARCH');
  assert.equal(flyer.targetStatus(111), 'EXPIRED');
});

test('regression: common flyer blocked recovery is finite and terminal', () => {
  const flyer = common({ blockedTicksBeforeRecovery: 1, maxRecoveryAttempts: 1 });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: false });
  assert.equal(flyer.attemptRecovery({ collisionClear: false, escapeTarget: [0, 72, 3] }), false);
  const state = flyer.snapshot();
  assert.equal(state.combatState, 'FAILED');
  assert.equal(state.terminalFailure, true);
});
