#!/usr/bin/env node
/** Fixed local owner operations. No start command, executable argument or arbitrary action payload. */
import path from 'node:path';
import {lstat,mkdir,open,realpath} from 'node:fs/promises';
import {exactKeys,integer,identifier,hashId,decodeJson,sha256,stableJson} from './json.mjs';
import {readRegisteredFile} from './materials.mjs';
import {readPreparedOwnerControl} from './owner-prelaunch.mjs';
import {inspectOwnerControl,submitSelectedAction,requestDeclaredCapture,inspectSelectedAction,privateExportRoot,requestOwnerCleanup,inspectOwnerCleanup} from './owner-action-adapter.mjs';
import {actionIdempotencyKey} from './selected-action.mjs';
import {exportFinalizedExperiment} from './result-export.mjs';
import {EvidenceRuntime} from '../evidence/runtime.mjs';
import {watchOwnerTriggerCaptures} from './owner-trigger-source.mjs';

async function directory(value){
 if(typeof value!=='string'||!path.isAbsolute(value)||path.resolve(value)!==value||await realpath(value)!==value||!(await lstat(value)).isDirectory())throw new Error('OWNER_DIRECTORY_UNSAFE');
 return value;
}
async function input(file,limit){
 if(typeof file!=='string'||!path.isAbsolute(file))throw new Error('ABSOLUTE_INPUT_REQUIRED');
 return decodeJson((await readRegisteredFile({root:path.dirname(file),relativePath:path.basename(file),maxBytes:limit})).bytes,limit);
}
async function ownerScope(owner,command){
 exactKeys(owner,['schemaVersion','runtimeRoot','inputRoot','run'],'CONTROL_OWNER');integer(owner.schemaVersion,1,1);
 await directory(owner.runtimeRoot);await directory(owner.inputRoot);
 exactKeys(owner.run,['runDir','identity','ownerEnvelopeHash'],'CONTROL_RUN');await directory(owner.run.runDir);hashId(owner.run.ownerEnvelopeHash);
 const relative=path.relative(owner.runtimeRoot,owner.run.runDir);
 if(!relative||relative.startsWith('..')||path.isAbsolute(relative))throw new Error('RUN_OUTSIDE_REGISTERED_ROOT');
 const id=owner.run.identity;exactKeys(id,['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','requestHash'],'CONTROL_IDENTITY');
 for(const k of ['debugSessionId','runId','runSnapshotId','experimentId'])identifier(id[k]);integer(id.processEpoch,1,2147483647);hashId(id.requestHash);
 if(command.requestHash!==id.requestHash)throw new Error('CONTROL_REQUEST_MISMATCH');
 const p=await readPreparedOwnerControl({runDir:owner.run.runDir,envelopeHash:owner.run.ownerEnvelopeHash,requireSnapshot:true});
 for(const k of ['debugSessionId','runId','runSnapshotId','processEpoch'])if(p.envelope[k]!==id[k])throw new Error('CONTROL_RUN_MISMATCH');
 if(p.envelope.requestHash!==id.requestHash||p.request.experiment_id!==id.experimentId)throw new Error('CONTROL_EXPERIMENT_MISMATCH');
 return p;
}
async function exclusiveBytes(root,relativePath,bytes){
 const file=path.join(root,relativePath);
 try {
  const handle=await open(file,'wx',0o600);try{await handle.writeFile(bytes);await handle.sync();}finally{await handle.close();}
 }catch(error){
  if(error.code!=='EEXIST')throw error;
  const current=await readRegisteredFile({root,relativePath,expectedSha256:sha256(bytes),maxBytes:bytes.length});
  if(current.sizeBytes!==bytes.length)throw new Error('TRANSPORT_CONTENT_CONFLICT');
 }
}
async function exportPrivate(owner,p,command){
 privateExportRoot(owner.run.runDir,owner.inputRoot,command.requestHash);
 const requestBytes=(await readRegisteredFile({root:owner.run.runDir,relativePath:'control/owner-experiment-request.json',expectedSha256:p.envelope.requestHash,maxBytes:128*1024})).bytes;
 const assertionsBytes=(await readRegisteredFile({root:owner.runtimeRoot,relativePath:'bridge/registrations/'+p.envelope.requestHash+'/assertions.json',expectedSha256:p.snapshot.techHub.assertions_hash,maxBytes:256*1024})).bytes;
 const exported=await exportFinalizedExperiment({runDir:owner.run.runDir,requestBytes,assertionsBytes,
  actionKeys:[...p.request.initial_state,...p.request.actions].map(a=>({actionId:a.action_id,idempotencyKey:actionIdempotencyKey(p.grant,a.action_id)})),
  observationIds:command.observationIds,timelineObservationIds:command.timelineObservationIds,visualPacketHash:command.visualPacketHash});
 let root=owner.inputRoot;
 for(const segment of ['exports',command.requestHash]){root=path.join(root,segment);try{await mkdir(root);}catch(error){if(error.code!=='EEXIST')throw error;}await directory(root);}
 for(const segment of ['blobs','manifests']){const dir=path.join(root,segment);try{await mkdir(dir);}catch(error){if(error.code!=='EEXIST')throw error;}await directory(dir);}
 for(const blob of exported.blobs){hashId(blob.contentHash);if(sha256(blob.bytes)!==blob.contentHash)throw new Error('EXPORT_BLOB_INTEGRITY');await exclusiveBytes(root,'blobs/'+blob.contentHash,blob.bytes);}
 const manifestBytes=Buffer.from(stableJson(exported.manifest)),manifestHash=sha256(manifestBytes);
 await exclusiveBytes(root,'manifests/'+manifestHash+'.json',manifestBytes);
 return manifestHash;
}
async function run(owner,command){
 const fields=['schemaVersion','operation','requestHash'];
 if(['submit_action','inspect_action'].includes(command?.operation))fields.push('selectedActionId');
 else if(command?.operation==='request_capture')fields.push('captureIndex');
 else if(command?.operation==='export_result')fields.push('observationIds','timelineObservationIds','visualPacketHash');
 exactKeys(command,fields,'CONTROL_COMMAND');integer(command.schemaVersion,1,1);hashId(command.requestHash);
 if(!['inspect_owner','submit_action','request_capture','inspect_action','export_result','request_cleanup','inspect_cleanup','watch_triggers'].includes(command.operation))throw new Error('UNSUPPORTED_CONTROL_OPERATION');
 const p=await ownerScope(owner,command),base={schemaVersion:1,operation:command.operation,requestHash:command.requestHash,runtimeAttestation:'NOT_ESTABLISHED'};
 const options={runDir:owner.run.runDir,envelopeHash:owner.run.ownerEnvelopeHash};
 if(command.operation==='watch_triggers'){
  const runtime=new EvidenceRuntime({runDir:owner.run.runDir,...p.identity});await runtime.init();
  const result=await watchOwnerTriggerCaptures(runtime,options);
  return {...base,status:result.status,captureWindowIds:result.captures.map(c=>c.manifest.captureId)};
 }
 if(command.operation==='inspect_owner'){await inspectOwnerControl(options);return {...base,status:'OWNER_RECORDED',ownerEnvelopeHash:options.envelopeHash};}
 if(command.operation==='request_cleanup'){const result=await requestOwnerCleanup(options);return {...base,status:result.status};}
 if(command.operation==='inspect_cleanup'){const result=await inspectOwnerCleanup(options);return {...base,status:result.reportedStatus,recordedStatus:result.recordedStatus,evidenceHashes:result.evidenceHashes,dispatchAllowed:false};}
 if(command.operation==='submit_action'){
  const result=await submitSelectedAction({...options,selectedActionId:command.selectedActionId});
  return {...base,status:result.status,selectedActionId:command.selectedActionId};
 }
 if(command.operation==='request_capture'){
  const result=await requestDeclaredCapture({...options,captureIndex:command.captureIndex});
  return {...base,status:result.status,captureIndex:command.captureIndex};
 }
 if(command.operation==='inspect_action'){
  const result=await inspectSelectedAction({...options,selectedActionId:command.selectedActionId});
  return {...base,status:result.reportedStatus,selectedActionId:command.selectedActionId,recordedStatus:result.recordedStatus,
    evidenceHashes:result.evidenceHashes,dispatchAllowed:false};
 }
 return {...base,status:'EXPORTED',manifestHash:await exportPrivate(owner,p,command)};
}
try {
 const args=process.argv.slice(2);if(args.length!==4||args[0]!=='--owner'||args[2]!=='--request')throw new Error('FIXED_ARGUMENTS_REQUIRED');
 const result=await run(await input(args[1],65536),await input(args[3],16384));
 const output=JSON.stringify(result)+'\n';if(Buffer.byteLength(output)>65536)throw new Error('OUTPUT_LIMIT');process.stdout.write(output);
}catch{
 process.stdout.write(JSON.stringify({schemaVersion:1,status:'BLOCKED',runtimeAttestation:'NOT_ESTABLISHED',reasonCode:'INVALID_OR_UNAVAILABLE_OWNER_CONTROL'})+'\n');process.exitCode=2;
}
