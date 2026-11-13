// Shared VFX Studio contract helpers. Pure functions only: no I/O, no clocks, no network.
import { exactKeys, hashId, identifier, integer, sha256, stableJson } from '../bridge/json.mjs';

export { exactKeys, hashId, identifier, integer, sha256, stableJson };

/** Truth labels that must never be rounded to PASS (PLAN §3). */
export const VERDICTS = Object.freeze(['PASS', 'FAIL', 'NOT_RUN', 'UNKNOWN', 'INCONCLUSIVE', 'BLOCKED', 'PARTIAL']);
export const EPISTEMIC = Object.freeze(['DIRECT_OBSERVED', 'SAMPLED_OBSERVED', 'DERIVED', 'VISUAL_INFERRED', 'NOT_EXPOSED']);

export function require(value, reason) { if (!value) throw new TypeError(reason); }
export const same = (a, b) => stableJson(a) === stableJson(b);

export function finite(value, min, max, reason = 'FINITE_NUMBER_REQUIRED') {
  require(typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max, reason);
  return value;
}
export function vector(value, size, limit = 30000000, reason = 'INVALID_VECTOR') {
  require(Array.isArray(value) && value.length === size, reason);
  value.forEach(n => finite(n, -limit, limit, reason));
  return value;
}
export function oneOf(value, allowed, reason) { require(allowed.includes(value), reason); return value; }
export function boundedList(value, max, reason = 'BOUNDED_LIST_REQUIRED') {
  require(Array.isArray(value) && value.length <= max, reason);
  return value;
}

const UUID = /^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/;
export function uuid(value, reason = 'EXACT_UUID_REQUIRED') { require(typeof value === 'string' && UUID.test(value), reason); return value; }

/** Namespaced resource id such as `kneekura:slash_afterglow`. Rejects paths, URLs and traversal. */
export function resourceId(value, reason = 'INVALID_RESOURCE_ID') {
  require(typeof value === 'string' && value.length <= 128 && /^[a-z0-9_.-]+:[a-z0-9_./-]+$/.test(value) &&
    !value.includes('..') && !value.includes('//') && !value.endsWith('/'), reason);
  return value;
}

/** Content reference `sha256:<64 hex>`. Placeholders such as `sha256:<atlas>` are rejected (PLAN §10.3). */
export function contentRef(value, reason = 'INVALID_CONTENT_REF') {
  require(typeof value === 'string' && /^sha256:[a-f0-9]{64}$/.test(value), reason);
  return value;
}

/** Git commit (40 hex) or sha256 (64 hex) revision. */
export function revision(value, reason = 'INVALID_SOURCE_REVISION') {
  require(typeof value === 'string' && /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value), reason);
  return value;
}

/** Self-hash: id = sha256(stableJson(body without id)). */
export function sealed(body, idKey) {
  require(!(idKey in body), 'SEAL_KEY_ALREADY_PRESENT');
  return { [idKey]: sha256(stableJson(body)), ...structuredClone(body) };
}
export function verifySeal(value, idKey, reason) {
  const { [idKey]: id, ...body } = value;
  hashId(id);
  require(sha256(stableJson(body)) === id, reason);
  return id;
}

export function byteLimit(value, max, reason) {
  require(Buffer.byteLength(stableJson(value)) <= max, reason);
}
