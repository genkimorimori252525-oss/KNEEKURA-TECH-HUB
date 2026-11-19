import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, access } from 'node:fs/promises';
import path from 'node:path';
import { preparedOwner } from './owner-action-fixture.mjs';
import { captureSlotKey, requestDeclaredCapture } from '../owner-action-adapter.mjs';
import { EvidenceRuntime } from '../../evidence/runtime.mjs';
import * as source from '../owner-trigger-source.mjs';

const config = { enabled: true, triggerKinds: ['ARENA_EXIT'], offsetsMs: [-1000, 0, 1000],
  toleranceMs: 200, cooldownMs: 1000, maxWindows: 1, captureBudget: 1, timeoutMs: 3000, captureIndices: [0] };
async function fixture(t) { return preparedOwner(t, { capture: true, triggerCapture: config }); }
function row(f, at = Date.now(), overrides = {}) {
  const identity = source.ownerTriggerIdentity(f.prepared);
  return { v: 1, kind: 'observation', observationId: 'obs:writer:1', debugSessionId: 's', runId: 'r',
    runSnapshotId: 'snap', processEpoch: 1, arenaEpoch: 0, resourceEpoch: 0, writerId: 'writer', writerSeq: 1,
    observedAt: new Date(at).toISOString(), level: 'L1', lane: 'SERVER_ENTITY_STATE', scope: { kind: 'ENTITY_UUID', entityUuid: f.prepared.grant.subjects[0].uuid },
    source: { side: 'SERVER', method: 'KneekuraDebugOwnerConnection.arena_exit' }, epistemicStatus: 'OBSERVED',
    completeness: { status: 'COMPLETE', complete: true }, payload: { kind: 'owner_trigger_event', triggerKind: 'ARENA_EXIT',
      identity, ownerEnvelopeHash: f.prepared.envelopeHash, triggerConfigHash: f.prepared.envelope.triggerConfigHash,
      subjectId: 'pig', uuid: f.prepared.grant.subjects[0].uuid, transition: 'INSIDE_TO_OUTSIDE', position: [9, 1, 1], previousPosition: [1, 1, 1], ...overrides } };
}
test('private trigger opt-in is sealed, read back and rejects unimplemented kinds and conflicting budgets', async t => {
  const f = await fixture(t);
  assert.deepEqual(f.prepared.triggerCapture, config);
  assert.equal(typeof f.prepared.envelope.triggerConfigHash, 'string');
  assert.throws(() => source.validateOwnerTriggerConfig({ ...config, triggerKinds: ['DAMAGE'] }, f.prepared.grant), /TRIGGER/);
  assert.throws(() => source.validateOwnerTriggerConfig({ ...config, captureIndices: [1] }, f.prepared.grant), /TRIGGER|INTEGER/);
  await writeFile(path.join(f.runDir, 'control/owner-trigger-config.json'), '{}');
  await assert.rejects(source.armOwnerTriggerCapture(new EvidenceRuntime({runDir:f.runDir,...f.identity}), f.controlOptions), /HASH|hash|SHA/);
});
test('opt-in source arms the real runtime and dispatches fixed native slots with event identity/deadline', async t => {
  const f = await fixture(t); const runtime = new EvidenceRuntime({runDir:f.runDir,...f.identity}); await runtime.init();
  await source.armOwnerTriggerCapture(runtime, f.controlOptions);
  const event = row(f); await runtime.store.appendObservation(event);
  runtime.triggerController.observeDeclaredTriggers(); await runtime.triggerController.poll(Date.now());
  await source.drainOwnerTriggerDispatches(runtime);
  const key = captureSlotKey(f.prepared.grant, 0);
  const marker = JSON.parse(await readFile(path.join(f.runDir,'control/captures',key,'request.json')));
  assert.equal(marker.captureId, 'capture-' + key); assert.equal(marker.captureIndex, 0);
  assert.equal(marker.trigger.observationId, event.observationId);
  assert.equal(marker.trigger.deadline, Date.parse(event.observedAt) + config.timeoutMs);
  assert.equal(marker.expectedArenaRevision, event.payload.identity.arenaRevision);
  await assert.rejects(requestDeclaredCapture({...f.controlOptions,captureIndex:0}), /RESERVED/);
  runtime.triggerController.close();
});
test('foreign source and closed owner never dispatch, and uncertain reservation cannot retry', async t => {
  const f = await fixture(t); const runtime = new EvidenceRuntime({runDir:f.runDir,...f.identity}); await runtime.init();
  await source.armOwnerTriggerCapture(runtime, f.controlOptions);
  const event = row(f,Date.now(),{triggerConfigHash:'a'.repeat(64)}); await runtime.store.appendObservation(event);
  await runtime.refresh(); await source.drainOwnerTriggerDispatches(runtime);
  await assert.rejects(access(path.join(f.runDir,'control/captures')));
  f.status.status='OWNER_CLOSED'; await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));
  const valid = {...row(f),observationId:'obs:writer:2',writerSeq:2}; await runtime.store.appendObservation(valid);
  await runtime.refresh(); await source.drainOwnerTriggerDispatches(runtime);
  await assert.rejects(access(path.join(f.runDir,'control/captures')));
});

test('an uncertain trigger reservation consumes its fixed slot without publishing or retrying', async t => {
  const f=await fixture(t),now=Date.now(),trigger={configHash:f.prepared.envelope.triggerConfigHash,kind:'ARENA_EXIT',
    observationId:'obs:writer:1',windowId:'window-1',triggerAt:now,offsetMs:0,deadline:now+config.timeoutMs};
  let checks=0;
  const first=await requestDeclaredCapture({...f.controlOptions,captureIndex:0,trigger,
    expectedIdentity:source.ownerTriggerIdentity(f.prepared),isClosed:()=>++checks>1});
  assert.equal(first.status,'OUTCOME_UNKNOWN');
  await assert.rejects(access(path.join(f.runDir,'control/captures',first.captureKey,'request.json')));
  const retry=await requestDeclaredCapture({...f.controlOptions,captureIndex:0,trigger,
    expectedIdentity:source.ownerTriggerIdentity(f.prepared)});
  assert.equal(retry.status,'ALREADY_RECORDED');
});
test('late or foreign trigger intent never reserves a native capture slot', async t => {
  const f=await fixture(t),now=Date.now(),base={configHash:f.prepared.envelope.triggerConfigHash,kind:'ARENA_EXIT',
    observationId:'obs:writer:1',windowId:'window-1',triggerAt:now,offsetMs:0,deadline:now+config.timeoutMs};
  for(const trigger of [{...base,configHash:'a'.repeat(64)},{...base,triggerAt:now-4000,deadline:now-1000},
    {...base,offsetMs:1000},{...base,deadline:now+config.timeoutMs+1}])
    await assert.rejects(requestDeclaredCapture({...f.controlOptions,captureIndex:0,trigger,expectedIdentity:source.ownerTriggerIdentity(f.prepared)}));
  await assert.rejects(access(path.join(f.runDir,'control/captures')));
});
test('watcher reservation is one-shot and old raw backlog cannot trigger after arming', async t => {
  const f=await fixture(t),runtime=new EvidenceRuntime({runDir:f.runDir,...f.identity});await runtime.init();
  const old=row(f,Date.now()-1000);await source.armOwnerTriggerCapture(runtime,f.controlOptions);
  await runtime.store.appendObservation(old);await runtime.refresh();await source.drainOwnerTriggerDispatches(runtime);
  assert.equal(runtime.triggerController.usedIds.size,0);
  const another=new EvidenceRuntime({runDir:f.runDir,...f.identity});await another.init();
  await assert.rejects(source.armOwnerTriggerCapture(another,f.controlOptions),{code:'EEXIST'});
  await assert.rejects(access(path.join(f.runDir,'control/captures')));
});
