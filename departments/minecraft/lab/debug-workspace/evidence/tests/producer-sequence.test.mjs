import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { EvidenceStore } from '../store.mjs';

function row(writerSeq, overrides = {}) {
  return { observationId: 'obs:producer:' + writerSeq, processEpoch: 1, arenaEpoch: 0,
    resourceEpoch: 0, writerId: 'forge-runtime:42', writerSeq, producerDeltaApplied: true,
    level: 'L1', lane: 'SERVER_TICK', observedAt: '2026-10-01T00:00:00.000Z',
    gameTime: writerSeq, scope: { kind: 'ENTITY_UUID', entityUuid: '00000000-0000-0000-0000-000000000001' }, source: { side: 'SERVER', method: 'sequence-test' },
    epistemicStatus: 'OBSERVED', completeness: { complete: true }, payload: { tick: writerSeq }, ...overrides };
}
async function fixture(t) {
  const runDir = await mkdtemp(path.join(os.tmpdir(), 'lab-producer-sequence-'));
  t.after(() => rm(runDir, { recursive: true, force: true }));
  const options = { runDir, debugSessionId: 'session', runId: 'run' };
  const store = new EvidenceStore(options); await store.init(); return { store, options };
}
const drops = store => store.lanes.snapshot().reduce((sum, lane) => sum + lane.dropped, 0);

test('producer sequence remains continuous across arena reset and resource epoch, including rehydration', async t => {
  const { store, options } = await fixture(t);
  await store.appendObservation(row(1)); await store.appendObservation(row(2));
  await store.appendObservation(row(3, { arenaEpoch: 1 }));
  await store.appendObservation(row(4, { arenaEpoch: 1, resourceEpoch: 1 }));
  assert.equal(drops(store), 0);
  const reopened = new EvidenceStore(options); await reopened.init(); assert.equal(drops(reopened), 0);
});
test('genuine producer gap across arena reset remains visible after rehydration', async t => {
  const { store, options } = await fixture(t);
  await store.appendObservation(row(1)); await store.appendObservation(row(3, { arenaEpoch: 1 }));
  assert.equal(drops(store), 1);
  const reopened = new EvidenceStore(options); await reopened.init(); assert.equal(drops(reopened), 1);
});
test('a new process has an independent producer sequence', async t => {
  const { store, options } = await fixture(t);
  await store.appendObservation(row(1)); await store.appendObservation(row(2));
  await store.appendObservation(row(1, { processEpoch: 2, arenaEpoch: 1, observationId: 'obs:process2:1' }));
  assert.equal(drops(store), 0);
  const reopened = new EvidenceStore(options); await reopened.init(); assert.equal(drops(reopened), 0);
});
test('producer replay cannot be disguised by changing the arena epoch', async t => {
  const { store } = await fixture(t);
  await store.appendObservation(row(1)); await store.appendObservation(row(2));
  await assert.rejects(store.appendObservation(row(1, { arenaEpoch: 1, observationId: 'obs:replayed' })), /monotonically/);
});
