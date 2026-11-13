import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { bindCueToModel, createCue, validateCue, validateCueLifecycle } from '../cue-contract.mjs';
import { createProviderAdapter, validateProviderManifest } from '../provider-adapter.mjs';
import { ACTOR, ASSET, LAYOUT, PROVIDER, TARGET, cue, cueBody, ref } from './fixtures.mjs';

const photon = JSON.parse(readFileSync(new URL('../providers/photon-1.20.1.capabilities.json', import.meta.url)));

test('a valid cue round-trips and its seal detects tampering', () => {
  const c = cue();
  assert.deepEqual(validateCue(c), c);
  assert.throws(() => validateCue({ ...c, params: { ...c.params, intensity: 2 } }), /VFX_CUE_INTEGRITY/);
});

test('cue rejects gameplay authority, determinism overclaims and unknown params', () => {
  assert.throws(() => createCue(cueBody({ gameplayAuthority: 'CLIENT_DECIDES_HIT' })), /VFX_GAMEPLAY_AUTHORITY_REJECTED/);
  assert.throws(() => createCue(cueBody({ seed: { value: 7, determinism: 'DETERMINISTIC' } })), /DETERMINISM_OVERCLAIM/);
  assert.throws(() => cue({ params: { lifetime: 10, shaderSource: 'void main(){}' } }), /FX_PARAMETER_NOT_ALLOWED/);
  assert.throws(() => cue({ params: JSON.parse('{"lifetime":10,"__proto__":1}') }), /FX_PARAMETER_NOT_ALLOWED|INVALID_FX_PARAMS/);
});

test('cue rejects path-like effect ids, placeholder hashes and over-ceiling budgets', () => {
  for (const effectId of ['../../etc/passwd', 'kneekura:../x', 'https://evil/x', 'kneekura:a//b'])
    assert.throws(() => cue({ effectId }), /INVALID_RESOURCE_ID/);
  assert.throws(() => cue({ runtimeAssetHash: 'sha256:<atlas>' }), /INVALID_CONTENT_REF/);
  assert.throws(() => cue({ limits: { ...cueBody().limits, maxParticles: 1_000_000 } }), /CUE_LIMIT_OVER_CEILING/);
  assert.throws(() => cue({ params: { ...cueBody().params, spawnRate: 2000, lifetime: 200 } }), /PARTICLE_BUDGET_EXCEEDED/);
  assert.throws(() => cue({ params: { ...cueBody().params, intensity: 4 }, limits: { ...cueBody().limits, maxCumulativeGlow: 2 } }), /GLOW_BUDGET_EXCEEDED/);
});

test('terminal cues carry no duration; live cues must be bounded', () => {
  assert.throws(() => cue({ eventKind: 'CANCEL' }), /TERMINAL_CUE_HAS_DURATION/);
  assert.ok(cue({ eventKind: 'CANCEL', timing: { serverTick: 104, serverGameTime: 5104, durationTicks: 0 } }));
  assert.throws(() => cue({ timing: { serverTick: 1, serverGameTime: 1, durationTicks: 0 } }), /UNBOUNDED_CUE_DURATION/);
  assert.throws(() => cue({ timing: { serverTick: 1, serverGameTime: 1, durationTicks: 999 } }), /CUE_DURATION/);
});

test('attachments must reference the cue actor or target', () => {
  assert.throws(() => cue({ attachment: { kind: 'ENTITY', entityUuid: '00000000-0000-4000-8000-000000000000', localOffset: [0, 0, 0] } }), /ATTACHMENT_ENTITY_NOT_IN_CUE/);
  assert.ok(cue({ attachment: { kind: 'ENTITY', entityUuid: TARGET, localOffset: [0, 1, 0] } }));
  assert.ok(cue({ attachment: { kind: 'WORLD', position: [4, 64, 8] } }));
});

test('lifecycle: ordered, single start, terminal ends it, missing terminal stays OPEN', () => {
  const t = (eventKind, serverTick, durationTicks = 12) => cue({ eventKind, timing: { serverTick, serverGameTime: 5000 + serverTick, durationTicks } });
  const ok = validateCueLifecycle([t('TELEGRAPH', 95), t('START', 100), t('HIT', 103), t('END', 112, 0)]);
  assert.equal(ok.status, 'TERMINATED'); assert.equal(ok.hits, 1);
  assert.equal(validateCueLifecycle([t('START', 100)]).status, 'OPEN');
  assert.throws(() => validateCueLifecycle([t('HIT', 99), t('START', 100)]), /HIT_BEFORE_START/);
  assert.throws(() => validateCueLifecycle([t('START', 100), t('CANCEL', 101, 0), t('HIT', 102)]), /CUE_AFTER_TERMINAL/);
  assert.throws(() => validateCueLifecycle([t('START', 100), t('HIT', 99)]), /OUT_OF_ORDER/);
  assert.throws(() => validateCueLifecycle([t('START', 100), t('START', 100)]), /DUPLICATE_CUE/);
  assert.throws(() => validateCueLifecycle([t('START', 100), cue({ eventKind: 'HIT', attackInstanceId: 'attack-2' })]), /IDENTITY_MISMATCH/);
});

test('bone emitters bind to the layout hash, not the bone name', () => {
  const model = { entityUuid: ACTOR, modelVersion: 'test_mob-1', boneLayoutHash: LAYOUT, bones: ['root', 'weapon_tip'] };
  assert.equal(bindCueToModel(cue(), model).status, 'BOUND');
  assert.throws(() => bindCueToModel(cue(), { ...model, boneLayoutHash: ref('layout-v2') }), /STALE_BONE_EMITTER_LAYOUT/);
  assert.throws(() => bindCueToModel(cue(), { ...model, bones: ['root'] }), /BONE_NOT_IN_LAYOUT/);
});

function fakeDriver(script = {}) {
  const calls = [];
  const d = {
    calls,
    async validateAsset() { calls.push('validateAsset'); return { ok: true }; },
    async prepare(c) { calls.push('prepare'); return { handle: c.cueId }; },
    async play() { calls.push('play'); if (script.play === 'throw') throw new Error('socket closed'); return { outcome: script.play ?? 'PLAYING' }; },
    async stop() { calls.push('stop'); return { outcome: script.stop ?? 'STOPPED' }; },
    async observe() { calls.push('observe'); return { alive: script.alive ?? true }; },
  };
  return d;
}
const assets = { 'kneekura:slash_afterglow': ASSET };

test('the pinned Photon manifest is valid, unverified, and forbids code import', () => {
  const m = validateProviderManifest(photon);
  assert.equal(m.providerId, PROVIDER.providerId);
  assert.equal(m.capabilities.controlledSeek, 'UNAVAILABLE');
  assert.equal(m.license.codeImport, 'FORBIDDEN');
  assert.throws(() => validateProviderManifest({ ...photon, license: { spdx: 'GPL-3.0', gate: 'OPEN', codeImport: 'ALLOWED' } }), /CODE_IMPORT_BEFORE_LICENSE_CLEARANCE/);
  assert.throws(() => validateProviderManifest({ ...photon, anchor: { minecraft: '1.21', loader: 'neoforge', java: 21 } }), /PROVIDER_NOT_ANCHOR/);
});

test('unverified capabilities need explicit opt-in; unavailable ones never run', async () => {
  const closed = createProviderAdapter({ manifest: photon, driver: fakeDriver(), registeredAssets: assets });
  await assert.rejects(closed.prepare(cue()), /PROVIDER_CAPABILITY_UNVERIFIED/);
  const open = createProviderAdapter({ manifest: photon, driver: fakeDriver(), registeredAssets: assets, allowUnverified: true });
  const r = await open.prepare(cue());
  assert.equal(r.outcome, 'PREPARED'); assert.equal(r.capabilityStatus, 'UNVERIFIED');
});

test('adapter refuses forbidden operations, unregistered assets and provider mismatches', async () => {
  const a = createProviderAdapter({ manifest: photon, driver: fakeDriver(), registeredAssets: assets, allowUnverified: true });
  for (const op of ['execute_script', 'eval', 'loadUrl', 'constructor', '__proto__'])
    await assert.rejects(a.invoke(op, 'x'), /PROVIDER_OPERATION_FORBIDDEN/);
  await assert.rejects(a.prepare(cue({ runtimeAssetHash: ref('swapped-asset') })), /UNREGISTERED_OR_CHANGED_FX_ASSET/);
  await assert.rejects(a.prepare(cue({ providerSourceRevision: 'a'.repeat(40) })), /CUE_PROVIDER_MISMATCH/);
  await assert.rejects(a.prepare(cue({ eventKind: 'END', timing: { serverTick: 1, serverGameTime: 1, durationTicks: 0 } })), /TERMINAL_CUE_CANNOT_PLAY/);
});

test('UNKNOWN play outcome forbids blind retry until observation resolves it', async () => {
  const driver = fakeDriver({ play: 'throw', alive: false });
  const a = createProviderAdapter({ manifest: photon, driver, registeredAssets: assets, allowUnverified: true });
  const c = cue();
  const { fxInstanceId } = await a.prepare(c);
  assert.equal((await a.play(fxInstanceId)).outcome, 'UNKNOWN');
  await assert.rejects(a.play(fxInstanceId), /BLIND_RETRY_FORBIDDEN_AFTER_UNKNOWN/);
  await assert.rejects(a.prepare(c), /BLIND_RETRY_FORBIDDEN_AFTER_UNKNOWN/);
  const o = await a.observe(fxInstanceId);
  assert.equal(o.outcome, 'STOPPED'); assert.equal(o.detail, 'PRIOR_OUTCOME_UNKNOWN_NOW_NOT_ALIVE');
  assert.equal(driver.calls.filter(x => x === 'play').length, 1);
});

test('stop is idempotent, bounded, and stopAll reports residue honestly', async () => {
  const a = createProviderAdapter({ manifest: photon, driver: fakeDriver(), registeredAssets: assets, allowUnverified: true });
  const { fxInstanceId } = await a.prepare(cue());
  await a.play(fxInstanceId);
  assert.equal((await a.stop(fxInstanceId, 'CANCEL')).outcome, 'STOPPED');
  assert.equal((await a.stop(fxInstanceId, 'CANCEL')).outcome, 'ALREADY_TERMINAL');

  const stuck = createProviderAdapter({ manifest: photon, driver: fakeDriver({ stop: 'UNKNOWN' }), registeredAssets: assets, allowUnverified: true });
  const p = await stuck.prepare(cue());
  await stuck.play(p.fxInstanceId);
  const all = await stuck.stopAll();
  assert.equal(all.status, 'UNKNOWN'); assert.deepEqual(all.residual, [p.fxInstanceId]);
  await stuck.stop(p.fxInstanceId); await stuck.stop(p.fxInstanceId);
  await assert.rejects(stuck.stop(p.fxInstanceId), /STOP_ATTEMPTS_EXHAUSTED_ESCALATE/);
});

test('concurrency is bounded by the cue budget', async () => {
  const a = createProviderAdapter({ manifest: photon, driver: fakeDriver(), registeredAssets: assets, allowUnverified: true });
  const c = cue({ limits: { ...cueBody().limits, maxConcurrentEffects: 1 } });
  await a.prepare(c);
  await assert.rejects(a.prepare(c), /FX_CONCURRENCY_LIMIT/);
  assert.equal(a.journal().length, 1);
});

test('a thrown prepare is UNKNOWN: no blind re-prepare, but stop is still allowed', async () => {
  const driver = fakeDriver(); driver.prepare = async () => { throw new Error('timeout'); };
  const a = createProviderAdapter({ manifest: photon, driver, registeredAssets: assets, allowUnverified: true });
  const c = cue();
  const r = await a.prepare(c);
  assert.equal(r.outcome, 'UNKNOWN');
  await assert.rejects(a.prepare(c), /BLIND_RETRY_FORBIDDEN_AFTER_UNKNOWN/);
  await assert.rejects(a.play(r.fxInstanceId), /BLIND_RETRY_FORBIDDEN_AFTER_UNKNOWN/);
  assert.equal((await a.stop(r.fxInstanceId, 'SESSION_END')).outcome, 'STOPPED');
});
