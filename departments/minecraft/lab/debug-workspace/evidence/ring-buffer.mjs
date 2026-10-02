import { validateObservation } from './schema.mjs';

function timeOf(record) {
  const ms = Date.parse(record?.observedAt);
  if (!Number.isFinite(ms)) {
    throw new TypeError('ring buffer record requires valid observedAt');
  }
  return ms;
}

export class ObservationRingBuffer {
  constructor(options = {}) {
    this.maxRecords = options.maxRecords ?? 2000;
    this.maxAgeMs = options.maxAgeMs ?? 10000;

    if (!Number.isInteger(this.maxRecords) || this.maxRecords < 1) {
      throw new TypeError('maxRecords must be an integer >= 1');
    }
    if (!Number.isInteger(this.maxAgeMs) || this.maxAgeMs < 1) {
      throw new TypeError('maxAgeMs must be an integer >= 1');
    }

    this.records = [];
    this.droppedRecords = 0;
    this.latestDroppedAtMs = null;
    this.firstObservedAtMs = null;
    this.lastObservedAtMs = null;
  }

  push(record) {
    const validation = validateObservation(record);
    if (!validation.ok) {
      throw new TypeError(
        'invalid ring-buffer observation: ' + validation.errors.join('; ')
      );
    }

    const ms = timeOf(record);

    this.firstObservedAtMs =
      this.firstObservedAtMs == null
        ? ms
        : Math.min(this.firstObservedAtMs, ms);
    this.lastObservedAtMs =
      this.lastObservedAtMs == null
        ? ms
        : Math.max(this.lastObservedAtMs, ms);

    // Cross-process evidence can arrive out of wall-clock order. observedAt is
    // correlation data, not a causal sequence. Keep the bounded buffer sorted
    // for time-window coverage without rejecting a valid late-arriving row.
    let lo = 0;
    let hi = this.records.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (timeOf(this.records[mid]) <= ms) lo = mid + 1;
      else hi = mid;
    }
    this.records.splice(lo, 0, record);

    this.#pruneByAge(this.lastObservedAtMs);
    this.#pruneByCapacity();

    return this.coverage();
  }

  #dropOne() {
    const dropped = this.records.shift();
    if (!dropped) return;
    this.droppedRecords += 1;
    this.latestDroppedAtMs = Math.max(
      this.latestDroppedAtMs ?? -Infinity,
      timeOf(dropped)
    );
  }

  #pruneByAge(nowMs) {
    const cutoff = nowMs - this.maxAgeMs;
    while (this.records.length && timeOf(this.records[0]) < cutoff) {
      this.#dropOne();
    }
  }

  #pruneByCapacity() {
    while (this.records.length > this.maxRecords) {
      this.#dropOne();
    }
  }

  coverage() {
    const oldest = this.records.length ? timeOf(this.records[0]) : null;
    const newest = this.records.length
      ? timeOf(this.records[this.records.length - 1])
      : null;

    return {
      maxRecords: this.maxRecords,
      maxAgeMs: this.maxAgeMs,
      retainedRecords: this.records.length,
      droppedRecords: this.droppedRecords,
      oldestRetainedAt: oldest == null ? null : new Date(oldest).toISOString(),
      newestRetainedAt: newest == null ? null : new Date(newest).toISOString(),
      firstObservedAt:
        this.firstObservedAtMs == null
          ? null
          : new Date(this.firstObservedAtMs).toISOString(),
      latestDroppedAt:
        this.latestDroppedAtMs == null
          ? null
          : new Date(this.latestDroppedAtMs).toISOString(),
    };
  }

  capturePreRoll(options) {
    const triggerMs =
      typeof options.triggerAt === 'number'
        ? options.triggerAt
        : Date.parse(options.triggerAt);
    const requestedPreRollMs = options.requestedPreRollMs ?? 5000;

    if (!Number.isFinite(triggerMs)) {
      throw new TypeError('triggerAt must be a valid timestamp');
    }
    if (!Number.isInteger(requestedPreRollMs) || requestedPreRollMs < 0) {
      throw new TypeError('requestedPreRollMs must be an integer >= 0');
    }

    const requestedStartMs = triggerMs - requestedPreRollMs;
    const filter = typeof options.filter === 'function'
      ? options.filter
      : () => true;

    const selected = this.records.filter((record) => {
      const ms = timeOf(record);
      return ms >= requestedStartMs && ms <= triggerMs && filter(record);
    });

    const oldestSelectedMs = selected.length ? timeOf(selected[0]) : null;
    const newestSelectedMs = selected.length
      ? timeOf(selected[selected.length - 1])
      : null;

    const droppedInsideRequestedWindow =
      this.latestDroppedAtMs != null &&
      this.latestDroppedAtMs >= requestedStartMs;

    const retainedOldestMs = this.records.length ? timeOf(this.records[0]) : null;
    const bufferStartedTooLate =
      this.firstObservedAtMs == null ||
      this.firstObservedAtMs > requestedStartMs;

    const availablePreRollMs =
      retainedOldestMs == null
        ? 0
        : Math.max(0, triggerMs - Math.max(requestedStartMs, retainedOldestMs));

    const truncated =
      droppedInsideRequestedWindow ||
      bufferStartedTooLate ||
      availablePreRollMs < requestedPreRollMs;

    return {
      triggerAt: new Date(triggerMs).toISOString(),
      requestedPreRollMs,
      requestedStartAt: new Date(requestedStartMs).toISOString(),
      availablePreRollMs,
      truncated,
      retainedRecords: selected.length,
      totalBufferedRecords: this.records.length,
      droppedRecords: this.droppedRecords,
      droppedInsideRequestedWindow,
      bufferStartedTooLate,
      oldestSelectedAt:
        oldestSelectedMs == null ? null : new Date(oldestSelectedMs).toISOString(),
      newestSelectedAt:
        newestSelectedMs == null ? null : new Date(newestSelectedMs).toISOString(),
      records: selected,
    };
  }
}
