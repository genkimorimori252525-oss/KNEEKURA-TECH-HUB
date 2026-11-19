import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { persistTriggerWindow } from '../trigger-capture.mjs';
import { manifest } from './visual-capture-fixtures.mjs';

test('retention rejects old visuals reassigned to a new trigger slot', async t => {
  const runDir = await mkdtemp(path.join(tmpdir(), 'trigger-retention-'));
  t.after(() => rm(runDir, { recursive: true, force: true }));
  const m = manifest();
  const proof = { count: 2 }; const coverage = { maxRecords: 10 };
  const source = { observedAt: new Date(1000).toISOString(), payload: m };
  const trigger = { observedAt: new Date(5000).toISOString(), payload: { identity: m.identity, triggerKind: 'DAMAGE' } };
  const runtime = { ...m.identity, runDir, store: { observationById: new Map([
    ['obs:source', JSON.stringify(source)], ['obs:trigger', JSON.stringify(trigger)]]),
    ring: { coverage: () => coverage }, canonicalPrefixProof: () => proof, assertMutable: async () => {} } };
  const window = { schemaVersion: 1, kind: 'trigger_visual_window', captureId: 'retained', identity: m.identity,
    triggerKind: 'DAMAGE', triggerObservationId: 'obs:trigger', triggerAt: trigger.observedAt, sameFrame: false,
    slots: [{ offsetMs: 0, at: 5000, status: 'PRESENT', reason: null, sourceObservationId: 'obs:source',
      captureId: m.captureId, imageHashes: m.frames.map(f => f.imageHash), captureStatus: 'COMPLETE' }], outcome: 'COMPLETE',
    config: { enabled: true, identity: m.identity, triggerKinds: ['DAMAGE'], offsetsMs: [0], toleranceMs: 200,
      cooldownMs: 1000, maxWindows: 1, captureBudget: 0, timeoutMs: 1000 }, ringCoverage: coverage, canonicalCut: proof,
    semantics: { windowClock: 'WALL_CLOCK_CORRELATION_NOT_CAUSAL_ORDER', captureBudgetUnit: 'FOUR_FRAME_CAPTURE_SETS',
      automaticRetry: false, rawEvidenceDuplicated: false, visualVerdict: 'NOT_RUN', behaviorVerdict: 'NOT_RUN' } };
  await assert.rejects(persistTriggerWindow(runtime, window), /TIME|WINDOW/);
  source.observedAt = trigger.observedAt; runtime.store.observationById.set('obs:source', JSON.stringify(source));
  assert.equal((await persistTriggerWindow(runtime, window)).manifest.outcome, 'COMPLETE');
  window.captureId = 'forged-proof'; window.canonicalCut = { count: 3 };
  await assert.rejects(persistTriggerWindow(runtime, window), /PROOF/);
});
