import {
  AirGroundState,
  FlightPurpose,
  RouteMode,
  assertNonNegativeInteger,
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
} from './contracts.mjs';

function nonEmptyString(value, name) {
  if (typeof value !== 'string' || value.length === 0) throw new TypeError(`${name} must be a non-empty string`);
  return value;
}

export class TierAHeroFlyer {
  constructor({
    selfId,
    position = [0, 80, 0],
    minAltitude = 1,
    maxAltitude = 256,
    maxRecoveryAttempts = 3,
    searchTicks = 40,
    defaultLandingTtlTicks = 60,
  }) {
    this.selfId = nonEmptyString(selfId, 'selfId');
    this.minAltitude = minAltitude;
    this.maxAltitude = maxAltitude;
    if (!Number.isFinite(minAltitude) || !Number.isFinite(maxAltitude) || minAltitude > maxAltitude) {
      throw new RangeError('invalid altitude bounds');
    }
    assertNonNegativeInteger(maxRecoveryAttempts, 'maxRecoveryAttempts');
    assertNonNegativeInteger(searchTicks, 'searchTicks');
    assertNonNegativeInteger(defaultLandingTtlTicks, 'defaultLandingTtlTicks');
    this.maxRecoveryAttempts = maxRecoveryAttempts;
    this.searchTicks = searchTicks;
    this.defaultLandingTtlTicks = defaultLandingTtlTicks;
    this.position = clampPositionAltitude(position, minAltitude, maxAltitude);
    this.airState = AirGroundState.AIRBORNE;
    this.routeGeneration = 0;
    this.intent = null;
    this.route = null;
    this.landing = null;
    this.targetMemory = null;
    this.recoveryAttempts = 0;
    this.terminalFailure = false;
    this.lastReason = 'INIT';
  }

  issueIntent({ purpose, targetPosition, targetId = null, speed = 1, arrival = 'BRAKE' }) {
    if (targetId !== null) assertTargetIdentity(this.selfId, targetId);
    const clamped = clampPositionAltitude(targetPosition, this.minAltitude, this.maxAltitude);
    this.routeGeneration += 1;
    this.intent = makeFlightIntent({
      purpose,
      targetPosition: clamped,
      targetId,
      speed,
      generation: this.routeGeneration,
      arrival,
    });
    this.route = null;
    this.lastReason = `INTENT_${purpose}`;
    return this.intent;
  }

  observeTarget({ targetId, position, visible, now }) {
    assertTargetIdentity(this.selfId, targetId);
    assertVec3(position, 'position');
    assertNonNegativeInteger(now, 'now');
    if (this.targetMemory == null || this.targetMemory.targetId !== targetId) {
      this.targetMemory = makeTargetMemory({
        selfId: this.selfId,
        targetId,
        position,
        visible,
        now,
        searchTicks: this.searchTicks,
      });
    } else {
      updateTargetMemory(this.targetMemory, { position, visible, now, searchTicks: this.searchTicks });
    }
    this.lastReason = visible ? 'TARGET_VISIBLE' : 'TARGET_LOST_LOS';
    return this.targetMemory;
  }

  targetStatus(now) {
    const status = targetMemoryStatus(this.targetMemory, now);
    if (status === 'EXPIRED') this.lastReason = 'TARGET_SEARCH_EXPIRED';
    return status;
  }

  planRoute({ directClear, pathAvailable = false, pathPoints = [] }) {
    if (!this.intent) throw new Error('flight intent required before route planning');
    if (typeof directClear !== 'boolean' || typeof pathAvailable !== 'boolean') {
      throw new TypeError('directClear and pathAvailable must be boolean');
    }
    if (directClear) {
      const route = makeRouteResult({
        generation: this.routeGeneration,
        mode: RouteMode.DIRECT,
        points: [this.intent.targetPosition],
      });
      this.route = route;
      this.airState = AirGroundState.AIRBORNE;
      this.recoveryAttempts = 0;
      this.lastReason = 'ROUTE_DIRECT';
      return route;
    }
    if (pathAvailable) {
      const points = pathPoints.length > 0 ? pathPoints : [this.intent.targetPosition];
      const route = makeRouteResult({ generation: this.routeGeneration, mode: RouteMode.PATH, points });
      this.route = route;
      this.airState = AirGroundState.AIRBORNE;
      this.recoveryAttempts = 0;
      this.lastReason = 'ROUTE_PATH';
      return route;
    }
    this.enterRecovery('NO_ROUTE');
    return null;
  }

  acceptAsyncRoute(route) {
    if (!routeMatchesGeneration(route, this.routeGeneration)) {
      this.lastReason = 'STALE_ROUTE_REJECTED';
      return false;
    }
    this.route = route;
    this.lastReason = `ROUTE_${route.mode}_ACCEPTED`;
    return true;
  }

  enterRecovery(reason) {
    nonEmptyString(reason, 'reason');
    this.route = makeRouteResult({ generation: this.routeGeneration, mode: RouteMode.RECOVERY, points: [] });
    this.airState = AirGroundState.RECOVERY;
    this.recoveryAttempts += 1;
    this.terminalFailure = this.recoveryAttempts >= this.maxRecoveryAttempts;
    this.lastReason = this.terminalFailure ? `RECOVERY_EXHAUSTED_${reason}` : `RECOVERY_${reason}`;
    return !this.terminalFailure;
  }

  retryAfterRecovery(routeOptions) {
    if (this.airState !== AirGroundState.RECOVERY) throw new Error('not in recovery');
    if (this.terminalFailure) {
      this.lastReason = 'RECOVERY_RETRY_REFUSED';
      return null;
    }
    this.airState = AirGroundState.AIRBORNE;
    return this.planRoute(routeOptions);
  }

  requestLanding({ id, position, supportId, supportValid, now, ttlTicks = this.defaultLandingTtlTicks }) {
    assertNonNegativeInteger(now, 'now');
    if (supportValid !== true) {
      this.lastReason = 'LANDING_REJECTED_INVALID_SUPPORT';
      return false;
    }
    const landingPosition = clampPositionAltitude(position, this.minAltitude, this.maxAltitude);
    this.issueIntent({
      purpose: FlightPurpose.LAND,
      targetPosition: landingPosition,
      speed: 1,
      arrival: 'CONTACT',
    });
    this.landing = makeLandingReservation({ id, position: landingPosition, supportId, now, ttlTicks });
    this.airState = AirGroundState.LANDING_APPROACH;
    this.lastReason = 'LANDING_APPROACH_STARTED';
    return true;
  }

  revalidateLanding({ now, supportId, supportValid, contact = false }) {
    if (!this.landing) return 'NONE';
    const status = landingReservationStatus(this.landing, { now, supportId, supportValid });
    if (status !== 'VALID') {
      this.landing = null;
      this.airState = AirGroundState.AIRBORNE;
      this.lastReason = `LANDING_CANCELLED_${status}`;
      return status;
    }
    if (contact) {
      this.airState = AirGroundState.TOUCHDOWN;
      this.lastReason = 'LANDING_CONTACT';
      return 'CONTACT';
    }
    this.airState = AirGroundState.LANDING_APPROACH;
    this.lastReason = 'LANDING_VALID_WAIT_CONTACT';
    return 'VALID';
  }

  completeTouchdown() {
    if (this.airState !== AirGroundState.TOUCHDOWN) {
      this.lastReason = 'TOUCHDOWN_COMPLETE_REFUSED';
      return false;
    }
    this.airState = AirGroundState.GROUNDED;
    this.route = null;
    this.intent = null;
    this.landing = null;
    this.recoveryAttempts = 0;
    this.terminalFailure = false;
    this.lastReason = 'LANDED';
    return true;
  }

  takeoff(targetPosition = this.position) {
    const target = clampPositionAltitude(targetPosition, this.minAltitude, this.maxAltitude);
    this.airState = AirGroundState.TAKEOFF;
    this.issueIntent({ purpose: FlightPurpose.TAKEOFF, targetPosition: target, speed: 1 });
    this.lastReason = 'TAKEOFF_STARTED';
    return true;
  }

  completeTakeoff() {
    if (this.airState !== AirGroundState.TAKEOFF) return false;
    this.airState = AirGroundState.AIRBORNE;
    this.lastReason = 'TAKEOFF_COMPLETE';
    return true;
  }

  snapshot() {
    return Object.freeze({
      selfId: this.selfId,
      airState: this.airState,
      routeGeneration: this.routeGeneration,
      routeMode: this.route?.mode ?? null,
      intentPurpose: this.intent?.purpose ?? null,
      landingId: this.landing?.id ?? null,
      targetId: this.targetMemory?.targetId ?? null,
      targetVisible: this.targetMemory?.visible ?? null,
      recoveryAttempts: this.recoveryAttempts,
      terminalFailure: this.terminalFailure,
      lastReason: this.lastReason,
    });
  }
}
