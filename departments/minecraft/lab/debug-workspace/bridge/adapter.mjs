/** Explicit local file adapter. No launch, endpoint, runtime install or mutation dispatch. */
import { lstat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { exactKeys, integer, hashId, identifier, decodeJson } from './json.mjs';
import { readRegisteredFile } from './materials.mjs';
import { registerBridgeRequest, loadBridgeRegistration } from './registration.mjs';
import { readActionOutcome } from './action-journal.mjs';

async function directory(value) {
  if (typeof value !== 'string' || !path.isAbsolute(value) || await realpath(value) !== path.resolve(value) || !(await lstat(value)).isDirectory()) throw new TypeError('UNSAFE_ADAPTER_DIRECTORY');
  return value;
}
export async function validateAdapterOwner(owner) {
  exactKeys(owner,['schemaVersion','runtimeRoot','inputRoot','run'],'ADAPTER_OWNER');
  integer(owner.schemaVersion,1,1);
  await directory(owner.runtimeRoot); await directory(owner.inputRoot);
  if (owner.run !== null) {
    exactKeys(owner.run,['runDir','identity'],'ADAPTER_RUN');
    await directory(owner.run.runDir);
    if (!path.relative(owner.runtimeRoot,owner.run.runDir) || path.relative(owner.runtimeRoot,owner.run.runDir).startsWith('..') || path.isAbsolute(path.relative(owner.runtimeRoot,owner.run.runDir))) throw new Error('RUN_OUTSIDE_OWNER_ROOT');
    const identity=owner.run.identity;
    exactKeys(identity,['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','requestHash'],'ADAPTER_IDENTITY');
    for (const key of ['debugSessionId','runId','runSnapshotId','experimentId']) identifier(identity[key]);
    integer(identity.processEpoch,0,Number.MAX_SAFE_INTEGER); hashId(identity.requestHash);
    const snapshot=decodeJson((await readRegisteredFile({root:owner.run.runDir,relativePath:'run-snapshot.json',maxBytes:2*1024*1024})).bytes,2*1024*1024);
    if (snapshot.debugSessionId!==identity.debugSessionId || snapshot.runId!==identity.runId || snapshot.snapshotId!==identity.runSnapshotId || snapshot.processEpoch!==identity.processEpoch || snapshot.techHub?.experiment_id!==identity.experimentId || snapshot.techHub?.request_hash!==identity.requestHash) throw new Error('ADAPTER_RUN_IDENTITY_MISMATCH');
  }
  return structuredClone(owner);
}
function publicRegistration(registered) {
  return {schemaVersion:1,status:'REGISTERED',requestHash:registered.binding.request_hash,
    registrationHash:registered.registrationHash,experimentId:registered.binding.experiment_id,
    generation:registered.binding.generation,execution:'NOT_RUN',runtimeAttestation:'NOT_ESTABLISHED',
    capabilityReadiness:{execution:'BLOCKED',arena:'BLOCKED',capture:'BLOCKED'}};
}
export async function invokeAdapter(owner,request) {
  owner=await validateAdapterOwner(owner);
  const reconcile=request?.operation==='reconcile_action';
  exactKeys(request,reconcile?['schemaVersion','operation','requestHash','idempotencyKey']:['schemaVersion','operation','requestHash'],'ADAPTER_REQUEST');
  integer(request.schemaVersion,1,1); hashId(request.requestHash);
  if (request.operation==='register') {
    const trustedRoot=path.join(owner.inputRoot,request.requestHash);
    await directory(trustedRoot);
    return publicRegistration(await registerBridgeRequest({runtimeRoot:owner.runtimeRoot,expectedRequestHash:request.requestHash,registration:{
      schemaVersion:1,trustedRoot,requestFile:'request.json',bindingFile:'binding.json',assertionsFile:'assertions.json',
      materials:{buildArtifact:{relativePath:'build.bin'},configArtifact:{relativePath:'config.bin'},resourceArtifact:{relativePath:'resource.bin'}},
    }}));
  }
  if (request.operation==='inspect_registration') {
    let marker=owner.runtimeRoot;
    for(const segment of ['bridge','registrations',request.requestHash]) {
      marker=path.join(marker,segment);
      try { await directory(marker); } catch(error) {
        if(error.code!=='ENOENT') throw error;
        return {schemaVersion:1,status:'NEVER_SEEN',requestHash:request.requestHash,execution:'NOT_RUN',runtimeAttestation:'NOT_ESTABLISHED'};
      }
    }
    return publicRegistration(await loadBridgeRegistration({runtimeRoot:owner.runtimeRoot,requestHash:request.requestHash}));
  }
  if (reconcile) {
    identifier(request.idempotencyKey);
    if(!owner.run || owner.run.identity.requestHash!==request.requestHash) throw new Error('REGISTERED_RUN_REQUIRED');
    const result=await readActionOutcome({runDir:owner.run.runDir,identity:owner.run.identity,idempotencyKey:request.idempotencyKey});
    return {schemaVersion:1,status:result.status,recordedStatus:result.recordedStatus??null,
      requestHash:request.requestHash,idempotencyKey:request.idempotencyKey,
      evidenceHashes:result.evidenceHashes??[],dispatchAllowed:false,runtimeAttestation:'NOT_ESTABLISHED'};
  }
  throw new TypeError('UNSUPPORTED_ADAPTER_OPERATION');
}
