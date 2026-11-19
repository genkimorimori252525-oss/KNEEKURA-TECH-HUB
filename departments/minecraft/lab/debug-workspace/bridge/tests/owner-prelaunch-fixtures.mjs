import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { sha256 } from '../json.mjs';
import { registerBridgeRequest } from '../registration.mjs';

export async function ownerPrelaunchFixture(t = null, suppliedRoot = null, sourceRevision = 'c'.repeat(40), mutateRequest = null) {
  const root = suppliedRoot ?? await mkdtemp(path.join(tmpdir(), 'owner-prelaunch-'));
  await mkdir(root, { recursive: true });
  t?.after(() => rm(root, { recursive: true, force: true }));
  const runtimeRoot = path.join(root, 'runtime'); const inputs = path.join(root, 'inputs');
  const privateRoot = path.join(root, 'private'); const world = path.join(root, 'KNEEKURA_DEBUG_WORLD');
  const runDir = path.join(runtimeRoot, 'sessions', 's', 'runs', 'r');
  for (const dir of [inputs, privateRoot, world, runDir]) await mkdir(dir, { recursive: true });
  const target = { profile_id: 'a'.repeat(64), index_snapshot_id: 'b'.repeat(64), build_artifact_hash: sha256('build'),
    source_revision: sourceRevision, dirty_hash: 'd'.repeat(64), config_hash: sha256('config'), resource_hash: sha256('resources') };
  const assertions = [{ assertion_id: 'health', subject_id: 'pig', kind: 'structured', field: 'health', operator: 'equals', expected: 20 }];
  const request = { schema_version: 1, experiment_id: 'experiment', generation: 1, target,
    arena: { arena_id: 'arena', preset: 'normal', baseline_hash: 'e'.repeat(64), bounds: { min: [0,0,0], max: [8,8,8] } },
    subjects: [{ subject_id: 'pig', uuid: '00000000-0000-0000-0000-000000000001', entity_type: 'minecraft:pig' }],
    initial_state: [], actions: [{ action_id: 'wait', operation: 'wait_ticks', ticks: 1 }],
    observation_scopes: [{ kind: 'ENTITY_UUID', subject_id: 'pig', lanes: ['SERVER_ENTITY_STATE'], level: 'L1' }],
    visual_rig: { mode: 'none' }, assertions, budgets: { time_budget_ms: 5000, max_actions: 1, max_captures: 0 } };
  if (mutateRequest) mutateRequest(request);
  const requestBytes = Buffer.from(JSON.stringify(request));
  const binding = { schema_version: 1, experiment_id: request.experiment_id, generation: 1, request_hash: sha256(requestBytes),
    target, arena_id: 'arena', arena_baseline_hash: request.arena.baseline_hash, assertions_hash: sha256(JSON.stringify(assertions)) };
  for (const [name, value] of Object.entries({ 'request.json': requestBytes, 'binding.json': JSON.stringify(binding),
    'assertions.json': JSON.stringify(assertions), 'build.bin': 'build', 'config.bin': 'config', 'resource.bin': 'resources' }))
    await writeFile(path.join(inputs, name), value);
  const bridgeContext = await registerBridgeRequest({ runtimeRoot, registration: { schemaVersion: 1, trustedRoot: inputs,
    requestFile: 'request.json', bindingFile: 'binding.json', assertionsFile: 'assertions.json',
    materials: { buildArtifact: { relativePath: 'build.bin' }, configArtifact: { relativePath: 'config.bin' }, resourceArtifact: { relativePath: 'resource.bin' } } } });
  const operator = { schemaVersion: 1, requestHash: binding.request_hash,
    materialDescriptor: { schemaVersion: 1, linkageMode: 'PACKAGED_JAR_CODE_SOURCE_AND_CLASS_RESOURCE_LINKAGE',
      targetModId: 'kneekura_staff', buildArtifactHash: target.build_artifact_hash, configArtifactHash: target.config_hash,
      resourceArtifactHash: target.resource_hash, classResources: [{ className: 'org.kneekura.StaffMod', sha256: 'f'.repeat(64) }] },
    worldRegistration: { schemaVersion: 1, registrationId: 'operator-world', canonicalWorldRoot: world,
      worldName: 'KNEEKURA_DEBUG_WORLD', dimensionId: 'minecraft:overworld', permissions: ['BOUNDED_DIAGNOSTIC_CONTROL'] },
    selection: { grantId: 'grant', leaseId: 'lease', arenaEpoch: 0, expectedArenaRevision: 0, allowedActions: ['wait_ticks'] } };
  const identity = { debugSessionId: 's', runId: 'r', runSnapshotId: 'snap', processEpoch: 1, handshakeNonce: 'n'.repeat(32) };
  async function select(value = operator) {
    const bytes = Buffer.from(JSON.stringify(value)); await writeFile(path.join(privateRoot, 'operator.json'), bytes);
    return { trustedRoot: privateRoot, relativePath: 'operator.json', sha256: sha256(bytes) };
  }
  const options = { runtimeRoot, runDir, identity, bridgeContext, operatorRegistration: await select() };
  return { root, runDir, runtimeRoot, inputs, operator, identity, bridgeContext, options, select };
}

