/* Sealed static-item pilot dispatcher, injected into a hash-checked sosadly source.
 * No generic commands, paths, scripts or plugin-management methods are exposed.
 * This protects the bridge, not the operating system from other trusted software.
 */
function createAssetGuard(configuration, host) {
  'use strict';
  const config = JSON.parse(JSON.stringify(configuration));
  if (!Number.isInteger(config.timeout_ms) || config.timeout_ms < 20 || config.timeout_ms > 120000) {
    throw new Error('Invalid guarded operation deadline');
  }
  const epoch = host.epoch();
  if (typeof epoch !== 'string' || !/^[a-zA-Z0-9_-]{32,64}$/.test(epoch)) {
    throw new Error('A fresh process epoch is required');
  }
  let phase = 'READY';
  let operation = null;
  const same = (a, b) => {
    if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
    let different = 0;
    for (let i = 0; i < a.length; i++) different |= a.charCodeAt(i) ^ b.charCodeAt(i);
    return different === 0;
  };
  const fail = () => { throw new Error('Guarded asset operation refused'); };
  function authorize(params, build) {
    if (!params || typeof params !== 'object' || Array.isArray(params)) fail();
    const keys = ['token', 'session_id', 'request_hash'];
    if (build) keys.push('epoch', 'operation_id');
    if (Object.keys(params).sort().join(',') !== keys.sort().join(',')) fail();
    for (const key of ['token', 'session_id', 'request_hash']) if (!same(params[key], config[key])) fail();
    if (build && (!same(params.epoch, epoch) || typeof params.operation_id !== 'string'
        || !/^[a-zA-Z0-9_-]{32,64}$/.test(params.operation_id))) fail();
  }
  const identity = () => ({session_id: config.session_id, request_hash: config.request_hash,
    epoch, operation_id: operation, phase,
    verification: {structural: 'NOT_RUN', visual: 'NOT_RUN', runtime: 'NOT_RUN'}});
  return async function guardedDispatch(action, params) {
    if (action !== 'kneekura_asset_status' && action !== 'kneekura_asset_build') fail();
    const build = action === 'kneekura_asset_build';
    authorize(params, build);
    if (!build) return identity();
    if (phase !== 'READY') fail();
    // Claim before any await. Even a refused/ambiguous first attempt is not replayable.
    phase = 'RUNNING'; operation = params.operation_id;
    let timer, owner = null;
    const active = () => {
      if (phase !== 'RUNNING') fail();
      if (owner !== null) host.assertOwned(owner);
    };
    const perform = async () => {
      host.assertEmpty(); active();
      await host.createProject(config);
      owner = host.project();
      if (!owner || typeof owner !== 'object') fail();
      active();
      await host.createTexture(config); active(); host.assertTexture();
      await host.createCubes(config); active();
      await host.setDisplay(config); active();
      const baseline = await host.fingerprint(); active();
      const exported = await host.exportBytes(); active();
      if (baseline !== await host.fingerprint()) fail();
      active();
      const views = {};
      for (const view of config.required_views) {
        active();
        if (baseline !== await host.fingerprint()) fail();
        active();
        views[view] = await host.screenshot(view); active();
        if (baseline !== await host.fingerprint()) fail();
        active();
      }
      const result = {...exported, views};
      if (new TextEncoder().encode(JSON.stringify(result)).length > 8 * 1024 * 1024) fail();
      return result;
    };
    try {
      const timeout = new Promise((_, reject) => {
        timer = setTimeout(() => { phase = 'TAINTED'; reject(new Error('Guarded asset deadline expired')); }, config.timeout_ms);
      });
      const result = await Promise.race([perform(), timeout]);
      active(); phase = 'EXPORTED_NOT_REVIEWED';
      return {...identity(), ...result};
    } catch (_) {
      phase = 'TAINTED';
      // Never serialize an upstream exception, params, session secret or script source.
      throw new Error('Guarded asset session tainted; do not retry; inspect the isolated editor');
    } finally {
      clearTimeout(timer);
    }
  };
}
