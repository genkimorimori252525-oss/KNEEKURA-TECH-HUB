/** Mob POV intents only; real client/server owner decides whether an operation can run. */
import path from 'node:path';
import {mkdir,lstat,realpath,open,link,unlink} from 'node:fs/promises';
import {randomUUID} from 'node:crypto';
import {exactKeys,integer,hashId,stableJson,sha256,decodeJson} from './json.mjs';
import {readRegisteredFile} from './materials.mjs';
import {readInstalledControl} from './owner-action-adapter.mjs';
import {readPreparedOwnerControl} from './owner-prelaunch.mjs';
import {validateVisualIdentity,readBoundedRawImage} from '../evidence/visual-capture.mjs';

export function validateMobPovCommand(command,prepared){
 const fields=['commandIndex','operation'];if(command?.operation==='attach')fields.push('subjectUuid','durationMs');
 exactKeys(command,fields,'MOB_POV_COMMAND');integer(command.commandIndex,0,31);
 if(!['attach','snapshot','return'].includes(command.operation))throw new Error('MOB_POV_OPERATION');
 if(prepared.request.visual_rig.mode!=='mob-eye-live-v1')throw new Error('MOB_POV_RIG_REQUIRED');
 if(command.operation==='attach'){
  integer(command.durationMs,1,120000);
  if(!prepared.grant.subjects.some(s=>s.uuid===command.subjectUuid))throw new Error('MOB_POV_SUBJECT_NOT_REGISTERED');
 }
 if(command.operation==='snapshot'&&prepared.grant.maxCaptures===0)throw new Error('MOB_POV_VIEW_ONLY');
 return structuredClone(command);
}
function directoryFor(runDir,index){return path.join(runDir,'control','mob-pov',String(index).padStart(2,'0'));}
async function safeDirectory(value){
 if(await realpath(value)!==value||!(await lstat(value)).isDirectory())throw new Error('MOB_POV_DIRECTORY_UNSAFE');
}
export async function publishMobPovCommand({runDir,envelopeHash,...command}){
 const prepared={...await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true}),envelopeHash};
 validateMobPovCommand(command,prepared);
 if(!prepared.worldRegistration.permissions.includes('MOB_POV_CAMERA'))throw new Error('MOB_POV_PERMISSION_MISSING');
 const relative='control/mob-pov/'+String(command.commandIndex).padStart(2,'0');
 let existing;
 try{existing=decodeJson((await readRegisteredFile({root:runDir,relativePath:relative+'/request.json',maxBytes:16384})).bytes);}
 catch(error){if(error.code!=='ENOENT')throw error;}
 if(existing){
  const selected=Object.fromEntries(Object.keys(command).map(k=>[k,existing[k]]));
  if(existing.ownerEnvelopeHash!==envelopeHash||stableJson(selected)!==stableJson(command))throw new Error('MOB_POV_REPLAY_CONFLICT');
  return {status:'ALREADY_REQUESTED',commandIndex:command.commandIndex,execution:'NOT_CONFIRMED'};
 }
 if(command.commandIndex>0)await readReceipt(runDir,envelopeHash,prepared,command.commandIndex-1);
 const {control}=await readInstalledControl({runDir,envelopeHash,minRemainingMs:command.operation==='return'?0:100});
 const marker={schemaVersion:1,...command,ownerEnvelopeHash:envelopeHash,runSnapshotId:prepared.envelope.runSnapshotId,
  runSnapshotHash:prepared.snapshot.snapshotHash,requestHash:prepared.envelope.requestHash,handshakeNonce:prepared.envelope.handshakeNonce,
  leaseId:prepared.grant.leaseId,expectedArenaEpoch:control.arenaEpoch,expectedArenaRevision:control.arenaRevision};
 for(const dir of [path.join(runDir,'control','mob-pov'),directoryFor(runDir,command.commandIndex)]){
  try{await mkdir(dir);}catch(error){if(error.code!=='EEXIST')throw error;}await safeDirectory(dir);
 }
 const dir=directoryFor(runDir,command.commandIndex),bytes=Buffer.from(stableJson(marker)),temp=path.join(dir,'.request-'+randomUUID()+'.tmp');
 const file=await open(temp,'wx',0o600);try{await file.writeFile(bytes);await file.sync();}finally{await file.close();}
 try{await link(temp,path.join(dir,'request.json'));}finally{await unlink(temp);}
 return {status:'REQUESTED',commandIndex:command.commandIndex,requestHash:prepared.envelope.requestHash,markerHash:sha256(bytes),execution:'NOT_CONFIRMED'};
}
export async function inspectMobPovCommand({runDir,envelopeHash,commandIndex}){
 integer(commandIndex,0,31);hashId(envelopeHash);
 const p=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true});
 const receipt=await readReceipt(runDir,envelopeHash,p,commandIndex);
 return {status:receipt.status,commandIndex,cameraOperation:receipt.operation,restoration:receipt.restoration??null,
  imageHash:receipt.imageHash??null,error:receipt.error??null,execution:'REPORTED_BY_OWNER'};
}
async function readReceipt(runDir,envelopeHash,p,commandIndex){
 const relative='control/mob-pov/'+String(commandIndex).padStart(2,'0');
 const receipt=decodeJson((await readRegisteredFile({root:runDir,relativePath:relative+'/receipt.json',maxBytes:16384})).bytes);
 const marker=decodeJson((await readRegisteredFile({root:runDir,relativePath:relative+'/request.json',maxBytes:16384})).bytes);
 const expected={attach:'ATTACHED',snapshot:'CAPTURED',return:'RETURNED'};
 if(receipt.schemaVersion!==1||receipt.kind!=='mob_pov_operation_receipt'||receipt.ownerEnvelopeHash!==envelopeHash||receipt.runSnapshotHash!==p.snapshot.snapshotHash||
  receipt.requestHash!==p.envelope.requestHash||receipt.commandIndex!==commandIndex||receipt.operation!==marker.operation||marker.ownerEnvelopeHash!==envelopeHash||
  marker.runSnapshotHash!==p.snapshot.snapshotHash||marker.requestHash!==p.envelope.requestHash||marker.commandIndex!==commandIndex||
  !Number.isFinite(Date.parse(receipt.observedAt))||![expected[marker.operation],'REJECTED','OUTCOME_UNKNOWN'].filter(Boolean).includes(receipt.status))throw new Error('MOB_POV_RECEIPT_IDENTITY_OR_STATUS');
 if(receipt.status===expected[marker.operation]&&receipt.result?.status!==receipt.status)throw new Error('MOB_POV_RECEIPT_RESULT');
 return receipt;
}
function requireValue(value,reason){if(!value)throw new Error(reason);}
function finite(value,min=-30000000,max=30000000){requireValue(typeof value==='number'&&Number.isFinite(value)&&value>=min&&value<=max,'MOB_POV_FINITE_NUMBER');}
function vector(value,size){requireValue(Array.isArray(value)&&value.length===size,'MOB_POV_VECTOR');value.forEach(n=>finite(n));}
export function validateMobPovFrame(frame,p){
 const f=structuredClone(frame);
 exactKeys(f,['schemaVersion','kind','rig','identity','subjectUuid','entityType','dimension','clientTick','renderFrame','captureId','imageHash','imageBytes','imagePath',
  'captureStage','artifactRole','partialTick','clientGameTime','serverReference','timePairing','aiPerceptionVerdict','cameraEffect','camera'],'MOB_POV_FRAME');
 integer(f.schemaVersion,1,1);validateVisualIdentity(f.identity);
 requireValue(f.kind==='mob_pov_raw_frame'&&f.rig==='mob-eye-live-v1'&&p.request.visual_rig.mode===f.rig&&p.grant.maxCaptures>0,'MOB_POV_FRAME_RIG');
 const g=p.grant;
 for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch','experimentId'])requireValue(f.identity[key]===g[key],'MOB_POV_FRAME_IDENTITY');
 for(const key of ['generation','requestHash','arenaId','arenaEpoch','baselineHash'])requireValue(f.identity[key]===g[key],'MOB_POV_FRAME_IDENTITY');
 const subject=p.request.subjects.find(s=>s.uuid===f.subjectUuid);
 requireValue(subject?.entity_type===f.entityType&&f.dimension===p.worldRegistration.dimensionId,'MOB_POV_FRAME_SUBJECT');
 requireValue(/^mob-pov-(?:[0-9]|[12][0-9]|3[01])$/.test(f.captureId),'MOB_POV_CAPTURE_ID');
 for(const key of ['clientTick','renderFrame','clientGameTime'])integer(f[key],0,Number.MAX_SAFE_INTEGER);finite(f.partialTick,0,1);
 hashId(f.imageHash);integer(f.imageBytes,1,4*1024*1024);
 requireValue(f.imagePath===`evidence/raw/visual/${f.imageHash}.png`&&f.artifactRole==='RAW_SCENE_RGB'&&f.captureStage==='AFTER_LEVEL_BEFORE_POST_EFFECT_HAND_HUD','MOB_POV_RAW_ARTIFACT');
 requireValue(f.timePairing==='INDEPENDENT_ASYNC_SERVER_SAMPLE_NOT_SAME_TICK'&&f.aiPerceptionVerdict==='NOT_ESTABLISHED'&&['NONE','ACTIVE_NOT_INCLUDED_AT_THIS_STAGE'].includes(f.cameraEffect),'MOB_POV_CERTAINTY');
 const reference=f.serverReference;
 exactKeys(reference,['identity','serverTick','serverGameTime','subjectUuid','validatedAtNanos','reservationToken','position'],'MOB_POV_SERVER_REFERENCE');
 requireValue(stableJson(reference.identity)===stableJson(f.identity)&&reference.subjectUuid===f.subjectUuid,'MOB_POV_SERVER_IDENTITY');
 for(const key of ['serverTick','serverGameTime','validatedAtNanos'])integer(reference[key],0,Number.MAX_SAFE_INTEGER);
 requireValue(typeof reference.reservationToken==='string'&&reference.reservationToken.length>0&&reference.reservationToken.length<=256,'MOB_POV_RESERVATION');vector(reference.position,3);
 const c=f.camera;exactKeys(c,['position','quaternion','yaw','pitch','fov','projectionMatrix','viewMatrix','viewport','matrixConvention'],'MOB_POV_CAMERA');
 vector(c.position,3);vector(c.quaternion,4);vector(c.projectionMatrix,16);vector(c.viewMatrix,16);finite(c.yaw);finite(c.pitch);finite(c.fov,29.999,100.001);
 requireValue(Math.abs(c.fov-p.request.visual_rig.fov)<=.001&&stableJson(c.viewport)===stableJson(p.request.visual_rig.viewport)&&c.matrixConvention==='JOML_COLUMN_MAJOR_CAMERA_RELATIVE','MOB_POV_CAMERA_RIG');
 return f;
}
/** Retrieve only an explicitly completed capture bound to this registered owner and receipt. */
export async function readMobPovImage({runDir,envelopeHash,commandIndex}){
 integer(commandIndex,0,31);hashId(envelopeHash);
 const p=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true}),receipt=await readReceipt(runDir,envelopeHash,p,commandIndex);
 requireValue(receipt.status==='CAPTURED'&&receipt.operation==='snapshot','MOB_POV_CAPTURE_NOT_COMPLETED');
 const {status,observationPayloadHash,...raw}=receipt.result;hashId(observationPayloadHash);
 const f=validateMobPovFrame(raw,p);
 requireValue(f.captureId==='mob-pov-'+commandIndex&&receipt.imageHash===f.imageHash&&receipt.imageBytes===f.imageBytes&&receipt.imagePath===f.imagePath&&receipt.observationPayloadHash===observationPayloadHash,'MOB_POV_RECEIPT_IMAGE');
 return readBoundedRawImage(runDir,f);
}
/** Finalization seals explicit images and their finite command records against canonical observations. */
export async function sealMobPovArtifacts(runDir,observations,artifacts){
 let request;
 try{request=decodeJson((await readRegisteredFile({root:runDir,relativePath:'control/owner-experiment-request.json',maxBytes:128*1024})).bytes);}
 catch(error){if(error.code==='ENOENT')return;throw error;}
 if(request.visual_rig?.mode!=='mob-eye-live-v1')return;
 const envelopeHash=sha256((await readRegisteredFile({root:runDir,relativePath:'control/owner-envelope.json',maxBytes:16384})).bytes);
 const p=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true});
 function retain(relativePath,bytes){
  const file=path.join(runDir,relativePath),row={path:file,size:bytes.length,sha256:'sha256:'+sha256(bytes)},old=artifacts.find(a=>a.path===file);
  if(old&&stableJson(old)!==stableJson(row))throw new Error('MOB_POV_ARTIFACT_CHANGED');if(!old)artifacts.push(row);
 }
 for(let i=0;i<32;i++){
  const dir='control/mob-pov/'+String(i).padStart(2,'0');let receipt;
  try{receipt=await readReceipt(runDir,envelopeHash,p,i);}catch(error){if(error.code==='ENOENT')continue;throw error;}
  for(const name of ['request.json','native-reservation.json','receipt.json']){
   try{retain(dir+'/'+name,(await readRegisteredFile({root:runDir,relativePath:dir+'/'+name,maxBytes:16384})).bytes);}catch(error){if(error.code!=='ENOENT')throw error;}
  }
  if(receipt.status!=='CAPTURED')continue;
  const {status,observationPayloadHash,...raw}=receipt.result,f=validateMobPovFrame(raw,p);
  const source=observations.find(row=>stableJson(row.payload)===stableJson(f)&&row.debugSessionId===f.identity.debugSessionId&&row.runId===f.identity.runId&&
   row.runSnapshotId===f.identity.runSnapshotId&&row.processEpoch===f.identity.processEpoch&&row.arenaEpoch===f.identity.arenaEpoch&&
   row.scope?.kind==='EXPERIMENT'&&row.scope.experimentId===f.identity.experimentId&&row.epistemicStatus==='OBSERVED'&&row.completeness?.complete===true);
  requireValue(source,'MOB_POV_CANONICAL_SOURCE_MISSING');
  retain(f.imagePath,await readMobPovImage({runDir,envelopeHash,commandIndex:i}));
 }
}
