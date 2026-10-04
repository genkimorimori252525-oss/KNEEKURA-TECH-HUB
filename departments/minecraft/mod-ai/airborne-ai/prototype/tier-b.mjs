import {
  assertFiniteNumber,
  assertNonNegativeInteger,
  assertTargetIdentity,
  assertVec3,
  clampPositionAltitude,
  normalize2Or3D,
  scale,
  subtract,
} from './contracts.mjs';

export const CommonCombatState = Object.freeze({
  IDLE: 'IDLE',
  CHASE: 'CHASE',
  CHARGE: 'CHARGE',
  RECOVERY: 'RECOVERY',
  FAILED: 'FAILED',
});

function distance(a, b) {
  const [dx, dy, dz] = subtract(a, b);
  return Math.hypot(dx, dy, dz);
}

export class TierBCommonFlyer {
  constructor({
    selfId,
    position = [0, 70, 0],
    minAltitude = 1,
    maxAltitude = 256,
    chaseSpeed = 0.6,
    chargeSpeed = 1.1,
    attackRange = 2.5,
    blockedTicksBeforeRecovery = 2,
    maxRecoveryAttempts = 2,
  }) {
    if (typeof selfId !== 'string' || selfId.length === 0) throw new TypeError('selfId must be a non-empty string');
    assertFiniteNumber(chaseSpeed, 'chaseSpeed');
    assertFiniteNumber(chargeSpeed, 'chargeSpeed');
    assertFiniteNumber(attackRange, 'attackRange');
    assertNonNegativeInteger(blockedTicksBeforeRecovery, 'blockedTicksBeforeRecovery');
    assertNonNegativeInteger(maxRecoveryAttempts, 'maxRecoveryAttempts');
    if (chaseSpeed < 0 || chargeSpeed < 0 || attackRange < 0) throw new RangeError('speed/range must be non-negative');
    if (!Number.isFinite(minAltitude) || !Number.isFinite(maxAltitude) || minAltitude > maxAltitude) {
      throw new RangeError('invalid altitude bounds');
    }
    this.selfId = selfId;
    this.minAltitude = minAltitude;
    this.maxAltitude = maxAltitude;
    this.chaseSpeed = chaseSpeed;
    this.chargeSpeed = chargeSpeed;
    this.attackRange = attackRange;
    this.blockedTicksBeforeRecovery = blockedTicksBeforeRecovery;
    this.maxRecoveryAttempts = maxRecoveryAttempts;
    this.position = clampPositionAltitude(position, minAltitude, maxAltitude);
    this.velocity = [0, 0, 0];
    this.targetId = null;
    this.targetPosition = null;
    this.combatState = CommonCombatState.IDLE;
    this.blockedTicks = 0;
    this.recoveryAttempts = 0;
    this.terminalFailure = false;
    this.lastReason = 'INIT';
  }

  clearTarget() {
    this.targetId = null;
    this.targetPosition = null;
    this.velocity = [0, 0, 0];
    this.combatState = CommonCombatState.IDLE;
    this.blockedTicks = 0;
    this.lastReason = 'TARGET_CLEARED';
  }

  setTarget({ targetId, position }) {
    assertTargetIdentity(this.selfId, targetId);
    this.targetId = targetId;
    this.targetPosition = clampPositionAltitude(assertVec3(position, 'position'), this.minAltitude, this.maxAltitude);
    this.lastReason = 'TARGET_SET';
    return this.targetPosition;
  }

  tickCombat({ targetId = this.targetId, targetPosition = this.targetPosition, collisionClear }) {
    if (targetId == null || targetPosition == null) {
      this.clearTarget();
      return this.snapshot();
    }
    assertTargetIdentity(this.selfId, targetId);
    if (typeof collisionClear !== 'boolean') throw new TypeError('collisionClear must be boolean');
    this.targetId = targetId;
    this.targetPosition = clampPositionAltitude(assertVec3(targetPosition, 'targetPosition'), this.minAltitude, this.maxAltitude);

    if (!collisionClear) {
      this.blockedTicks += 1;
      this.velocity = scale(this.velocity, 0.5);
      this.lastReason = 'COLLISION_BLOCKED';
      if (this.blockedTicks >= this.blockedTicksBeforeRecovery) this.enterRecovery('BLOCKED_STREAK');
      return this.snapshot();
    }

    this.blockedTicks = 0;
    this.recoveryAttempts = 0;
    this.terminalFailure = false;
    const delta = subtract(this.targetPosition, this.position);
    const dist = distance(this.targetPosition, this.position);
    const direction = normalize2Or3D(delta);
    if (dist <= this.attackRange) {
      this.combatState = CommonCombatState.CHARGE;
      this.velocity = scale(direction, this.chargeSpeed);
      this.lastReason = 'CHARGE';
    } else {
      this.combatState = CommonCombatState.CHASE;
      this.velocity = scale(direction, this.chaseSpeed);
      this.lastReason = 'CHASE';
    }
    return this.snapshot();
  }

  enterRecovery(reason) {
    this.combatState = CommonCombatState.RECOVERY;
    this.velocity = scale(this.velocity, 0.5);
    this.lastReason = `RECOVERY_${reason}`;
  }

  attemptRecovery({ collisionClear, escapeTarget }) {
    if (this.combatState !== CommonCombatState.RECOVERY) throw new Error('not in recovery');
    if (this.terminalFailure) {
      this.lastReason = 'RECOVERY_RETRY_REFUSED';
      return false;
    }
    if (typeof collisionClear !== 'boolean') throw new TypeError('collisionClear must be boolean');
    const target = clampPositionAltitude(assertVec3(escapeTarget, 'escapeTarget'), this.minAltitude, this.maxAltitude);
    if (!collisionClear) {
      this.recoveryAttempts += 1;
      if (this.recoveryAttempts >= this.maxRecoveryAttempts) {
        this.terminalFailure = true;
        this.combatState = CommonCombatState.FAILED;
        this.velocity = [0, 0, 0];
        this.lastReason = 'RECOVERY_EXHAUSTED';
      } else {
        this.lastReason = 'RECOVERY_BLOCKED';
      }
      return false;
    }
    this.velocity = scale(normalize2Or3D(subtract(target, this.position)), this.chaseSpeed);
    this.position = [...this.position];
    this.blockedTicks = 0;
    this.recoveryAttempts = 0;
    this.combatState = this.targetId == null ? CommonCombatState.IDLE : CommonCombatState.CHASE;
    this.lastReason = 'RECOVERY_CLEAR';
    return true;
  }

  snapshot() {
    return Object.freeze({
      selfId: this.selfId,
      combatState: this.combatState,
      targetId: this.targetId,
      targetPosition: this.targetPosition ? [...this.targetPosition] : null,
      velocity: [...this.velocity],
      blockedTicks: this.blockedTicks,
      recoveryAttempts: this.recoveryAttempts,
      terminalFailure: this.terminalFailure,
      lastReason: this.lastReason,
    });
  }
}
