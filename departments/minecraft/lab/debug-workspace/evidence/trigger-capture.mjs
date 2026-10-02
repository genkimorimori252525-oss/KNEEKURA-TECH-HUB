import { createHash } from 'node:crypto';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { exactKeys, identifier, integer, stableJson } from '../bridge/json.mjs';
import { validateVisualIdentity, validateVisualManifest } from './visual-capture.mjs';

const TRIGGERS = new Set(['AI_EXPLICIT', 'TARGET_CHANGED', 'DAMAGE', 'PROJECTILE_SPAWN',
  'PROJECTILE_HIT', 'PROJECTILE_REMOVE', 'NAVIGATION_STUCK', 'ARENA_EXIT', 'INVARIANT_FAILURE',
  'M5_WITHOUT_M6', 'RENDER_ANOMALY', 'EXCEPTION']);
function require(value, reason) { if (!value) throw new TypeError(reason); }
function sameExperiment(a, b) {
  const left = { ...a }; const right = { ...b };
  delete left.arenaRevision; delete right.arenaRevision;
  return stableJson(left) === stableJson(right);
}
export function validateTriggerConfig(value, runtime) {
  const c = structuredClone(value);
  exactKeys(c, ['enabled', 'identity', 'triggerKinds', 'offsetsMs', 'toleranceMs', 'cooldownMs',
    'maxWindows', 'captureBudget', 'timeoutMs'], 'TRIGGER_CONFIG');
  require(c.enabled === true, 'TRIGGERS_REQUIRE_EXPLICIT_OPT_IN'); validateVisualIdentity(c.identity);
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch'])
    require(c.identity[key] === runtime[key], 'FOREIGN_TRIGGER_RUN');
  require(Array.isArray(c.triggerKinds) && c.triggerKinds.length > 0 && c.triggerKinds.length <= TRIGGERS.size &&
    new Set(c.triggerKinds).size === c.triggerKinds.length && c.triggerKinds.every(x => TRIGGERS.has(x)), 'INVALID_TRIGGERS');
  require(Array.isArray(c.offsetsMs) && c.offsetsMs.length > 0 && c.offsetsMs.length <= 21, 'INVALID_CAPTURE_OFFSETS');
  c.offsetsMs.forEach((n, i) => { integer(n, -10000, 10000);
    if (i) require(n - c.offsetsMs[i - 1] >= 250, 'CAPTURE_SAMPLE_RATE_LIMIT'); });
  integer(c.toleranceMs, 0, 250); integer(c.cooldownMs, 1000, 60000);
  integer(c.maxWindows, 1, 8); integer(c.captureBudget, 0, 4); integer(c.timeoutMs, 1, 20000);
  require(c.timeoutMs >= Math.max(0, ...c.offsetsMs), 'TRIGGER_DEADLINE_BEFORE_LAST_SLOT');
  return c;
}
/** Bounded metadata only. Uses the existing EvidenceStore ring and caller's ordinary polling loop. */
export class TriggerCaptureController {
  constructor(runtime, config, requestCapture = null, acceptTrigger = null) {
    require(runtime?.store?.ring && runtime.store.observationById instanceof Map, 'EXISTING_EVIDENCE_OWNER_REQUIRED');
    require(requestCapture === null || typeof requestCapture === 'function', 'REGISTERED_CAPTURE_CALLBACK_REQUIRED');
    this.runtime = runtime; this.config = validateTriggerConfig(config, runtime); this.requestCapture = requestCapture;
    require(acceptTrigger === null || typeof acceptTrigger === 'function', 'REGISTERED_TRIGGER_FILTER_REQUIRED');
    this.acceptTrigger = acceptTrigger;
    this.windows = new Map(); this.usedIds = new Set(); this.usedObservations = new Set();
    this.seenTriggerRows = new Set(runtime.store.observationById.keys());
    this.dispatched = 0; this.lastTrigger = null; this.lastPoll = null; this.closed = false;
  }
  trigger(kind, observationId, captureId) {
    require(!this.closed, 'TRIGGER_OWNER_CLOSED'); identifier(observationId); identifier(captureId);
    require(/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(captureId), 'SAFE_CAPTURE_ID_REQUIRED');
    require(this.config.triggerKinds.includes(kind), 'TRIGGER_NOT_DECLARED');
    require(!this.usedIds.has(captureId) && !this.usedObservations.has(observationId) &&
      this.usedIds.size < this.config.maxWindows, 'TRIGGER_ALREADY_ATTEMPTED_OR_BUDGET');
    const text = this.runtime.store.observationById.get(observationId);
    require(typeof text === 'string', 'CANONICAL_TRIGGER_OBSERVATION_REQUIRED');
    const source = JSON.parse(text);
    require(!this.acceptTrigger || this.acceptTrigger(source), 'TRIGGER_SOURCE_NOT_REGISTERED');
    const identity = validateVisualIdentity(source.payload?.identity);
    require(sameExperiment(identity, this.config.identity) && (kind === 'AI_EXPLICIT' || source.payload.triggerKind === kind), 'TRIGGER_IDENTITY_OR_KIND_MISMATCH');
    const at = Date.parse(source.observedAt); require(Number.isFinite(at), 'TRIGGER_TIME_UNAVAILABLE');
    if (this.lastTrigger !== null) require(at - this.lastTrigger >= this.config.cooldownMs, 'TRIGGER_COOLDOWN');
    const window = { captureId, kind, observationId, at, identity, observedAt: source.observedAt, deadline: at + this.config.timeoutMs,
      slots: this.config.offsetsMs.map(offsetMs => ({ offsetMs, at: at + offsetMs, status: 'WAITING', reason: null,
        sourceObservationId: null, captureId: null, imageHashes: [], captureStatus: null, dispatch: null, match: null })) };
    for (const slot of window.slots) if (slot.offsetMs < 0) {
      const retained = this.#find(slot.at, null, at);
      Object.assign(slot, retained ?? { status: 'MISSING', reason: 'PRE_FRAME_NOT_RETAINED_AT_TRIGGER' });
    }
    this.windows.set(captureId, window); this.usedIds.add(captureId); this.usedObservations.add(observationId); this.lastTrigger = at;
    return { captureId, deadline: window.deadline, slots: window.slots.length };
  }
  observeDeclaredTriggers() {
    if (this.closed) return [];
    const records = this.runtime.store.ring.records;
    const retainedIds = new Set(records.map(r => r.observationId));
    for (const id of this.seenTriggerRows) if (!retainedIds.has(id)) this.seenTriggerRows.delete(id);
    const reports = [];
    for (const row of records) {
      const kind = row.payload?.triggerKind;
      if (!this.config.triggerKinds.includes(kind) || this.seenTriggerRows.has(row.observationId) || (this.acceptTrigger && !this.acceptTrigger(row))) continue;
      this.seenTriggerRows.add(row.observationId);
      if (this.usedIds.size >= this.config.maxWindows) continue;
      const id = 'trigger-' + createHash('sha256').update(row.observationId).digest('hex').slice(0, 32);
      try { reports.push(this.trigger(kind, row.observationId, id)); }
      catch { reports.push({ sourceObservationId: row.observationId, status: 'TRIGGER_REJECTED' }); }
    }
    return reports;
  }
  #find(at, dispatch = null, beforeMs = null) {
    const capture = this.runtime.store.ring.capturePreRoll({ triggerAt: dispatch?.deadline ?? at + this.config.toleranceMs,
      requestedPreRollMs: dispatch ? dispatch.deadline - at : this.config.toleranceMs * 2,
      filter: r => r.payload?.kind === 'cardinal4_capture_manifest' });
    const candidates = capture.records.filter(r => {
      if (beforeMs !== null && Date.parse(r.observedAt) >= beforeMs) return false;
      try { const m = validateVisualManifest(r.payload); return sameExperiment(m.identity, this.config.identity) && (dispatch === null || m.captureId === dispatch.captureId); }
      catch { return false; }
    }).sort((a, b) => Math.abs(Date.parse(a.observedAt) - at) - Math.abs(Date.parse(b.observedAt) - at) ||
      a.observationId.localeCompare(b.observationId));
    const record = candidates[0]; if (!record) return null;
    const m = validateVisualManifest(record.payload);
    return { status: m.result.status === 'COMPLETE' ? 'PRESENT' : 'PRESENT_PARTIAL', reason: null,
      match: { basis: dispatch ? 'DISPATCHED_CAPTURE_ID_WITHIN_REQUEST_WINDOW' : 'RETAINED_MANIFEST_WITHIN_TOLERANCE',
        observedAt: record.observedAt, offsetFromRequestedMs: Date.parse(record.observedAt) - at },
      sourceObservationId: record.observationId, captureId: m.captureId, captureStatus: m.result.status,
      imageHashes: m.result.frames.filter(f => f.status === 'PRESENT').map(f => f.imageHash) };
  }
  async poll(nowMs) {
    integer(nowMs, 0, Number.MAX_SAFE_INTEGER);
    if (this.lastPoll !== null) require(nowMs >= this.lastPoll, 'TRIGGER_CLOCK_REVERSED');
    this.lastPoll = nowMs;
    const complete = [];
    for (const [id, window] of this.windows) {
      for (const slot of window.slots) {
        if (!['WAITING', 'DISPATCHED'].includes(slot.status)) continue;
        const retained = slot.status === 'DISPATCHED' && slot.dispatch === null ? null
          : this.#find(slot.at, slot.dispatch);
        if (retained) { Object.assign(slot, retained); continue; }
        if (this.closed || nowMs >= window.deadline) {
          slot.reason = this.closed ? 'OWNER_CLOSED' : 'WINDOW_DEADLINE';
          slot.status = slot.status === 'DISPATCHED' ? 'OUTCOME_UNKNOWN' : 'MISSING';
        } else if (slot.status === 'WAITING' && nowMs >= slot.at) {
          if (!this.requestCapture || this.dispatched >= this.config.captureBudget) {
            slot.status = 'MISSING'; slot.reason = this.requestCapture ? 'CAPTURE_BUDGET_EXHAUSTED' : 'CAPTURE_NOT_CONFIGURED';
          } else {
            slot.status = 'DISPATCHED'; this.dispatched++;
            // A capture set consumes four image slots in the independently enforced runtime owner grant.
            const command = Object.freeze({ captureId: 'capture-' + createHash('sha256').update(`${id}:${slot.offsetMs}`).digest('hex').slice(0, 48),
              triggerCaptureId: id, triggerObservationId: window.observationId,
              offsetMs: slot.offsetMs, requestedAt: slot.at, deadline: window.deadline,
              identity: structuredClone(window.identity), rig: 'cardinal-4-snapshot-v1', imageCost: 4 });
            const failed = () => {
              if (this.windows.has(id) && slot.status === 'DISPATCHED') {
                slot.status = 'OUTCOME_UNKNOWN'; slot.reason = 'CAPTURE_COMPLETION_UNKNOWN';
              }
            };
            try {
              // Dispatch immediately on this existing owner poll. The registered runtime handler must enforce the supplied deadline.
              Promise.resolve(this.requestCapture(command)).then(result => {
                if (this.windows.has(id) && slot.status === 'DISPATCHED')
                  slot.dispatch = { captureId: result?.captureId ?? command.captureId, requestedAt: slot.at, deadline: window.deadline };
                // An acknowledgement is not retained evidence. Only #find can mark a slot PRESENT.
              }, failed);
            } catch { failed(); }
          }
        }
      }
      if (window.slots.every(s => !['WAITING', 'DISPATCHED'].includes(s.status))) {
        complete.push({ schemaVersion: 1, kind: 'trigger_visual_window', captureId: id,
          identity: structuredClone(window.identity), triggerKind: window.kind,
          triggerObservationId: window.observationId, triggerAt: window.observedAt,
          sameFrame: false, slots: structuredClone(window.slots),
          outcome: window.slots.every(s => s.status === 'PRESENT') ? 'COMPLETE' : 'PARTIAL',
          config: { ...structuredClone(this.config), identity: structuredClone(window.identity) }, ringCoverage: this.runtime.store.ring.coverage(),
          canonicalCut: this.runtime.store.canonicalPrefixProof(),
          semantics: { windowClock: 'WALL_CLOCK_CORRELATION_NOT_CAUSAL_ORDER',
            captureBudgetUnit: 'FOUR_FRAME_CAPTURE_SETS', automaticRetry: false,
            rawEvidenceDuplicated: false, visualVerdict: 'NOT_RUN', behaviorVerdict: 'NOT_RUN' } });
        this.windows.delete(id);
      }
    }
    // Let already settled callbacks report failure; never await an unresolved capture.
    await Promise.resolve(); await Promise.resolve();
    return complete;
  }
  close() { this.closed = true; }
}
export async function persistTriggerWindow(runtime, manifest) {
  require(manifest?.kind === 'trigger_visual_window' && manifest.schemaVersion === 1, 'INVALID_TRIGGER_WINDOW');
  exactKeys(manifest, ['schemaVersion', 'kind', 'captureId', 'identity', 'triggerKind', 'triggerObservationId',
    'triggerAt', 'sameFrame', 'slots', 'outcome', 'config', 'ringCoverage', 'canonicalCut', 'semantics'], 'TRIGGER_MANIFEST');
  identifier(manifest.captureId); require(/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(manifest.captureId), 'SAFE_CAPTURE_ID_REQUIRED'); validateVisualIdentity(manifest.identity);
  const config = validateTriggerConfig(manifest.config, runtime);
  require(stableJson(config.identity) === stableJson(manifest.identity) && config.triggerKinds.includes(manifest.triggerKind) &&
    manifest.sameFrame === false && ['COMPLETE', 'PARTIAL'].includes(manifest.outcome), 'TRIGGER_MANIFEST_IDENTITY');
  const trigger = runtime.store.observationById.get(manifest.triggerObservationId);
  require(typeof trigger === 'string' && JSON.parse(trigger).observedAt === manifest.triggerAt &&
    stableJson(JSON.parse(trigger).payload.identity) === stableJson(manifest.identity), 'TRIGGER_SOURCE_MISMATCH');
  require(Array.isArray(manifest.slots) && manifest.slots.length === config.offsetsMs.length, 'TRIGGER_SLOT_COUNT');
  manifest.slots.forEach((slot, i) => {
    exactKeys(slot, ['offsetMs', 'at', 'status', 'reason', 'sourceObservationId', 'captureId', 'imageHashes', 'captureStatus', ...(Object.hasOwn(slot, 'dispatch') ? ['dispatch'] : []), ...(Object.hasOwn(slot, 'match') ? ['match'] : [])], 'TRIGGER_SLOT');
    require(slot.offsetMs === config.offsetsMs[i] && slot.at === Date.parse(manifest.triggerAt) + slot.offsetMs &&
      ['PRESENT', 'PRESENT_PARTIAL', 'MISSING', 'OUTCOME_UNKNOWN'].includes(slot.status), 'TRIGGER_SLOT_IDENTITY');
    if (slot.dispatch != null) {
      exactKeys(slot.dispatch, ['captureId', 'requestedAt', 'deadline'], 'TRIGGER_DISPATCH');
      identifier(slot.dispatch.captureId);
      require(slot.offsetMs >= 0 && slot.dispatch.requestedAt === slot.at &&
        slot.dispatch.deadline === Date.parse(manifest.triggerAt) + config.timeoutMs, 'TRIGGER_DISPATCH_WINDOW_MISMATCH');
    }
    if (slot.status.startsWith('PRESENT')) {
      const raw = runtime.store.observationById.get(slot.sourceObservationId);
      require(typeof raw === 'string', 'TRIGGER_FRAME_SOURCE_MISSING');
      const source = JSON.parse(raw);
      const observedAt = Date.parse(source.observedAt);
      require(Number.isFinite(observedAt) && (slot.offsetMs >= 0 || observedAt < Date.parse(manifest.triggerAt)) && (slot.dispatch
        ? slot.captureId === slot.dispatch.captureId && observedAt >= slot.at && observedAt <= slot.dispatch.deadline
        : Math.abs(observedAt - slot.at) <= config.toleranceMs), 'TRIGGER_FRAME_TIME_OUTSIDE_WINDOW');
      if (slot.match != null || slot.dispatch != null) {
        exactKeys(slot.match, ['basis', 'observedAt', 'offsetFromRequestedMs'], 'TRIGGER_MATCH');
        require(slot.match.observedAt === source.observedAt && slot.match.offsetFromRequestedMs === observedAt - slot.at &&
          slot.match.basis === (slot.dispatch ? 'DISPATCHED_CAPTURE_ID_WITHIN_REQUEST_WINDOW' : 'RETAINED_MANIFEST_WITHIN_TOLERANCE'),
          'TRIGGER_ACTUAL_TIME_OR_MATCH_BASIS_MISMATCH');
      }
      const captured = validateVisualManifest(source.payload);
      require(sameExperiment(captured.identity, manifest.identity) && captured.captureId === slot.captureId &&
        captured.result.status === slot.captureStatus &&
        stableJson(captured.result.frames.filter(f => f.status === 'PRESENT').map(f => f.imageHash)) === stableJson(slot.imageHashes),
        'TRIGGER_FRAME_BINDING_MISMATCH');
    } else require(slot.sourceObservationId === null && slot.captureId === null && slot.imageHashes.length === 0 &&
      slot.captureStatus === null && slot.match == null && typeof slot.reason === 'string', 'MISSING_TRIGGER_FRAME_HAS_EVIDENCE');
  });
  require(manifest.outcome === (manifest.slots.every(slot => slot.status === 'PRESENT') ? 'COMPLETE' : 'PARTIAL'), 'FALSE_TRIGGER_COMPLETION');
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch'])
    require(manifest.identity[key] === runtime[key], 'FOREIGN_TRIGGER_RUN');
  require(stableJson(manifest.canonicalCut) === stableJson(runtime.store.canonicalPrefixProof()) &&
    stableJson(manifest.ringCoverage) === stableJson(runtime.store.ring.coverage()), 'TRIGGER_CANONICAL_PROOF_MISMATCH');
  require(stableJson(manifest.semantics) === stableJson({ windowClock: 'WALL_CLOCK_CORRELATION_NOT_CAUSAL_ORDER',
    captureBudgetUnit: 'FOUR_FRAME_CAPTURE_SETS', automaticRetry: false, rawEvidenceDuplicated: false,
    visualVerdict: 'NOT_RUN', behaviorVerdict: 'NOT_RUN' }), 'FALSE_TRIGGER_SEMANTICS');
  require(manifest.triggerKind === 'AI_EXPLICIT' || JSON.parse(trigger).payload.triggerKind === manifest.triggerKind, 'TRIGGER_KIND_MISMATCH');
  const bytes = Buffer.from(JSON.stringify(manifest, null, 2) + '\n');
  require(bytes.length <= 128 * 1024, 'TRIGGER_WINDOW_TOO_LARGE');
  await runtime.store.assertMutable();
  const dir = path.join(runtime.runDir, 'evidence', 'captures'); await mkdir(dir, { recursive: true });
  const file = path.join(dir, `trigger-${manifest.captureId}.json`);
  await writeFile(file, bytes, { flag: 'wx' });
  return { file, manifest };
}
