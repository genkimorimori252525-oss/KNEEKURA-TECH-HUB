import test from 'node:test';
import assert from 'node:assert/strict';
import { TriggerCaptureController } from '../trigger-capture.mjs';
import { ObservationRingBuffer } from '../ring-buffer.mjs';
const identity = { debugSessionId: 'session', runId: 'run', runSnapshotId: 'snapshot', processEpoch: 1,
  experimentId: 'experiment', generation: 1, requestHash: 'a'.repeat(64), arenaId: 'arena', arenaEpoch: 0,
  arenaRevision: 1, baselineHash: 'b'.repeat(64) };
function record(n, at, payload = {}) {
  return { v: 1, kind: 'observation', observationId: `obs:writer:${n}`, debugSessionId: 'session', runId: 'run',
    runSnapshotId: 'snapshot', processEpoch: 1, arenaEpoch: 0, resourceEpoch: 0, writerId: 'writer', writerSeq: n,
    observedAt: new Date(at).toISOString(), level: 'L1', lane: 'VISUAL_CAPTURE', scope: { kind: 'GLOBAL_HEALTH' },
    source: { side: 'CLIENT', method: 'test' }, epistemicStatus: 'OBSERVED',
    completeness: { status: 'COMPLETE', complete: true }, payload };
}
function fixture(dispatch = null) {
  const ring = new ObservationRingBuffer({ maxRecords: 100, maxAgeMs: 10000 });
  const observationById = new Map();
  const runtime = { ...identity, store: { ring, observationById, canonicalPrefixProof: () => ({ count: observationById.size }) } };
  const add = r => { ring.push(r); observationById.set(r.observationId, JSON.stringify(r)); return r; };
  const trigger = add(record(1, 5000, { triggerKind: 'DAMAGE', identity }));
  const controller = new TriggerCaptureController(runtime, { enabled: true, identity,
    triggerKinds: ['DAMAGE', 'AI_EXPLICIT'], offsetsMs: [-1000, 0, 1000], toleranceMs: 200,
    cooldownMs: 1000, maxWindows: 2, captureBudget: 2, timeoutMs: 3000 }, dispatch);
  return { controller, runtime, add, trigger };
}
test('pre-roll never invents an image and unsupported future capture is explicit', async () => {
  const { controller, trigger } = fixture(); controller.trigger('DAMAGE', trigger.observationId, 'trigger-1');
  const [m] = await controller.poll(9000);
  assert.equal(m.slots.length, 3); assert.ok(m.slots.every(s => s.status === 'MISSING'));
  assert.equal(m.sameFrame, false); assert.equal(m.outcome, 'PARTIAL');
});
test('one bounded dispatch per future slot and no retry after uncertain result', async () => {
  const calls = []; const { controller, trigger } = fixture(async slot => { calls.push(slot); throw Error('lost'); });
  controller.trigger('DAMAGE', trigger.observationId, 'trigger-1');
  await controller.poll(5000); await controller.poll(6000); const [m] = await controller.poll(9000);
  assert.equal(calls.length, 2); assert.equal(m.slots[1].status, 'OUTCOME_UNKNOWN');
  assert.equal(m.slots[2].status, 'OUTCOME_UNKNOWN');
  assert.throws(() => controller.trigger('DAMAGE', trigger.observationId, 'trigger-1'));
});
test('unresolved dispatch is bounded by existing owner polls, never awaited forever', async () => {
  let called = 0; const { controller, trigger } = fixture(() => { called++; return new Promise(() => {}); });
  controller.trigger('DAMAGE', trigger.observationId, 'trigger-1');
  await controller.poll(5000); const [m] = await controller.poll(9000);
  assert.equal(called, 1); assert.equal(m.slots[1].status, 'OUTCOME_UNKNOWN');
});
test('trigger identity and kind must belong to canonical retained observation', () => {
  const { controller, add } = fixture();
  add(record(2, 5000, { triggerKind: 'DAMAGE', identity: { ...identity, requestHash: 'c'.repeat(64) } }));
  assert.throws(() => controller.trigger('DAMAGE', 'obs:writer:2', 'trigger-2'));
  assert.throws(() => controller.trigger('EXCEPTION', 'obs:writer:1', 'trigger-3'));
  assert.throws(() => controller.trigger('DAMAGE', 'obs:missing', 'trigger-4'));
});
test('no scheduler or observer is enabled by default', () => {
  const { runtime } = fixture();
  assert.throws(() => new TriggerCaptureController(runtime, { enabled: false }));
});

test('declared canonical trigger is consumed once on existing owner polling', () => {
  const { controller, add } = fixture();
  assert.equal(controller.observeDeclaredTriggers().length, 0, 'arming never replays old trigger rows');
  add(record(2, 6000, { triggerKind: 'DAMAGE', identity }));
  assert.equal(controller.observeDeclaredTriggers().length, 1);
  assert.equal(controller.observeDeclaredTriggers().length, 0);
});

test('derived runtime capture IDs stay bounded for maximum-length trigger IDs', async () => {
  const calls = []; const { controller, trigger } = fixture(command => { calls.push(command); });
  controller.trigger('DAMAGE', trigger.observationId, 'x'.repeat(128));
  await controller.poll(5000);
  assert.equal(calls.length, 1);
  assert.match(calls[0].captureId, /^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/);
});

test('a slower dispatched capture binds its exact acknowledged native ID within the deadline', async () => {
  const {manifest}=await import('./visual-capture-fixtures.mjs');
  const f=fixture(()=>({captureId:'native-fixed-slot'}));
  f.controller.trigger('DAMAGE',f.trigger.observationId,'slow-window');
  await f.controller.poll(5000);
  const m=manifest(); m.captureId='native-fixed-slot';m.identity=identity;
  m.frames.forEach(frame=>{frame.captureId=m.captureId;frame.identity=identity;});
  f.add(record(2,5500,m));
  const windows=await f.controller.poll(9000);
  assert.equal(windows[0].slots[1].status,'PRESENT');
  assert.equal(windows[0].slots[1].captureId,'native-fixed-slot');
  assert.equal(windows[0].slots[1].match.offsetFromRequestedMs,500);
  assert.equal(windows[0].slots[1].match.observedAt,new Date(5500).toISOString());
  assert.equal(windows[0].slots[1].match.basis,'DISPATCHED_CAPTURE_ID_WITHIN_REQUEST_WINDOW');
});

test('window identity records actual canonical trigger revision after arming', async () => {
  const f=fixture(); const actual={...identity,arenaRevision:identity.arenaRevision+1};
  f.add(record(2,6000,{triggerKind:'DAMAGE',identity:actual}));
  f.controller.observeDeclaredTriggers();
  const [window]=await f.controller.poll(10000);
  assert.deepEqual(window.identity,actual);
  assert.deepEqual(window.config.identity,actual);
});

test('negative pre-roll slots never use a retained source after the actual trigger', async () => {
  const {manifest}=await import('./visual-capture-fixtures.mjs');const f=fixture();
  const m=manifest();m.identity=identity;m.frames.forEach(frame=>{frame.identity=identity;});
  f.add(record(2,5050,m));
  const controller=new TriggerCaptureController(f.runtime,{...f.controller.config,offsetsMs:[-100],captureBudget:0});
  controller.trigger('DAMAGE',f.trigger.observationId,'pre-window');
  const [window]=await controller.poll(5100);
  assert.equal(window.slots[0].status,'MISSING');
});

test('canonical native sub-millisecond trigger timestamp is retained verbatim', async () => {
  const f=fixture(),event=record(2,6000,{triggerKind:'DAMAGE',identity});
  event.observedAt='1970-01-01T00:00:06.123456Z';f.add(event);
  f.controller.observeDeclaredTriggers();const [window]=await f.controller.poll(10000);
  assert.equal(window.triggerAt,event.observedAt);
});

test('negative slots reject sub-millisecond later images in the same quantized millisecond', async () => {
  const {manifest}=await import('./visual-capture-fixtures.mjs');const f=fixture();
  const trigger=record(2,6000,{triggerKind:'DAMAGE',identity});trigger.observedAt='1970-01-01T00:00:06.123100Z';f.add(trigger);
  const m=manifest();m.identity=identity;m.frames.forEach(frame=>{frame.identity=identity;});
  const visual=record(3,6000,m);visual.observedAt='1970-01-01T00:00:06.123900Z';f.add(visual);
  const controller=new TriggerCaptureController(f.runtime,{...f.controller.config,offsetsMs:[-1],captureBudget:0});
  controller.trigger('DAMAGE',trigger.observationId,'sub-ms-pre-window');
  const [window]=await controller.poll(7000);
  assert.equal(window.slots[0].status,'MISSING');
  assert.equal(window.triggerAt,trigger.observedAt);
});
