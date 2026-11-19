import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, rename, rm, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { finalizeEvidenceRun } from '../finalize.mjs';
import { evidenceRuntimeFromCurrent } from '../runtime.mjs';
import { retainVisualManifest } from '../visual-capture.mjs';
import { TriggerCaptureController, persistTriggerWindow } from '../trigger-capture.mjs';
import { sha256 } from '../../bridge/json.mjs';
import { fixture } from './visual-fixture.mjs';

function current(f) { return { ...f.manifest.identity, runDir: f.runDir, live: false, status: 'STOPPED' }; }
function runtime(f) { return { ...current(f), store: f.store }; }
function finalize(f) { return finalizeEvidenceRun(current(f), { cleanShutdown: true }); }
async function retainVisual(f) {
  const bytes = Buffer.from(JSON.stringify(f.manifest, null, 2) + '\n');
  const retained = await retainVisualManifest(runtime(f), bytes, f.sourceObservationId);
  return { ...retained, bytes };
}
async function addTrigger(f, at = '2026-10-01T00:00:00.000Z') {
  return (await f.store.appendObservation({ observationId: 'obs:trigger:1', processEpoch: 1,
    arenaEpoch: 0, resourceEpoch: 0, writerId: 'trigger', writerSeq: 1, level: 'L2', lane: 'TRIGGER',
    observedAt: at, scope: { kind: 'EXPERIMENT', experimentId: f.manifest.identity.experimentId },
    source: { side: 'CLIENT', method: 'source_fixture' }, epistemicStatus: 'OBSERVED',
    completeness: { complete: true }, payload: { triggerKind: 'DAMAGE', identity: f.manifest.identity } })).record;
}
async function retainTrigger(f, { offsetsMs = [0], dispatch = null, at, captureBudget = 0 } = {}) {
  const row = await addTrigger(f, at);
  const owner = runtime(f);
  const controller = new TriggerCaptureController(owner, { enabled: true, identity: f.manifest.identity,
    triggerKinds: ['DAMAGE'], offsetsMs, toleranceMs: 100, cooldownMs: 1000,
    maxWindows: 1, captureBudget, timeoutMs: 2000 }, dispatch);
  controller.trigger('DAMAGE', row.observationId, 'window-1');
  const completed = await controller.poll(Date.parse(row.observedAt));
  completed.push(...await controller.poll(Date.parse(row.observedAt) + 2000));
  assert.equal(completed.length, 1);
  const [manifest] = completed;
  return persistTriggerWindow(owner, manifest);
}
async function tamper(file, change) {
  const value = JSON.parse(await readFile(file, 'utf8')); change(value);
  await writeFile(file, JSON.stringify(value, null, 2) + '\n');
}
function partial(m) {
  m.result.status = 'PARTIAL'; m.result.gaps = ['DEADLINE_EXPIRED'];
  m.frames = m.frames.slice(0, 1);
  m.result.frames = m.result.frames.map((frame, i) => i ?
    { view: frame.view, status: 'MISSING', renderFrame: null, imageHash: null, observationHash: null } : frame);
}

test('finalization refuses an export-incompatible inventory even without derived visuals', async t => {
  const f = await fixture(t);
  const raw = path.join(f.runDir, 'evidence', 'raw');
  await mkdir(raw, { recursive: true });
  for (let i = 0; i < 1025; i++) await writeFile(path.join(raw, `inventory-${i}.bin`), 'x');
  await assert.rejects(finalize(f), /FINALIZATION_INVENTORY_LIMIT/);
  await assert.rejects(readFile(f.store.finalizationFile), { code: 'ENOENT' });
});

test('finalizes actual retained visual and trigger manifests alongside replayed pre-roll without rewriting sources', async t => {
  const f = await fixture(t); const visual = await retainVisual(f); const trigger = await retainTrigger(f);
  const r = evidenceRuntimeFromCurrent(current(f)); await r.init();
  const preRoll = await r.capturePreRoll({ captureId: 'pre-1', triggerAt: '2026-10-01T00:00:00.000Z', requestedPreRollMs: 0 });
  const retainedFiles = [visual.file, trigger.file, preRoll.file];
  const before = await Promise.all(retainedFiles.map(file => readFile(file)));
  const { manifest: result } = await finalize(f);
  assert.equal(result.status, 'EVIDENCE_COMPLETE');
  assert.equal(result.counts.captureManifests, 3); assert.equal(result.counts.partialCaptures, 0);
  assert.equal(result.captures.coverageStatus, 'COMPLETE');
  assert.deepEqual(result.captures.byKind, { pre_roll_capture: 1, cardinal4_capture_manifest: 1, trigger_visual_window: 1 });
  const visualSummary = result.captures.records.find(row => row.kind === 'cardinal4_capture_manifest');
  assert.equal(visualSummary.status, 'COMPLETE'); assert.equal(visualSummary.restoration, 'RESTORED');
  assert.deepEqual(visualSummary.sourceObservationIds, [f.sourceObservationId]);
  for (const [i, file] of retainedFiles.entries()) {
    assert.deepEqual(await readFile(file), before[i]);
    assert.equal(result.artifacts.find(artifact => artifact.path === file).sha256, 'sha256:' + sha256(before[i]));
  }
  for (const frame of f.manifest.frames) {
    const artifact = result.artifacts.find(item => item.path === path.join(f.runDir, frame.imagePath));
    assert.equal(artifact?.sha256, 'sha256:' + frame.imageHash);
  }
  assert.equal((await finalize(f)).alreadyFinalized, true);
});

for (const status of ['PARTIAL', 'UNKNOWN']) test(`retained ${status} visuals preserve restoration and trigger coverage uncertainty`, async t => {
  const f = await fixture(t, { mutate: m => {
    partial(m);
    if (status === 'UNKNOWN') { m.result.status = 'UNKNOWN'; m.result.restoration = 'UNKNOWN'; delete m.restorationProof.observed; }
  } });
  await retainVisual(f); await retainTrigger(f, { offsetsMs: [-1000, 0] });
  const { manifest: result } = await finalize(f);
  assert.equal(result.captures.partialCount, 2); assert.equal(result.counts.partialCaptures, 2);
  assert.equal(result.captures.coverageStatus, status);
  assert.equal(result.captures.unknownCount, status === 'UNKNOWN' ? 2 : 0);
  const visual = result.captures.records.find(row => row.kind === 'cardinal4_capture_manifest');
  assert.equal(visual.status, status); assert.equal(visual.restoration, f.manifest.result.restoration);
  const trigger = result.captures.records.find(row => row.kind === 'trigger_visual_window');
  assert.equal(trigger.outcome, 'PARTIAL'); assert.equal(trigger.status, status);
  assert.deepEqual(trigger.slotCounts, { PRESENT: 0, PRESENT_PARTIAL: 1, MISSING: 1, OUTCOME_UNKNOWN: 0 });
  assert.ok(result.limitations.some(line => /visual|trigger/i.test(line)));
  if (status === 'UNKNOWN') assert.ok(result.limitations.some(line => /unknown|uncertain/i.test(line)));
});

test('unresolved dispatched trigger remains unknown through real retention and finalization', async t => {
  const f = await fixture(t); await retainVisual(f);
  const window = await retainTrigger(f, { at: '2026-10-01T00:00:01.000Z', dispatch: () => new Promise(() => {}), captureBudget: 1 });
  assert.equal(window.manifest.slots[0].status, 'OUTCOME_UNKNOWN');
  const { manifest: result } = await finalize(f);
  assert.equal(result.captures.coverageStatus, 'UNKNOWN'); assert.equal(result.captures.unknownCount, 1);
  assert.equal(result.captures.records.find(row => row.kind === 'trigger_visual_window').slotCounts.OUTCOME_UNKNOWN, 1);
});

test('trigger proof binds its retained canonical prefix when later rows are appended', async t => {
  const f = await fixture(t); await retainVisual(f); const trigger = await retainTrigger(f);
  await f.store.heartbeat({ processEpoch: 1, observedAt: '2026-10-01T00:00:01.000Z' });
  const { manifest: result } = await finalize(f);
  const summary = result.captures.records.find(row => row.kind === 'trigger_visual_window');
  assert.deepEqual(summary.canonicalCut, trigger.manifest.canonicalCut);
  assert.equal(summary.canonicalCut.count, 2); assert.equal(result.counts.observations, 3);
});

for (const [fault, change, expected] of [
  ['source payload', m => { m.barrierDurationMs++; }, /canonical.*binding|source.*mismatch/i],
  ['nested identity', m => { m.identity.processEpoch++; m.frames.forEach(frame => frame.identity.processEpoch++); }, /identity mismatch/i],
  ['restoration', m => { m.restorationProof.observed.paused = true; }, /RESTORATION_NOT_OBSERVED/],
  ['unknown property', m => { m.complete = true; }, /VISUAL_MANIFEST_FIELDS/],
]) test(`finalization rejects retained visual ${fault} tampering`, async t => {
  const f = await fixture(t); const visual = await retainVisual(f); await tamper(visual.file, change);
  await assert.rejects(finalize(f), expected);
});

test('finalization rejects a renamed visual manifest and mutated immutable raw image', async t => {
  const f = await fixture(t); const visual = await retainVisual(f);
  const renamed = path.join(path.dirname(visual.file), 'visual-other.json'); await rename(visual.file, renamed);
  await assert.rejects(finalize(f), /filename\/id mismatch/i);
  await rename(renamed, visual.file);
  await writeFile(path.join(f.runDir, f.manifest.frames[0].imagePath), Buffer.from('corrupt PNG'));
  await assert.rejects(finalize(f), /HASH|PNG/);
});

for (const [fault, change, expected] of [
  ['canonical prefix', m => { m.canonicalCut.canonicalRecordsSha256 = 'sha256:' + '0'.repeat(64); }, /canonical prefix proof mismatch/i],
  ['ring coverage', m => { m.ringCoverage.retainedRecords++; }, /ring coverage.*mismatch/i],
  ['trigger source', m => { m.triggerObservationId = 'obs:missing'; }, /trigger source.*missing|trigger source.*mismatch/i],
  ['slot source', m => { m.slots[0].sourceObservationId = 'obs:missing'; }, /trigger frame source.*missing/i],
  ['image hash', m => { m.slots[0].imageHashes[0] = '0'.repeat(64); }, /trigger frame binding mismatch/i],
  ['slot time', m => { m.slots[0].at++; }, /trigger slot identity/i],
  ['trigger kind', m => { m.triggerKind = 'EXCEPTION'; m.config.triggerKinds = ['EXCEPTION']; }, /trigger kind mismatch/i],
  ['semantics', m => { m.semantics.visualVerdict = 'PASS'; }, /trigger semantics/i],
]) test(`finalization rejects retained trigger ${fault} tampering`, async t => {
  const f = await fixture(t); await retainVisual(f); const trigger = await retainTrigger(f);
  await tamper(trigger.file, change); await assert.rejects(finalize(f), expected);
});

test('finalization rejects a forged PRESENT slot for an actual partial visual', async t => {
  const f = await fixture(t, { mutate: partial }); await retainVisual(f); const trigger = await retainTrigger(f);
  await tamper(trigger.file, m => { m.slots[0].status = 'PRESENT'; m.outcome = 'COMPLETE'; });
  await assert.rejects(finalize(f), /trigger.*(status|completion|binding)/i);
});

test('pre-roll replay and unsupported retained kinds still fail closed', async t => {
  const f = await fixture(t); const r = evidenceRuntimeFromCurrent(current(f)); await r.init();
  const pre = await r.capturePreRoll({ captureId: 'pre-1', triggerAt: '2026-10-01T00:00:00.000Z', requestedPreRollMs: 0 });
  await tamper(pre.file, m => { m.coverage.selectedRecords++; });
  await assert.rejects(finalize(f), /capture coverage replay mismatch/);
  await rm(pre.file);
  await writeFile(path.join(path.dirname(pre.file), 'unsupported.json'), JSON.stringify({ kind: 'future_capture' }));
  await assert.rejects(finalize(f), /unsupported capture manifest kind/i);
});

test('unknown frame writes stay partial and do not acquire a durable image claim', async t => {
  const f = await fixture(t, { mutate: m => {
    m.result.status = 'PARTIAL'; m.result.gaps = ['WRITE_UNCONFIRMED'];
    m.result.frames[3].status = 'WRITE_UNKNOWN'; m.result.frames[3].observationHash = null;
  } });
  await rm(path.join(f.runDir, f.manifest.frames[3].imagePath));
  await retainVisual(f); await retainTrigger(f);
  const { manifest: result } = await finalize(f);
  assert.equal(result.captures.coverageStatus, 'PARTIAL');
  const summary = result.captures.records.find(row => row.kind === 'cardinal4_capture_manifest');
  assert.deepEqual(summary.viewCounts, { PRESENT: 3, WRITE_UNKNOWN: 1, MISSING: 0 });
  assert.equal(result.artifacts.filter(row => row.path.endsWith('.png')).length, 3);
});

test('trigger-only retention seals canonical source images without inventing a visual manifest file', async t => {
  const f = await fixture(t); await retainTrigger(f);
  const { manifest: result } = await finalize(f);
  assert.equal(result.counts.captureManifests, 1);
  assert.equal(result.captures.byKind.cardinal4_capture_manifest, 0);
  assert.equal(result.captures.coverageStatus, 'COMPLETE');
  assert.equal(result.artifacts.filter(row => row.path.endsWith('.png')).length, 4);
});
for(const fault of ['scope','arena','epistemic','completeness'])test(`visual seal requires complete observed outer source identity: ${fault}`,async t=>{
 const f=await fixture(t);await retainVisual(f);
 const rows=(await readFile(f.store.evidenceFile,'utf8')).trim().split('\n').map(JSON.parse);const row=rows[0];
 if(fault==='scope')row.scope={kind:'EXPERIMENT',experimentId:'foreign'};
 if(fault==='arena')row.arenaEpoch++;
 if(fault==='epistemic')row.epistemicStatus='DERIVED';
 if(fault==='completeness'){row.completeness.complete=false;row.completeness.status='PARTIAL';}
 await writeFile(f.store.evidenceFile,rows.map(JSON.stringify).join('\n')+'\n');
 await assert.rejects(finalize(f),/visual observation source/);
});

for (const corrupt of [false,true]) test(`dispatched capture finalization preserves actual delayed time (tampered=${corrupt})`, async t => {
  const f=await fixture(t);const owner=runtime(f),row=await addTrigger(f,'2026-09-30T23:59:59.500Z');
  const controller=new TriggerCaptureController(owner,{enabled:true,identity:f.manifest.identity,triggerKinds:['DAMAGE'],
    offsetsMs:[0],toleranceMs:100,cooldownMs:1000,maxWindows:1,captureBudget:1,timeoutMs:2000},
    ()=>({captureId:f.manifest.captureId}));
  controller.trigger('DAMAGE',row.observationId,'delayed-window');
  await controller.poll(Date.parse(row.observedAt));
  const [manifest]=await controller.poll(Date.parse(row.observedAt)+500);
  assert.equal(manifest.slots[0].match.offsetFromRequestedMs,500);
  const retained=await persistTriggerWindow(owner,manifest);
  if(corrupt){await tamper(retained.file,m=>{m.slots[0].match.offsetFromRequestedMs=0;});
    await assert.rejects(finalize(f),/actual time|match basis/);
  }else{const result=await finalize(f);assert.equal(result.manifest.captures.records[0].status,'COMPLETE');}
});
