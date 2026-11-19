// VFX Provider Adapter (PLAN §4.1). Thin, provider-neutral guard around a driver that talks to a
// real provider (e.g. Photon 1.20.1). Provider APIs stay inside the driver; this layer enforces the
// contract: declared capabilities only, registered assets only, bounded concurrency, idempotent stop,
// and no blind retry after an UNKNOWN outcome.
import { validateCue, TERMINAL_EVENTS } from './cue-contract.mjs';
import { contentRef, exactKeys, identifier, oneOf, require, resourceId, revision } from './common.mjs';

export const OPERATIONS = Object.freeze(['capabilities', 'validate', 'prepare', 'play', 'stop', 'observe']);
export const CAPABILITY_STATUS = Object.freeze(['AVAILABLE', 'UNVERIFIED', 'UNAVAILABLE', 'NOT_EXPOSED']);
const CAPABILITY_KEYS = ['validate', 'prepare', 'play', 'stop', 'observe', 'controlledSeek', 'pause', 'particlePositions', 'emitterPosition'];
const MAX_STOP_ATTEMPTS = 3;

export function validateProviderManifest(input) {
  const m = structuredClone(input);
  exactKeys(m, ['schemaVersion', 'kind', 'providerId', 'providerSourceRevision', 'anchor', 'license', 'capabilities', 'evidence'], 'PROVIDER_MANIFEST');
  require(m.schemaVersion === 1 && m.kind === 'kneekura_vfx_provider_capabilities', 'INVALID_PROVIDER_MANIFEST');
  identifier(m.providerId); revision(m.providerSourceRevision);
  exactKeys(m.anchor, ['minecraft', 'loader', 'java'], 'PROVIDER_ANCHOR');
  require(m.anchor.minecraft === '1.20.1' && m.anchor.loader === 'forge' && m.anchor.java === 17, 'PROVIDER_NOT_ANCHOR');
  exactKeys(m.license, ['spdx', 'gate', 'codeImport'], 'PROVIDER_LICENSE');
  require(typeof m.license.spdx === 'string' && m.license.spdx.length <= 64, 'INVALID_PROVIDER_LICENSE');
  oneOf(m.license.gate, ['OPEN', 'RECORDED', 'CLEARED'], 'INVALID_LICENSE_GATE');
  // Third-party code is never vendored until the gate is CLEARED by a human (PLAN §2).
  require(m.license.codeImport === 'FORBIDDEN' || m.license.gate === 'CLEARED', 'CODE_IMPORT_BEFORE_LICENSE_CLEARANCE');
  exactKeys(m.capabilities, CAPABILITY_KEYS, 'PROVIDER_CAPABILITIES');
  for (const value of Object.values(m.capabilities)) oneOf(value, CAPABILITY_STATUS, 'INVALID_CAPABILITY_STATUS');
  require(Array.isArray(m.evidence) && m.evidence.length <= 32 && m.evidence.every(e => typeof e === 'string' && e.length <= 512), 'INVALID_PROVIDER_EVIDENCE');
  return m;
}

/**
 * @param {object} options
 * @param {object} options.manifest  provider capability manifest
 * @param {object} options.driver    { validateAsset, prepare, play, stop, observe } async functions
 * @param {Record<string,string>} options.registeredAssets effectId -> runtimeAssetHash (sha256:...)
 * @param {boolean} [options.allowUnverified] explicit opt-in for capabilities not yet proven on a real client
 */
export function createProviderAdapter({ manifest, driver, registeredAssets, allowUnverified = false }) {
  const m = validateProviderManifest(manifest);
  for (const op of ['validateAsset', 'prepare', 'play', 'stop', 'observe']) require(typeof driver?.[op] === 'function', 'DRIVER_OPERATION_MISSING');
  const assets = new Map();
  for (const [effectId, hash] of Object.entries(registeredAssets ?? {})) assets.set(resourceId(effectId), contentRef(hash));
  const instances = new Map();
  const journal = [];
  let counter = 0;

  function capability(name) {
    const status = m.capabilities[name];
    require(status !== 'UNAVAILABLE' && status !== 'NOT_EXPOSED', 'PROVIDER_CAPABILITY_UNAVAILABLE');
    require(status === 'AVAILABLE' || allowUnverified, 'PROVIDER_CAPABILITY_UNVERIFIED');
    return status;
  }
  function record(op, instance, outcome, status, detail = null) {
    const entry = { seq: journal.length + 1, op, fxInstanceId: instance?.fxInstanceId ?? null, cueId: instance?.cueId ?? null,
      outcome, capabilityStatus: status, detail };
    journal.push(Object.freeze(entry));
    return { ...entry };
  }
  function live() { return [...instances.values()].filter(i => ['PREPARED', 'PLAYING', 'UNKNOWN'].includes(i.state)); }
  function get(fxInstanceId) {
    identifier(fxInstanceId);
    const instance = instances.get(fxInstanceId);
    require(instance, 'FX_INSTANCE_NOT_FOUND');
    return instance;
  }
  function checkCue(cueInput) {
    const cue = validateCue(cueInput);
    require(cue.providerId === m.providerId && cue.providerSourceRevision === m.providerSourceRevision, 'CUE_PROVIDER_MISMATCH');
    require(assets.get(cue.effectId) === cue.runtimeAssetHash, 'UNREGISTERED_OR_CHANGED_FX_ASSET');
    return cue;
  }

  const api = {
    capabilities() { return structuredClone(m.capabilities); },

    async validate(cueInput) {
      const status = capability('validate');
      const cue = checkCue(cueInput);
      const result = await driver.validateAsset(cue.effectId, cue.runtimeAssetHash);
      require(result && typeof result.ok === 'boolean', 'DRIVER_RESULT_INVALID');
      return record('validate', { cueId: cue.cueId }, result.ok ? 'VALID' : 'INVALID', status, result.ok ? null : String(result.reason ?? 'UNSPECIFIED').slice(0, 256));
    },

    async prepare(cueInput) {
      const status = capability('prepare');
      const cue = checkCue(cueInput);
      require(!TERMINAL_EVENTS.includes(cue.eventKind), 'TERMINAL_CUE_CANNOT_PLAY');
      for (const i of instances.values()) require(!(i.cueId === cue.cueId && i.state === 'UNKNOWN'), 'BLIND_RETRY_FORBIDDEN_AFTER_UNKNOWN');
      require(live().length < cue.limits.maxConcurrentEffects, 'FX_CONCURRENCY_LIMIT');
      const fxInstanceId = `fx-${cue.cueId.slice(0, 16)}-${++counter}`;
      const instance = { fxInstanceId, cueId: cue.cueId, attackInstanceId: cue.attackInstanceId, state: 'PREPARED', handle: null, stopAttempts: 0 };
      // A thrown prepare may have half-created provider state: treat it as UNKNOWN, not as a clean failure,
      // so the same cue cannot be blindly re-prepared; only stop/observe may follow.
      try { instance.handle = await driver.prepare(cue); }
      catch (error) { instance.state = 'UNKNOWN'; instances.set(fxInstanceId, instance); return record('prepare', instance, 'UNKNOWN', status, String(error?.message ?? error).slice(0, 256)); }
      instances.set(fxInstanceId, instance);
      return record('prepare', instance, 'PREPARED', status);
    },

    async play(fxInstanceId) {
      const status = capability('play');
      const instance = get(fxInstanceId);
      require(instance.state !== 'UNKNOWN', 'BLIND_RETRY_FORBIDDEN_AFTER_UNKNOWN');
      require(instance.state === 'PREPARED', 'FX_INSTANCE_NOT_PREPARED');
      let outcome;
      try { outcome = (await driver.play(instance.handle))?.outcome; } catch { outcome = 'UNKNOWN'; }
      instance.state = outcome === 'PLAYING' ? 'PLAYING' : outcome === 'FAILED' ? 'FAILED' : 'UNKNOWN';
      return record('play', instance, instance.state, status);
    },

    /** Idempotent. Stop is restorative, so a bounded re-attempt after UNKNOWN is allowed. */
    async stop(fxInstanceId, reason = 'REQUESTED') {
      const status = capability('stop');
      const instance = get(fxInstanceId);
      oneOf(reason, ['REQUESTED', 'CANCEL', 'END', 'UNLOAD', 'SESSION_END', 'DEATH', 'TARGET_LOST'], 'INVALID_STOP_REASON');
      if (instance.state === 'STOPPED' || instance.state === 'FAILED') return record('stop', instance, 'ALREADY_TERMINAL', status, reason);
      require(instance.stopAttempts < MAX_STOP_ATTEMPTS, 'STOP_ATTEMPTS_EXHAUSTED_ESCALATE');
      instance.stopAttempts++;
      let outcome;
      try { outcome = (await driver.stop(instance.handle))?.outcome; } catch { outcome = 'UNKNOWN'; }
      instance.state = outcome === 'STOPPED' || outcome === 'NOT_FOUND' ? 'STOPPED' : 'UNKNOWN';
      return record('stop', instance, instance.state, status, reason);
    },

    async observe(fxInstanceId) {
      const status = capability('observe');
      const instance = get(fxInstanceId);
      let alive = null;
      try { const r = await driver.observe(instance.handle); alive = typeof r?.alive === 'boolean' ? r.alive : null; } catch { alive = null; }
      let detail = alive === null ? 'OBSERVATION_UNAVAILABLE' : null;
      if (instance.state === 'UNKNOWN' && alive === true) instance.state = 'PLAYING';
      else if (instance.state === 'UNKNOWN' && alive === false) { instance.state = 'STOPPED'; detail = 'PRIOR_OUTCOME_UNKNOWN_NOW_NOT_ALIVE'; }
      else if (instance.state === 'PLAYING' && alive === false) { instance.state = 'STOPPED'; detail = 'ENDED_BY_LIFETIME'; }
      return { ...record('observe', instance, instance.state, status, detail), alive };
    },

    /** Session end / unload: stop everything still live and report each outcome (A12). */
    async stopAll(reason = 'SESSION_END') {
      const results = [];
      for (const instance of live()) results.push(await api.stop(instance.fxInstanceId, reason));
      const residual = live().map(i => i.fxInstanceId);
      return { results, residual, status: residual.length ? 'UNKNOWN' : 'ALL_STOPPED' };
    },

    /** Generic dispatcher for AI callers. Anything outside OPERATIONS is refused by name. */
    async invoke(operation, ...args) {
      require(typeof operation === 'string' && OPERATIONS.includes(operation), 'PROVIDER_OPERATION_FORBIDDEN');
      return api[operation](...args);
    },

    state(fxInstanceId) { const i = get(fxInstanceId); return { fxInstanceId: i.fxInstanceId, cueId: i.cueId, state: i.state, stopAttempts: i.stopAttempts }; },
    journal() { return journal.map(e => ({ ...e })); },
  };
  return Object.freeze(api);
}
