/** Registered bounded intent publication; the in-JVM owner remains the mutation authority. */
import {sha256,stableJson,integer,hashId,identifier} from './json.mjs';
import path from 'node:path';
import { ownerTriggerIdentity, validateOwnerTriggerIntent } from './owner-trigger-config.mjs';

function same(a,b){return stableJson(a)===stableJson(b);}
export function validateControlState(prepared,receipt,status,{now=Date.now(),allowUnsafeCleanup=false,allowBusyObservation=false}={}) {
  const {receiptHash,...body}=receipt??{};hashId(receiptHash);
  if(sha256(stableJson(body))!==receiptHash||body.schemaVersion!==1||
      body.kind!=='owner_installation_receipt'||body.status!=='INSTALLED_SCOPED_CONTROL'||
      body.scope!=='BOUNDED_DIAGNOSTIC_CONTROL'||body.error!==null)throw new Error('OWNER_INSTALLATION_UNVERIFIED');
  for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch']) {
    if(body[key]!==prepared.envelope[key]||status?.[key]!==body[key])throw new Error('OWNER_IDENTITY_MISMATCH');
  }
  if(body.ownerEnvelopeHash!==prepared.envelopeHash||body.grantHash!==prepared.envelope.grantHash||
      body.runSnapshotHash!==prepared.snapshot.snapshotHash||status.ownerEnvelopeHash!==prepared.envelopeHash||
      status.installedReceiptHash!==receiptHash)throw new Error('OWNER_BINDING_MISMATCH');
  const grant=prepared.grant;
  if(body.leaseId!==grant.leaseId||body.arenaId!==grant.arenaId||body.arenaEpoch!==grant.arenaEpoch||
      body.arenaRevision!==grant.expectedArenaRevision||body.baselineHash!==grant.baselineHash||
      status.leaseId!==grant.leaseId||status.arenaId!==grant.arenaId||status.arenaEpoch!==grant.arenaEpoch)throw new Error('OWNER_ARENA_MISMATCH');
  integer(status.arenaRevision,grant.expectedArenaRevision,Number.MAX_SAFE_INTEGER);
  if(status.nextActionId!==null)identifier(status.nextActionId);
  const material=prepared.materialDescriptor,observed=body.materialLinkage,world=prepared.worldRegistration;
  if(!observed||observed.mode!==material.linkageMode||observed.targetModId!==material.targetModId||
      observed.buildArtifactHash!==material.buildArtifactHash||!Array.isArray(observed.classResources)||
      !same(observed.classResources.map(({className,sha256})=>({className,sha256})),material.classResources)||
      observed.configCertainty!=='ON_DISK_NOT_LOADED'||observed.resourceCertainty!=='ON_DISK_NOT_LOADED'||
      observed.transformedClassCertainty!=='NOT_ESTABLISHED'||observed.fullTargetAttestation!=='NOT_ESTABLISHED')throw new Error('OWNER_MATERIAL_SCOPE_MISMATCH');
  if(!body.worldObservation||body.worldObservation.canonicalWorldRoot!==world.canonicalWorldRoot||
      body.worldObservation.worldName!==world.worldName||body.worldObservation.dimensionId!==world.dimensionId||
      body.worldObservation.registrationHash!==prepared.envelope.worldRegistrationHash)throw new Error('OWNER_WORLD_MISMATCH');
  const observedAt=Date.parse(status.observedAt),installedAt=Date.parse(body.observedAt);
  if(status.schemaVersion!==1||!(allowUnsafeCleanup?['ACTIVE_SCOPED_CONTROL','OUTCOME_UNKNOWN']:['ACTIVE_SCOPED_CONTROL']).includes(status.status)||(allowBusyObservation?typeof status.idle!=='boolean':status.idle!==true)||
      (allowUnsafeCleanup?typeof status.unsafe!=='boolean':status.unsafe!==false)||
      !Number.isFinite(observedAt)||!Number.isFinite(installedAt)||!Number.isFinite(now)||
      now-observedAt>5000||observedAt-now>1000||installedAt-now>1000||now-installedAt>=grant.timeBudgetMs)
    throw new Error('OWNER_NOT_CURRENT_IDLE_CONTROL');
  return {installedReceiptHash:receiptHash,ownerEnvelopeHash:prepared.envelopeHash,
    runSnapshotHash:body.runSnapshotHash,arenaEpoch:status.arenaEpoch,arenaRevision:status.arenaRevision,nextActionId:status.nextActionId,
    scope:'BOUNDED_DIAGNOSTIC_CONTROL',fullTargetAttestation:'NOT_ESTABLISHED'};
}

export async function readInstalledControl({runDir,envelopeHash,now=Date.now(),allowUnsafeCleanup=false,allowBusyObservation=false}) {
  const {readPreparedOwnerControl}=await import('./owner-prelaunch.mjs');
  const {readRegisteredFile}=await import('./materials.mjs');
  const {decodeJson}=await import('./json.mjs');
  const prepared={...await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true}),envelopeHash};
  const read=async name=>decodeJson((await readRegisteredFile({root:runDir,relativePath:'control/'+name,maxBytes:1024*1024})).bytes);
  const receipt=await read('owner-installed.json'),status=await read('owner-status.json');
  const control=validateControlState(prepared,receipt,status,{now,allowUnsafeCleanup,allowBusyObservation});
  return {prepared,control,receipt};
}
export async function inspectOwnerControl(options) {
  const {prepared,control}=await readInstalledControl(options);
  return {schemaVersion:1,status:'ACTIVE_SCOPED_CONTROL',requestHash:prepared.envelope.requestHash,
    ...control,execution:'NOT_RUN',nextOperation:'submit_action'};
}

async function publishMarker(directory,name,value) {
  const {open,link,unlink,realpath,lstat}=await import('node:fs/promises');
  const path=(await import('node:path')).default;
  const {randomUUID}=await import('node:crypto');
  if(await realpath(directory)!==directory||!(await lstat(directory)).isDirectory())throw new Error('OWNER_INTENT_DIRECTORY_UNSAFE');
  const bytes=Buffer.from(stableJson(value)),temporary=path.join(directory,'.'+name+'-'+randomUUID()+'.tmp');
  const file=await open(temporary,'wx',0o600);
  try {await file.writeFile(bytes);await file.sync();}finally{await file.close();}
  try {await link(temporary,path.join(directory,name));}finally{await unlink(temporary);}
  return sha256(bytes);
}
function publicIntent(prepared,action,status,extra={}) {
  return {schemaVersion:1,status,requestHash:prepared.envelope.requestHash,selectedActionId:action.actionId,
    idempotencyKey:action.idempotencyKey,ownerEnvelopeHash:prepared.envelopeHash,
    execution:'NOT_CONFIRMED',scope:'BOUNDED_DIAGNOSTIC_CONTROL',fullTargetAttestation:'NOT_ESTABLISHED',...extra};
}
export async function submitSelectedAction({runDir,envelopeHash,selectedActionId,now=Date.now()}) {
  const {selectRetainedAction,actionIdempotencyKey}=await import('./selected-action.mjs');
  const {beginAction,readActionOutcome}=await import('./action-journal.mjs');
  const path=(await import('node:path')).default;
  const {prepared,control}=await readInstalledControl({runDir,envelopeHash,now});
  const {action,priorActionIds}=selectRetainedAction({request:prepared.request,grant:prepared.grant,selectedActionId});
  const identity={...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,prepared.identity[k]])),experimentId:prepared.request.experiment_id,
    subjects:Object.fromEntries(prepared.grant.subjects.map(s=>[s.subjectId,s.uuid]))};
  const existing=await readActionOutcome({runDir,identity,idempotencyKey:action.idempotencyKey});
  if(existing.status!=='NEVER_SEEN')return publicIntent(prepared,action,'ALREADY_RECORDED',{recordedStatus:existing.status});
  if(control.nextActionId!==selectedActionId)throw new Error('OWNER_ACTION_ORDER_MISMATCH');
  if(control.arenaEpoch!==action.arenaEpoch||control.arenaRevision!==action.expectedArenaRevision)throw new Error('OWNER_ACTION_REVISION_MISMATCH');
  for(const actionId of priorActionIds) {
    const prior=await readActionOutcome({runDir,identity,idempotencyKey:actionIdempotencyKey(prepared.grant,actionId)});
    if(prior.status!=='VERIFIED')throw new Error('PRIOR_ACTION_RECONCILIATION_REQUIRED');
  }
  const arena={schemaVersion:1,arenaId:action.arenaId,arenaEpoch:action.arenaEpoch,arenaRevision:action.expectedArenaRevision,
    baselineHash:prepared.grant.baselineHash,bounds:prepared.grant.bounds,allowedMutationBounds:prepared.grant.bounds,
    resetClasses:{blocks:'RESETTABLE',entities:'UNKNOWN'}};
  const rechecked=await readInstalledControl({runDir,envelopeHash});
  if(rechecked.control.arenaRevision!==control.arenaRevision||rechecked.control.installedReceiptHash!==control.installedReceiptHash||rechecked.control.nextActionId!==selectedActionId)
    throw new Error('OWNER_CHANGED_BEFORE_INTENT');
  let begun=false;
  try {
    const journal=await beginAction({runDir,arena,identity,action});begun=true;
    if(journal.alreadyRecorded)return publicIntent(prepared,action,'ALREADY_RECORDED',{recordedStatus:journal.status});
    const payloadHash=sha256(stableJson(action));
    const dispatch={schemaVersion:1,ownerEnvelopeHash:envelopeHash,runSnapshotId:prepared.envelope.runSnapshotId,
      runSnapshotHash:prepared.snapshot.snapshotHash,requestHash:prepared.envelope.requestHash,
      handshakeNonce:prepared.envelope.handshakeNonce,leaseId:prepared.grant.leaseId,
      selectedActionId,idempotencyKey:action.idempotencyKey,payloadHash};
    const dispatchHash=await publishMarker(path.join(runDir,'control','actions',sha256(action.idempotencyKey)),'dispatch.json',dispatch);
    return publicIntent(prepared,action,'REQUESTED',{dispatchHash,payloadHash});
  } catch(error) {
    if(!begun)throw error;
    return publicIntent(prepared,action,'OUTCOME_UNKNOWN');
  }
}

export function captureSlotKey(grant,captureIndex) {
  integer(captureIndex,0,3);
  return sha256(stableJson({captureIndex,processEpoch:grant.processEpoch,requestHash:grant.requestHash,
    runId:grant.runId,runSnapshotId:grant.runSnapshotId}));
}
export async function requestDeclaredCapture({runDir,envelopeHash,captureIndex,now=Date.now(),trigger=null,expectedIdentity=null,isClosed=()=>false}) {
  const {mkdir,realpath,lstat}=await import('node:fs/promises');
  const path=(await import('node:path')).default;
  const {prepared,control}=await readInstalledControl({runDir,envelopeHash,now});
  if(prepared.request.visual_rig.mode!=='cardinal-4-snapshot-v1'||
      !prepared.worldRegistration.permissions.includes('CARDINAL_CAPTURE_PAUSE_CAMERA'))throw new Error('OWNER_CAPTURE_NOT_AUTHORIZED');
  integer(captureIndex,0,Math.floor(prepared.grant.maxCaptures/4)-1);
  if(trigger!==null){
    validateOwnerTriggerIntent(prepared,captureIndex,trigger,now);
    if(!same(expectedIdentity,ownerTriggerIdentity(prepared,control.arenaRevision))||isClosed())throw new Error('TRIGGER_IDENTITY_OR_OWNER_CHANGED');
  }else if(prepared.triggerCapture?.captureIndices.includes(captureIndex))throw new Error('CAPTURE_SLOT_RESERVED_FOR_TRIGGER');
  const captureKey=captureSlotKey(prepared.grant,captureIndex),captureId='capture-'+captureKey;
  const publicValue={schemaVersion:1,requestHash:prepared.envelope.requestHash,ownerEnvelopeHash:envelopeHash,
    captureIndex,captureKey,captureId,execution:'NOT_CONFIRMED',scope:'BOUNDED_DIAGNOSTIC_CONTROL',fullTargetAttestation:'NOT_ESTABLISHED'};
  const parent=path.join(runDir,'control','captures');
  try {await mkdir(parent);}catch(error){if(error.code!=='EEXIST')throw error;}
  if(await realpath(parent)!==parent||!(await lstat(parent)).isDirectory())throw new Error('OWNER_CAPTURE_DIRECTORY_UNSAFE');
  const directory=path.join(parent,captureKey);
  try {await mkdir(directory);}catch(error){if(error.code==='EEXIST')return {...publicValue,status:'ALREADY_RECORDED'};throw error;}
  try {
    const marker={schemaVersion:1,ownerEnvelopeHash:envelopeHash,runSnapshotId:prepared.envelope.runSnapshotId,
      runSnapshotHash:prepared.snapshot.snapshotHash,requestHash:prepared.envelope.requestHash,
      handshakeNonce:prepared.envelope.handshakeNonce,leaseId:prepared.grant.leaseId,captureIndex,captureKey,captureId,
      expectedArenaEpoch:control.arenaEpoch,expectedArenaRevision:control.arenaRevision,...(trigger===null?{}:{trigger:structuredClone(trigger)})};
    const current=await readInstalledControl({runDir,envelopeHash});
    if(current.control.arenaEpoch!==control.arenaEpoch||current.control.arenaRevision!==control.arenaRevision||isClosed())
      throw new Error('OWNER_CHANGED_BEFORE_CAPTURE');
    if(trigger!==null)validateOwnerTriggerIntent(current.prepared,captureIndex,trigger,Date.now());
    const dispatchHash=await publishMarker(directory,'request.json',marker);
    return {...publicValue,status:'REQUESTED',dispatchHash};
  } catch {
    return {...publicValue,status:'OUTCOME_UNKNOWN'};
  }
}
export async function inspectSelectedAction({runDir,envelopeHash,selectedActionId}) {
  const {readPreparedOwnerControl}=await import('./owner-prelaunch.mjs');
  const {selectRetainedAction}=await import('./selected-action.mjs');
  const {readActionOutcome}=await import('./action-journal.mjs');
  const prepared={...await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true}),envelopeHash};
  const {action}=selectRetainedAction({request:prepared.request,grant:prepared.grant,selectedActionId});
  const identity={...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,prepared.identity[k]])),experimentId:prepared.request.experiment_id};
  const outcome=await readActionOutcome({runDir,identity,idempotencyKey:action.idempotencyKey});
  return publicIntent(prepared,action,'REPORTED_ACTION',{reportedStatus:outcome.status,recordedStatus:outcome.recordedStatus??null,evidenceHashes:outcome.evidenceHashes??[],dispatchAllowed:false,execution:'NOT_RUN'});
}

export function privateExportRoot(runDir,inputRoot,requestHash){
  hashId(requestHash);
  const root=path.join(inputRoot,'exports',requestHash);
  const inside=(parent,candidate)=>{
    const rel=path.relative(parent,candidate);
    return rel!== '..'&&!rel.startsWith('..'+path.sep)&&!path.isAbsolute(rel);
  };
  if(inside(runDir,inputRoot)||inside(runDir,root)||inside(root,runDir))throw new Error('EXPORT_MUST_STAY_OUTSIDE_SEALED_RUN');
  return root;
}

export function ownerCleanupKey(grant){
  return sha256(stableJson({operation:'owner_cleanup_reset',processEpoch:grant.processEpoch,
    requestHash:grant.requestHash,runId:grant.runId,runSnapshotId:grant.runSnapshotId}));
}
export async function requestOwnerCleanup({runDir,envelopeHash,now=Date.now()}){
  const {mkdir}=await import('node:fs/promises');
  const {prepared,control}=await readInstalledControl({runDir,envelopeHash,now,allowUnsafeCleanup:true});
  const cleanupKey=ownerCleanupKey(prepared.grant),value={schemaVersion:1,requestHash:prepared.envelope.requestHash,
    ownerEnvelopeHash:envelopeHash,cleanupKey,execution:'NOT_CONFIRMED',scope:'BOUNDED_DIAGNOSTIC_CONTROL',fullTargetAttestation:'NOT_ESTABLISHED'};
  const directory=path.join(runDir,'control','owner-cleanup');
  try{await mkdir(directory);}catch(error){if(error.code==='EEXIST')return {...value,status:'ALREADY_RECORDED'};throw error;}
  try{
    const current=await readInstalledControl({runDir,envelopeHash,allowUnsafeCleanup:true});
    if(current.control.arenaEpoch!==control.arenaEpoch||current.control.arenaRevision!==control.arenaRevision||
       current.control.installedReceiptHash!==control.installedReceiptHash)throw new Error('OWNER_CHANGED_BEFORE_CLEANUP');
    const marker={schemaVersion:1,ownerEnvelopeHash:envelopeHash,runSnapshotId:prepared.envelope.runSnapshotId,
      runSnapshotHash:prepared.snapshot.snapshotHash,requestHash:prepared.envelope.requestHash,
      handshakeNonce:prepared.envelope.handshakeNonce,leaseId:prepared.grant.leaseId,
      expectedArenaEpoch:control.arenaEpoch,expectedArenaRevision:control.arenaRevision,cleanupKey};
    const dispatchHash=await publishMarker(directory,'request.json',marker);
    return {...value,status:'REQUESTED',dispatchHash};
  }catch{return {...value,status:'OUTCOME_UNKNOWN'};}
}
export async function inspectOwnerCleanup({runDir,envelopeHash}){
  const {readPreparedOwnerControl}=await import('./owner-prelaunch.mjs');
  const {readActionOutcome}=await import('./action-journal.mjs');
  const {lstat}=await import('node:fs/promises');
  const prepared=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true});
  const identity={...Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch'].map(k=>[k,prepared.identity[k]])),experimentId:prepared.request.experiment_id};
  const outcome=await readActionOutcome({runDir,identity,idempotencyKey:ownerCleanupKey(prepared.grant)});
  let reportedStatus=outcome.status;
  if(reportedStatus==='NEVER_SEEN'){
    try{await lstat(path.join(runDir,'control','owner-cleanup'));reportedStatus='OUTCOME_UNKNOWN';}
    catch(error){if(error.code!=='ENOENT')reportedStatus='OUTCOME_UNKNOWN';}
  }
  return {schemaVersion:1,requestHash:prepared.envelope.requestHash,reportedStatus,
    recordedStatus:outcome.recordedStatus??null,evidenceHashes:outcome.evidenceHashes??[],dispatchAllowed:false};
}
