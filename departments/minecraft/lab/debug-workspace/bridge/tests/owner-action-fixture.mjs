import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, readdir, rm, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { sha256, stableJson } from '../json.mjs';
import { registerBridgeRequest } from '../registration.mjs';
import { prepareOwnerControl, readPreparedOwnerControl, ownerLaunchEnvironment } from '../owner-prelaunch.mjs';
import { buildRunSnapshot, writeImmutableRunSnapshot } from '../../core.mjs';

export async function ownerFixture(t, {capture=false,captureRig='cardinal-4-snapshot-v1',mobPov=false,observation=false,triggerCapture=null,requestBytesOverride=null,assertionsBytesOverride=null}={}) {
  const root = await mkdtemp(path.join(tmpdir(), 'owner-prelaunch-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const runtimeRoot = path.join(root, 'runtime'); const inputs = path.join(root, 'inputs');
  const privateRoot = path.join(root, 'private'); const world = path.join(root, 'KNEEKURA_DEBUG_WORLD');
  const runDir = path.join(runtimeRoot, 'sessions', 's', 'runs', 'r');
  for (const dir of [inputs, privateRoot, world, runDir]) await mkdir(dir, { recursive: true });
  let target = { profile_id: 'a'.repeat(64), index_snapshot_id: 'b'.repeat(64), build_artifact_hash: sha256('build'),
    source_revision: 'c'.repeat(40), dirty_hash: 'd'.repeat(64), config_hash: sha256('config'), resource_hash: sha256('resources') };
  let assertions = [{ assertion_id: 'health', subject_id: 'pig', kind: 'structured', field: 'health', operator: 'equals', expected: 20 }];
  let request = { schema_version: 1, experiment_id: 'experiment', generation: 1, target,
    arena: { arena_id: 'arena', preset: 'normal', baseline_hash: 'e'.repeat(64), bounds: { min: [0,0,0], max: [8,8,8] } },
    subjects: [{ subject_id: 'pig', uuid: '00000000-0000-0000-0000-000000000001', entity_type: 'minecraft:pig' }],
    initial_state: [], actions: [{ action_id: 'wait', operation: 'wait_ticks', ticks: 1 }],
    observation_scopes: [{ kind: 'ENTITY_UUID', subject_id: 'pig', lanes: ['SERVER_ENTITY_STATE'], level: 'L1' }],
    visual_rig: { mode: 'none' }, assertions, budgets: { time_budget_ms: 5000, max_actions: 1, max_captures: 0 } };
  if(capture){request.visual_rig={mode:captureRig,fov:60,viewport:[64,64]};request.budgets.max_captures=4;}
  if(mobPov){request.visual_rig={mode:'mob-eye-live-v1',fov:60,viewport:[64,64]};request.budgets.max_captures=capture?1:0;}
  const requestBytes = requestBytesOverride ?? Buffer.from(JSON.stringify(request));
  assert(Buffer.isBuffer(requestBytes));request=JSON.parse(requestBytes);target=request.target;assertions=request.assertions;
  const assertionsBytes=assertionsBytesOverride??Buffer.from(JSON.stringify(assertions));
  assert(Buffer.isBuffer(assertionsBytes));assert.equal(stableJson(JSON.parse(assertionsBytes)),stableJson(assertions));
  const binding = { schema_version: 1, experiment_id: request.experiment_id, generation: request.generation, request_hash: sha256(requestBytes),
    target, arena_id: request.arena.arena_id, arena_baseline_hash: request.arena.baseline_hash, assertions_hash: sha256(assertionsBytes) };
  for (const [name, value] of Object.entries({ 'request.json': requestBytes, 'binding.json': JSON.stringify(binding),
    'assertions.json': assertionsBytes, 'build.bin': 'build', 'config.bin': 'config', 'resource.bin': 'resources' }))
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
  if(['cardinal-4-snapshot-v1','tank-cardinal-4-snapshot-v2'].includes(request.visual_rig.mode))operator.worldRegistration.permissions.push('CARDINAL_CAPTURE_PAUSE_CAMERA');
  if(request.visual_rig.mode==='mob-eye-live-v1')operator.worldRegistration.permissions.push('MOB_POV_CAMERA');
  if(triggerCapture!==null)operator.triggerCapture=structuredClone(triggerCapture);
  if(observation){
   const recipe={v:1,kind:'tank_recipe',dimension:'minecraft:overworld',origin:{x:0,y:0,z:0},dimensions:{width:16,height:8,depth:16},presentation:{mode:'NATIVE',gridSpacing:1}};
   const recipeHash=sha256(stableJson(recipe));
   await writeFile(path.join(world,'kneekura-tank-owner.json'),JSON.stringify({status:'GEOMETRY_VERIFIED',displayMode:'NATIVE',recipeHash,recipe}));
   operator.worldRegistration.permissions.push('TANK_OBSERVATION_READ');operator.tankObservation={schemaVersion:1,scope:'TANK_OBSERVATION_READ',dimensionId:'minecraft:overworld',min:[0,0,0],max:[16,8,16],recipeHash,maxEntities:4,maxSamples:2};
  }
  const identity = { debugSessionId: 's', runId: 'r', runSnapshotId: 'snap', processEpoch: 1, handshakeNonce: 'n'.repeat(32) };
  async function select(value = operator) {
    const bytes = Buffer.from(JSON.stringify(value)); await writeFile(path.join(privateRoot, 'operator.json'), bytes);
    return { trustedRoot: privateRoot, relativePath: 'operator.json', sha256: sha256(bytes) };
  }
  const options = { runtimeRoot, runDir, identity, bridgeContext, operatorRegistration: await select() };
  return { root, runDir, runtimeRoot, inputs, operator, identity, bridgeContext, options, select, requestBytes, assertionsBytes };
}

export async function preparedOwner(t,options={}){
 const f=await ownerFixture(t,options),p=await prepareOwnerControl(f.options);
 await writeImmutableRunSnapshot(path.join(f.runDir,'run-snapshot.json'),buildRunSnapshot({schemaVersion:1,snapshotId:'snap',
  createdAt:new Date().toISOString(),debugProfile:'owner-source-fixture',workspaceId:'fixture-workspace',
  debugSessionId:'s',runId:'r',processEpoch:1,worldName:'KNEEKURA_DEBUG_WORLD',
  source:{revision:f.bridgeContext.binding.target.source_revision},observer:{basis:'SOURCE_FIXTURE_NOT_RUNTIME'},build:{status:'NOT_RUN'},
  runtime:{pid:process.pid,attestation:{topology:'INTEGRATED_SERVER',basis:'SOURCE_FIXTURE_NOT_RUNTIME'}}},
  {...f.bridgeContext,ownerControlIntent:p.ownerControlIntent}));
 const prepared={...await readPreparedOwnerControl({runDir:f.runDir,envelopeHash:p.envelopeHash,requireSnapshot:true}),envelopeHash:p.envelopeHash};
 const now=Date.now(),receipt={schemaVersion:1,kind:'owner_installation_receipt',status:'INSTALLED_SCOPED_CONTROL',...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,prepared.envelope[k]])),runSnapshotHash:prepared.snapshot.snapshotHash,ownerEnvelopeHash:p.envelopeHash,grantHash:prepared.envelope.grantHash,leaseId:prepared.grant.leaseId,arenaId:prepared.grant.arenaId,arenaEpoch:0,arenaRevision:0,baselineHash:prepared.grant.baselineHash,scope:'BOUNDED_DIAGNOSTIC_CONTROL',observedAt:new Date(now).toISOString(),materialLinkage:{mode:prepared.materialDescriptor.linkageMode,targetModId:prepared.materialDescriptor.targetModId,buildArtifactHash:prepared.materialDescriptor.buildArtifactHash,containerIdentity:'fixture-only-not-a-JVM',classResources:prepared.materialDescriptor.classResources,configCertainty:'ON_DISK_NOT_LOADED',resourceCertainty:'ON_DISK_NOT_LOADED',transformedClassCertainty:'NOT_ESTABLISHED',fullTargetAttestation:'NOT_ESTABLISHED'},worldObservation:{canonicalWorldRoot:prepared.worldRegistration.canonicalWorldRoot,worldName:prepared.worldRegistration.worldName,dimensionId:prepared.worldRegistration.dimensionId,registrationHash:prepared.envelope.worldRegistrationHash},error:null};
 receipt.receiptHash=sha256(stableJson(receipt));
 const status={schemaVersion:1,...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,prepared.envelope[k]])),ownerEnvelopeHash:p.envelopeHash,installedReceiptHash:receipt.receiptHash,leaseId:prepared.grant.leaseId,arenaId:prepared.grant.arenaId,arenaEpoch:0,arenaRevision:0,idle:true,unsafe:false,nextActionId:'wait',status:'ACTIVE_SCOPED_CONTROL',observedAt:new Date(now).toISOString()};
 await writeFile(path.join(f.runDir,'control/owner-installed.json'),JSON.stringify(receipt));await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(status));
 return {...f,prepared,receipt,status,controlOptions:{runDir:f.runDir,envelopeHash:p.envelopeHash}};
}
