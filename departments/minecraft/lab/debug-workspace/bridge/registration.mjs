import { mkdir, open, lstat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { isDeepStrictEqual } from 'node:util';
import {
  exactKeys, hashId, identifier, integer, sha256, stableJson, decodeJson,
} from './json.mjs';
import { readRegisteredFile, verifyBridgeMaterials } from './materials.mjs';

const BINDING_FIELDS = [
  'schema_version', 'experiment_id', 'generation', 'request_hash', 'target',
  'arena_id', 'arena_baseline_hash', 'assertions_hash',
];
const TARGET_FIELDS = [
  'profile_id', 'index_snapshot_id', 'build_artifact_hash', 'source_revision',
  'dirty_hash', 'config_hash', 'resource_hash',
];
const REQUEST_FIELDS = [
  'schema_version', 'experiment_id', 'generation', 'target', 'arena', 'subjects',
  'initial_state', 'actions', 'observation_scopes', 'visual_rig', 'assertions', 'budgets',
];

export function validateTechHubBinding(value) {
  exactKeys(value, BINDING_FIELDS, 'BINDING');
  integer(value.schema_version, 1, 1);
  identifier(value.experiment_id);
  integer(value.generation, 1, 1000000);
  identifier(value.arena_id);
  for (const key of ['request_hash', 'arena_baseline_hash', 'assertions_hash']) {
    hashId(value[key]);
  }
  exactKeys(value.target, TARGET_FIELDS, 'TARGET');
  for (const key of TARGET_FIELDS) {
    if (key === 'source_revision') {
      if (typeof value.target[key] !== 'string' ||
          !/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/.test(value.target[key])) {
        throw new TypeError('INVALID_REVISION');
      }
    } else {
      hashId(value.target[key]);
    }
  }
  return structuredClone(value);
}

function validateRequestLinkage(request, assertions, binding) {
  exactKeys(request, REQUEST_FIELDS, 'REQUEST');
  if (request.schema_version !== 1 ||
      request.experiment_id !== binding.experiment_id ||
      request.generation !== binding.generation ||
      !isDeepStrictEqual(request.target, binding.target) ||
      request.arena?.arena_id !== binding.arena_id ||
      request.arena?.baseline_hash !== binding.arena_baseline_hash) {
    throw new Error('REQUEST_BINDING_MISMATCH');
  }
  if (!Array.isArray(assertions) || !isDeepStrictEqual(request.assertions, assertions)) {
    throw new Error('ASSERTIONS_PAYLOAD_MISMATCH');
  }
}

/** Read linkage/material inputs only; this does not authorize or execute an experiment. */
export async function readBridgeInputs(registration) {
  exactKeys(registration, [
    'schemaVersion', 'trustedRoot', 'requestFile', 'bindingFile', 'assertionsFile', 'materials',
  ], 'REGISTRATION');
  integer(registration.schemaVersion, 1, 1);
  const read = (relativePath, maxBytes) => readRegisteredFile({
    root: registration.trustedRoot, relativePath, maxBytes,
  });
  const [requestFile, bindingFile, assertionsFile] = await Promise.all([
    read(registration.requestFile, 128 * 1024),
    read(registration.bindingFile, 64 * 1024),
    read(registration.assertionsFile, 256 * 1024),
  ]);
  const binding = validateTechHubBinding(decodeJson(bindingFile.bytes));
  const request = decodeJson(requestFile.bytes, 128 * 1024);
  const assertions = decodeJson(assertionsFile.bytes, 256 * 1024);
  if (requestFile.sha256 !== binding.request_hash) throw new Error('REQUEST_HASH_MISMATCH');
  if (assertionsFile.sha256 !== binding.assertions_hash) throw new Error('ASSERTIONS_HASH_MISMATCH');
  validateRequestLinkage(request, assertions, binding);
  const materialInventory = await verifyBridgeMaterials(registration, binding);
  return {
    binding, request, assertions, materialInventory,
    runtimeAttestation: 'NOT_ESTABLISHED',
    bytes: { request: requestFile.bytes, binding: bindingFile.bytes, assertions: assertionsFile.bytes },
  };
}

async function registryRoot(runtimeRoot, { create = false } = {}) {
  if (typeof runtimeRoot !== 'string' || !path.isAbsolute(runtimeRoot)) {
    throw new TypeError('INVALID_RUNTIME_ROOT');
  }
  if (create) await mkdir(runtimeRoot, { recursive: true });
  if (await realpath(runtimeRoot) !== path.resolve(runtimeRoot)) {
    throw new Error('UNSAFE_RUNTIME_ROOT');
  }
  let directory = runtimeRoot;
  for (const segment of ['bridge', 'registrations']) {
    directory = path.join(directory, segment);
    if (create) await mkdir(directory, { recursive: true });
    if ((await lstat(directory)).isSymbolicLink()) throw new Error('SYMLINK_REJECTED');
  }
  return directory;
}

async function writeExclusive(file, bytes) {
  const handle = await open(file, 'wx');
  try {
    await handle.writeFile(bytes);
    await handle.sync();
  } finally {
    await handle.close();
  }
}

function manifestFor(registration, input) {
  return {
    schemaVersion: 1,
    registration: structuredClone(registration),
    binding: input.binding,
    materialInventory: input.materialInventory,
    inputHashes: {
      request: sha256(input.bytes.request),
      binding: sha256(input.bytes.binding),
      assertions: sha256(input.bytes.assertions),
    },
    runtimeAttestation: 'NOT_ESTABLISHED',
    capabilityReadiness: { execution: 'BLOCKED', arena: 'BLOCKED', capture: 'BLOCKED' },
  };
}

export async function registerBridgeRequest({ runtimeRoot, registration, expectedRequestHash = null }) {
  const input = await readBridgeInputs(registration);
  if (expectedRequestHash !== null && hashId(expectedRequestHash) !== input.binding.request_hash) {
    throw new Error('ADAPTER_REQUEST_HASH_MISMATCH');
  }
  const base = await registryRoot(runtimeRoot, { create: true });
  const directory = path.join(base, input.binding.request_hash);
  const manifest = manifestFor(registration, input);
  const registrationHash = sha256(stableJson(manifest));
  try {
    await mkdir(directory);
  } catch (error) {
    if (error.code !== 'EEXIST') throw error;
    const previous = await loadBridgeRegistration({ runtimeRoot, requestHash: input.binding.request_hash });
    if (previous.registrationHash !== registrationHash) throw new Error('REGISTRATION_CONFLICT');
    return previous;
  }
  // The manifest is the final commit marker. Incomplete directories fail closed.
  for (const key of ['request', 'binding', 'assertions']) {
    await writeExclusive(path.join(directory, key + '.json'), input.bytes[key]);
  }
  await writeExclusive(
    path.join(directory, 'registration.json'),
    Buffer.from(JSON.stringify({ ...manifest, registrationHash }, null, 2) + '\n'),
  );
  return { directory, registrationHash, ...input, manifest };
}

export async function loadBridgeRegistration({ runtimeRoot, requestHash }) {
  hashId(requestHash);
  let base, saved;
  try {
    base = await registryRoot(runtimeRoot);
    const file = await readRegisteredFile({
      root: base, relativePath: requestHash + '/registration.json', maxBytes: 128 * 1024,
    });
    saved = decodeJson(file.bytes);
  } catch (error) {
    if (error.code === 'ENOENT') throw new Error('REGISTRATION_INCOMPLETE');
    throw error;
  }
  const directory = path.join(base, requestHash);
  const { registrationHash, ...manifest } = saved;
  hashId(registrationHash);
  if (sha256(stableJson(manifest)) !== registrationHash || manifest.binding?.request_hash !== requestHash) {
    throw new Error('REGISTRATION_INTEGRITY');
  }
  const input = await readBridgeInputs(manifest.registration);
  if (sha256(stableJson(manifestFor(manifest.registration, input))) !== registrationHash) {
    throw new Error('REGISTRATION_CONFLICT');
  }
  for (const key of ['request', 'binding', 'assertions']) {
    await readRegisteredFile({
      root: directory, relativePath: key + '.json',
      expectedSha256: manifest.inputHashes[key], maxBytes: 256 * 1024,
    });
  }
  return { directory, registrationHash, ...input, manifest };
}
