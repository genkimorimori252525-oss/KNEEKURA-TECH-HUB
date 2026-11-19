/** Private, explicit owner preparation for the existing launch flow. No launch or attestation is performed here. */
import { lstat, mkdir, open, realpath } from 'node:fs/promises';
import path from 'node:path';
import { exactKeys, identifier, integer, hashId, decodeJson, sha256, stableJson, canonicalRunSnapshotBytes } from './json.mjs';
import { readRegisteredFile } from './materials.mjs';
import { validateVisualExperimentRequest } from '../evidence/visual-request-contract.mjs';
import { loadBridgeRegistration, validateTechHubBinding } from './registration.mjs';
import { buildOwnerGrantIntent, buildGrantFromSealedRequest } from './owner-grant.mjs';
import { validateOwnerTriggerConfig } from './owner-trigger-config.mjs';
import { TANK_ROTATION_PERMISSION, buildTankRotationIntent, validateTankRotation } from './owner-tank-rotation.mjs';
export {buildTankPresentationResource} from './tank-resource.mjs';

export const OWNER_ENV_FILE = 'KNEEKURA_DEBUG_OWNER_ENVELOPE_FILE';
export const OWNER_ENV_HASH = 'KNEEKURA_DEBUG_OWNER_ENVELOPE_SHA256';
const ID_FIELDS = ['debugSessionId', 'runId', 'runSnapshotId', 'processEpoch', 'handshakeNonce'];
const ENVELOPE_FIELDS = ['schemaVersion', ...ID_FIELDS, 'requestHash', 'grantHash', 'materialDescriptorHash', 'worldRegistrationHash', 'controlMode'];
const LINKAGE = new Set(['PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE', 'OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE']);
const MATERIALS = [
  ['buildArtifact', 'build.jar', 'buildArtifactHash', 'build_artifact_hash', 64 * 1024 * 1024],
  ['configArtifact', 'config.bin', 'configArtifactHash', 'config_hash', 1024 * 1024],
  ['resourceArtifact', 'resources.bin', 'resourceArtifactHash', 'resource_hash', 16 * 1024 * 1024],
];
function require(value, reason) {
  if (!value) throw new Error(reason);
}
function same(a, b) { return stableJson(a) === stableJson(b); }
function bytes(value) { return Buffer.from(stableJson(value), 'utf8'); }
async function directory(value) {
  require(typeof value === 'string' && path.isAbsolute(value) && value === path.resolve(value), 'OWNER_ABSOLUTE_CANONICAL_DIRECTORY_REQUIRED');
  require(await realpath(value) === value && (await lstat(value)).isDirectory(), 'OWNER_DIRECTORY_UNSAFE');
  return value;
}
function validateIdentity(value) {
  exactKeys(value, ID_FIELDS, 'OWNER_IDENTITY');
  for (const key of ['debugSessionId', 'runId', 'runSnapshotId', 'handshakeNonce']) identifier(value[key]);
  integer(value.processEpoch, 1, 2147483647);
  require(value.handshakeNonce.length >= 16, 'OWNER_NONCE_TOO_SHORT');
  return structuredClone(value);
}
function resource(value) {
  return typeof value === 'string' && value.length <= 128 && /^[a-z0-9_]+:[a-z0-9_/.-]+$/.test(value) &&
    !value.split(':')[1].split('/').some(p => !p || p === '.' || p === '..');
}
function validateDescriptor(value, target) {
  exactKeys(value, ['schemaVersion', 'linkageMode', 'targetModId', 'buildArtifactHash', 'configArtifactHash', 'resourceArtifactHash', 'classResources'], 'OWNER_MATERIAL_DESCRIPTOR');
  integer(value.schemaVersion, 1, 1);
  require(LINKAGE.has(value.linkageMode) && typeof value.targetModId === 'string' && /^[a-z][a-z0-9_]{1,63}$/.test(value.targetModId), 'OWNER_LINKAGE_UNSUPPORTED');
  for (const [, , descriptorField, targetField] of MATERIALS) {
    hashId(value[descriptorField]);
    require(value[descriptorField] === target[targetField], 'OWNER_MATERIAL_TARGET_MISMATCH');
  }
  require(Array.isArray(value.classResources) && value.classResources.length >= 1 && value.classResources.length <= 8, 'OWNER_CLASS_RESOURCE_LIMIT');
  const names = new Set();
  for (const item of value.classResources) {
    exactKeys(item, ['className', 'sha256'], 'OWNER_CLASS_RESOURCE');
    require(typeof item.className === 'string' && item.className.length <= 256 &&
      /^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+$/.test(item.className) && !names.has(item.className), 'OWNER_CLASS_RESOURCE_INVALID');
    names.add(item.className);
    hashId(item.sha256);
  }
  return structuredClone(value);
}
async function validateWorld(value) {
  exactKeys(value, ['schemaVersion', 'registrationId', 'canonicalWorldRoot', 'worldName', 'dimensionId', 'permissions'], 'OWNER_WORLD_REGISTRATION');
  integer(value.schemaVersion, 1, 1);
  identifier(value.registrationId);
  require(value.worldName === 'KNEEKURA_DEBUG_WORLD' && resource(value.dimensionId), 'OWNER_DISPOSABLE_WORLD_REQUIRED');
  require(Array.isArray(value.permissions) && value.permissions.includes('BOUNDED_DIAGNOSTIC_CONTROL') &&
    value.permissions.length <= 3 && new Set(value.permissions).size === value.permissions.length &&
    value.permissions.every(p => ['BOUNDED_DIAGNOSTIC_CONTROL', 'CARDINAL_CAPTURE_PAUSE_CAMERA', TANK_ROTATION_PERMISSION].includes(p)), 'OWNER_PERMISSION_SCOPE');
  await directory(value.canonicalWorldRoot);
  return structuredClone(value);
}
function capturePermission(request, world) {
  if (request.visual_rig?.mode === 'cardinal-4-snapshot-v1' || request.budgets?.max_captures > 0)
    require(world.permissions.includes('CARDINAL_CAPTURE_PAUSE_CAMERA'), 'OWNER_CAPTURE_PERMISSION_MISSING');
}
function ownerIntent(envelopeHash) {
  return { envelopeHash: hashId(envelopeHash), scope: 'BOUNDED_DIAGNOSTIC_CONTROL', fullTargetAttestation: 'NOT_ESTABLISHED' };
}
async function writeExclusive(file, content) {
  const handle = await open(file, 'wx', 0o600);
  try { await handle.writeFile(content); await handle.sync(); } finally { await handle.close(); }
}
async function absent(file) {
  try { await lstat(file); throw new Error('OWNER_IMMUTABLE_PATH_EXISTS'); }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
}
function grantIdentity(identity, world) {
  return { ...identity, dimensionId: world.dimensionId, disposableWorldName: world.worldName };
}
export async function prepareOwnerControl({ runtimeRoot, runDir, identity, operatorRegistration, bridgeContext }) {
  identity = validateIdentity(identity);
  await directory(runtimeRoot);
  await directory(runDir);
  const relative = path.relative(runtimeRoot, runDir);
  require(relative && !relative.startsWith('..') && !path.isAbsolute(relative), 'OWNER_RUN_OUTSIDE_RUNTIME');
  require(bridgeContext?.binding?.request_hash, 'OWNER_REGISTERED_BRIDGE_REQUIRED');
  // Re-read the existing committed registry; callers cannot replace its request/materials with an arbitrary object.
  const bridge = await loadBridgeRegistration({ runtimeRoot, requestHash: bridgeContext.binding.request_hash });
  require(bridge.registrationHash === bridgeContext.registrationHash, 'OWNER_BRIDGE_REGISTRATION_CHANGED');
  validateVisualExperimentRequest(bridge.request); // Validate values without rewriting the sealed request bytes.
  exactKeys(operatorRegistration, ['trustedRoot', 'relativePath', 'sha256'], 'PRIVATE_OWNER_LOCATOR');
  const selected = await readRegisteredFile({ root: operatorRegistration.trustedRoot, relativePath: operatorRegistration.relativePath,
    expectedSha256: hashId(operatorRegistration.sha256), maxBytes: 128 * 1024 });
  const operator = decodeJson(selected.bytes, 128 * 1024);
  exactKeys(operator, ['schemaVersion', 'requestHash', 'materialDescriptor', 'worldRegistration', 'selection', ...(Object.hasOwn(operator, 'triggerCapture') ? ['triggerCapture'] : []),
    ...(Object.hasOwn(operator, 'tankRotation') ? ['tankRotation'] : [])], 'PRIVATE_OWNER_REGISTRATION');
  integer(operator.schemaVersion, 1, 1);
  require(operator.requestHash === bridge.binding.request_hash, 'OWNER_REQUEST_MISMATCH');
  const materialDescriptor = validateDescriptor(operator.materialDescriptor, bridge.binding.target);
  const worldRegistration = await validateWorld(operator.worldRegistration);
  capturePermission(bridge.request, worldRegistration);
  const grant = buildOwnerGrantIntent({ binding: bridge.binding, request: bridge.request,
    identity: grantIdentity(identity, worldRegistration), selection: operator.selection });
  const triggerCapture = Object.hasOwn(operator, 'triggerCapture') ? validateOwnerTriggerConfig(operator.triggerCapture, grant) : null;
  if(triggerCapture && bridge.request.visual_rig.mode !== 'cardinal-4-snapshot-v1') throw new Error('OWNER_TRIGGER_CARDINAL_RIG_REQUIRED');
  let tankRotation = null, tankPredecessor = null;
  if (Object.hasOwn(operator, 'tankRotation')) {
    tankPredecessor = (await readRegisteredFile({root:worldRegistration.canonicalWorldRoot,relativePath:'kneekura-tank-owner.json',
      expectedSha256:hashId(operator.tankRotation?.previousOwnerFileSha256),maxBytes:65536})).bytes;
    tankRotation = buildTankRotationIntent(operator.tankRotation,{identity,grant,request:bridge.request,world:worldRegistration,triggerCapture,previousOwnerBytes:tankPredecessor});
  }
  const materialBytes = [];
  for (const [key, name, , targetField, maxBytes] of MATERIALS) {
    const registration = bridge.manifest.registration;
    const input = await readRegisteredFile({ root: registration.trustedRoot, relativePath: registration.materials[key].relativePath,
      expectedSha256: bridge.binding.target[targetField], maxBytes });
    materialBytes.push([name, input.bytes]);
  }
  const grantBytes = bytes(grant);
  const descriptorBytes = bytes(materialDescriptor);
  const worldBytes = bytes(worldRegistration);
  const envelope = { schemaVersion: 1, ...identity, requestHash: bridge.binding.request_hash,
    grantHash: sha256(grantBytes), materialDescriptorHash: sha256(descriptorBytes), worldRegistrationHash: sha256(worldBytes),
    controlMode: 'BOUNDED_DIAGNOSTIC_CONTROL', ...(triggerCapture ? { triggerConfigHash: sha256(bytes(triggerCapture)) } : {}),
    ...(tankRotation ? { tankRotationHash: sha256(bytes(tankRotation)) } : {}) };
  const envelopeBytes = bytes(envelope);
  const envelopeHash = sha256(envelopeBytes);
  const control = path.join(runDir, 'control');
  for (const name of ['run-snapshot.json', 'run-snapshot.canonical.json', 'control/owner-envelope.json', 'control/owner-grant.json',
    'control/owner-material-descriptor.json', 'control/owner-world-registration.json', 'control/owner-experiment-request.json', 'control/owner-trigger-config.json',
    'control/owner-tank-rotation.json', 'control/owner-tank-predecessor.json']) await absent(path.join(runDir, name));
  try { await mkdir(control, { mode: 0o700 }); } catch (error) { if (error.code !== 'EEXIST') throw error; }
  await directory(control);
  const materialDir = path.join(control, 'owner-materials');
  await mkdir(materialDir, { mode: 0o700 }); // Exclusive reservation. An incomplete prior attempt is never healed.
  for (const [name, raw] of materialBytes) await writeExclusive(path.join(materialDir, name), raw);
  for (const [name, raw] of [['owner-grant.json', grantBytes], ['owner-material-descriptor.json', descriptorBytes],
    ['owner-world-registration.json', worldBytes], ['owner-experiment-request.json', bridge.bytes.request]]) await writeExclusive(path.join(control, name), raw);
  if (triggerCapture) await writeExclusive(path.join(control, 'owner-trigger-config.json'), bytes(triggerCapture));
  if (tankRotation) {
    await writeExclusive(path.join(control,'owner-tank-rotation.json'),bytes(tankRotation));
    await writeExclusive(path.join(control,'owner-tank-predecessor.json'),tankPredecessor);
  }
  await writeExclusive(path.join(control, 'owner-envelope.json'), envelopeBytes); // Final preparation commit marker.
  return { ...(await readPreparedOwnerControl({ runDir, envelopeHash })), envelopeHash,
    envelopeFile: path.join(control, 'owner-envelope.json'), operatorRegistrationHash: selected.sha256 };
}

export async function readPreparedOwnerControl({ runDir, envelopeHash, requireSnapshot = false }) {
  hashId(envelopeHash);
  require(typeof requireSnapshot === 'boolean', 'OWNER_SNAPSHOT_FLAG');
  await directory(runDir);
  const read = (relativePath, expectedSha256, maxBytes = 128 * 1024) => readRegisteredFile({ root: runDir, relativePath, expectedSha256, maxBytes });
  const envelope = decodeJson((await read('control/owner-envelope.json', envelopeHash)).bytes);
  exactKeys(envelope, [...ENVELOPE_FIELDS, ...(Object.hasOwn(envelope, 'triggerConfigHash') ? ['triggerConfigHash'] : []),
    ...(Object.hasOwn(envelope,'tankRotationHash') ? ['tankRotationHash'] : [])], 'OWNER_ENVELOPE');
  integer(envelope.schemaVersion, 1, 1);
  require(envelope.controlMode === 'BOUNDED_DIAGNOSTIC_CONTROL', 'OWNER_CONTROL_SCOPE');
  const identity = validateIdentity(Object.fromEntries(ID_FIELDS.map(k => [k, envelope[k]])));
  for (const key of ['requestHash', 'grantHash', 'materialDescriptorHash', 'worldRegistrationHash']) hashId(envelope[key]);
  const grant = decodeJson((await read('control/owner-grant.json', envelope.grantHash)).bytes);
  const request = decodeJson((await read('control/owner-experiment-request.json', envelope.requestHash)).bytes);
  validateVisualExperimentRequest(request);
  const materialDescriptor = validateDescriptor(decodeJson((await read('control/owner-material-descriptor.json', envelope.materialDescriptorHash)).bytes), request.target);
  const worldRegistration = await validateWorld(decodeJson((await read('control/owner-world-registration.json', envelope.worldRegistrationHash)).bytes));
  capturePermission(request, worldRegistration);
  const selection = Object.fromEntries(['grantId', 'leaseId', 'arenaEpoch', 'expectedArenaRevision', 'allowedActions'].map(k => [k, grant[k]]));
  const expected = buildGrantFromSealedRequest({ request, requestHash: envelope.requestHash, identity: grantIdentity(identity, worldRegistration), selection });
  require(same(grant, expected), 'OWNER_GRANT_LINKAGE_MISMATCH');
  for (const [, name, descriptorField, , maxBytes] of MATERIALS)
    await read(`control/owner-materials/${name}`, materialDescriptor[descriptorField], maxBytes);
  const triggerCapture = Object.hasOwn(envelope, 'triggerConfigHash')
    ? validateOwnerTriggerConfig(decodeJson((await read('control/owner-trigger-config.json', hashId(envelope.triggerConfigHash))).bytes), grant) : null;
  if(triggerCapture && request.visual_rig.mode !== 'cardinal-4-snapshot-v1') throw new Error('OWNER_TRIGGER_CARDINAL_RIG_REQUIRED');
  let tankRotation = null;
  if (Object.hasOwn(envelope,'tankRotationHash')) {
    const plan = decodeJson((await read('control/owner-tank-rotation.json',hashId(envelope.tankRotationHash),16384)).bytes);
    const predecessor = await read('control/owner-tank-predecessor.json',hashId(plan.previousOwnerFileSha256),65536);
    tankRotation = validateTankRotation(plan,{identity,grant,request,world:worldRegistration,triggerCapture,previousOwnerBytes:predecessor.bytes});
  }
  const ownerControlIntent = ownerIntent(envelopeHash);
  const result = { envelope, grant, request, materialDescriptor, worldRegistration, identity, ownerControlIntent, triggerCapture, tankRotation };
  if (requireSnapshot) {
    const raw = await read('run-snapshot.json', null, 2 * 1024 * 1024);
    const body = await read('run-snapshot.canonical.json', null, 2 * 1024 * 1024);
    const snapshot = decodeJson(raw.bytes, 2 * 1024 * 1024);
    const { snapshotHash, ...withoutHash } = snapshot;
    require(snapshotHash === 'sha256:' + body.sha256 && body.bytes.equals(canonicalRunSnapshotBytes(withoutHash)) &&
      same(withoutHash, decodeJson(body.bytes, 2 * 1024 * 1024)), 'OWNER_SNAPSHOT_CANONICAL_MISMATCH');
    integer(snapshot.schemaVersion, 1, 1);
    require(snapshot.worldName === worldRegistration.worldName, 'OWNER_SNAPSHOT_WORLD_MISMATCH');
    integer(snapshot.runtime?.pid, 1, Number.MAX_SAFE_INTEGER);
    require(snapshot.runtime?.attestation?.topology === 'INTEGRATED_SERVER', 'OWNER_SNAPSHOT_TOPOLOGY_UNSUPPORTED');
    validateTechHubBinding(snapshot.techHub);
    require(snapshot.techHub.arena_id === request.arena.arena_id && snapshot.techHub.arena_baseline_hash === request.arena.baseline_hash, 'OWNER_SNAPSHOT_ARENA_MISMATCH');
    require(snapshot.snapshotId === identity.runSnapshotId && snapshot.debugSessionId === identity.debugSessionId &&
      snapshot.runId === identity.runId && snapshot.processEpoch === identity.processEpoch &&
      snapshot.techHub?.request_hash === envelope.requestHash && snapshot.techHub?.generation === request.generation &&
      snapshot.techHub?.experiment_id === request.experiment_id && same(snapshot.techHub?.target, request.target) &&
      same(snapshot.bridge?.ownerControlIntent, ownerControlIntent), 'OWNER_SNAPSHOT_LINKAGE_MISMATCH');
    result.snapshot = snapshot;
  }
  return result;
}

export function ownerLaunchEnvironment(environment, preparedOwner) {
  const result = { ...environment };
  delete result[OWNER_ENV_FILE];
  delete result[OWNER_ENV_HASH];
  if (preparedOwner != null) {
    hashId(preparedOwner.envelopeHash);
    require(typeof preparedOwner.envelopeFile === 'string' && path.isAbsolute(preparedOwner.envelopeFile) &&
      path.basename(preparedOwner.envelopeFile) === 'owner-envelope.json', 'OWNER_ENVIRONMENT_NOT_PREPARED');
    result[OWNER_ENV_FILE] = preparedOwner.envelopeFile;
    result[OWNER_ENV_HASH] = preparedOwner.envelopeHash;
  }
  return result;
}

/** Existing private --config files may opt in; no new launch command or request-controlled path exists. */
export function ownerLaunchSelection(config = {}, options = {}) {
  const configured = config.ownerControl ?? null;
  if (configured !== null) {
    exactKeys(configured, ['requestHash', 'operatorRegistration'], 'OWNER_LAUNCH_CONFIG');
    hashId(configured.requestHash);
  }
  const requestHash = options.bridgeRequestHash ?? configured?.requestHash ?? null;
  const operatorRegistration = options.ownerRegistration ?? configured?.operatorRegistration ?? null;
  if (requestHash !== null) hashId(requestHash);
  if (operatorRegistration !== null) {
    require(requestHash !== null, 'OWNER_REGISTERED_BRIDGE_REQUIRED');
    exactKeys(operatorRegistration, ['trustedRoot', 'relativePath', 'sha256'], 'PRIVATE_OWNER_LOCATOR');
    hashId(operatorRegistration.sha256);
    require(typeof operatorRegistration.trustedRoot === 'string' && path.isAbsolute(operatorRegistration.trustedRoot) &&
      typeof operatorRegistration.relativePath === 'string' && operatorRegistration.relativePath.length > 0,
    'PRIVATE_OWNER_LOCATOR_INVALID');
  }
  if (configured !== null) require(requestHash === configured.requestHash &&
    same(operatorRegistration, configured.operatorRegistration), 'CONFLICTING_OWNER_LAUNCH_CONFIG');
  return { requestHash, operatorRegistration: operatorRegistration == null ? null : structuredClone(operatorRegistration) };
}
