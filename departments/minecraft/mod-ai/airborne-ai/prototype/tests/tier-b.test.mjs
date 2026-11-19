import test from 'node:test';
import assert from 'node:assert/strict';
import { CommonCombatState, TierBCommonFlyer } from '../tier-b.mjs';

const common = (overrides = {}) => new TierBCommonFlyer({ selfId: 'mob', position: [0, 70, 0], ...overrides });

test('Tier B clear corridor produces cheap direct chase velocity', () => {
  const flyer = common({ chaseSpeed: 0.5 });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  const state = flyer.tickCombat({ collisionClear: true });
  assert.equal(state.combatState, CommonCombatState.CHASE);
  assert.deepEqual(state.velocity, [0.5, 0, 0]);
});

test('Tier B enters charge state inside attack range', () => {
  const flyer = common({ attackRange: 3, chargeSpeed: 1.2 });
  flyer.setTarget({ targetId: 'target', position: [2, 70, 0] });
  const state = flyer.tickCombat({ collisionClear: true });
  assert.equal(state.combatState, CommonCombatState.CHARGE);
  assert.deepEqual(state.velocity, [1.2, 0, 0]);
});

test('Tier B rejects self-target', () => {
  const flyer = common();
  assert.throws(() => flyer.setTarget({ targetId: 'mob', position: [1, 70, 0] }), /self-target/);
});

test('Tier B collision probe damps movement and enters recovery after bounded blocked streak', () => {
  const flyer = common({ blockedTicksBeforeRecovery: 2 });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: true });
  assert.equal(flyer.tickCombat({ collisionClear: false }).combatState, CommonCombatState.CHASE);
  const second = flyer.tickCombat({ collisionClear: false });
  assert.equal(second.combatState, CommonCombatState.RECOVERY);
  assert.equal(second.blockedTicks, 2);
});

test('Tier B recovery can escape through one clear cheap probe', () => {
  const flyer = common({ blockedTicksBeforeRecovery: 1 });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: false });
  assert.equal(flyer.snapshot().combatState, CommonCombatState.RECOVERY);
  assert.equal(flyer.attemptRecovery({ collisionClear: true, escapeTarget: [0, 72, 4] }), true);
  assert.equal(flyer.snapshot().combatState, CommonCombatState.CHASE);
  assert.equal(flyer.snapshot().lastReason, 'RECOVERY_CLEAR');
});

test('Tier B recovery attempts are bounded and end in FAILED', () => {
  const flyer = common({ blockedTicksBeforeRecovery: 1, maxRecoveryAttempts: 2 });
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: false });
  assert.equal(flyer.attemptRecovery({ collisionClear: false, escapeTarget: [0, 72, 4] }), false);
  assert.equal(flyer.snapshot().combatState, CommonCombatState.RECOVERY);
  assert.equal(flyer.attemptRecovery({ collisionClear: false, escapeTarget: [0, 72, 4] }), false);
  assert.equal(flyer.snapshot().combatState, CommonCombatState.FAILED);
  assert.equal(flyer.snapshot().terminalFailure, true);
});

test('zero-length target vector never creates NaN velocity', () => {
  const flyer = common();
  flyer.setTarget({ targetId: 'target', position: [0, 70, 0] });
  const state = flyer.tickCombat({ collisionClear: true });
  assert.deepEqual(state.velocity, [0, 0, 0]);
  assert.ok(state.velocity.every(Number.isFinite));
});

test('Tier B clamps target altitude without full path planning', () => {
  const flyer = common({ maxAltitude: 100 });
  assert.deepEqual(flyer.setTarget({ targetId: 'target', position: [2, 999, 3] }), [2, 100, 3]);
});

test('clearing target returns the common flyer to idle with zero velocity', () => {
  const flyer = common();
  flyer.setTarget({ targetId: 'target', position: [10, 70, 0] });
  flyer.tickCombat({ collisionClear: true });
  flyer.clearTarget();
  const state = flyer.snapshot();
  assert.equal(state.combatState, CommonCombatState.IDLE);
  assert.deepEqual(state.velocity, [0, 0, 0]);
});
