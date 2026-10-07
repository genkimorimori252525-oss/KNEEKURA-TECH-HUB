import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {readFile,readdir,writeFile,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {request} from '../../evidence/tests/visual-fixture.mjs';
import {validateVisualExperimentRequest} from '../../evidence/visual-request-contract.mjs';
import {ownerPrelaunchFixture} from './owner-prelaunch-fixtures.mjs';
import {prepareOwnerControl,readPreparedOwnerControl} from '../owner-prelaunch.mjs';
import {preparedOwner} from './owner-action-fixture.mjs';
import {sha256} from '../json.mjs';
import {encodePngRgba} from '../../../simlab/golden/png.mjs';

const url=new URL('../mob-pov.mjs',import.meta.url),api=existsSync(url)?await import(url):{};
function req(captures=0){const r=request();r.visual_rig.mode='mob-eye-live-v1';r.budgets.max_captures=captures;return r;}
test('mob POV accepts zero image budget and explicit single-image budget without cardinal assertions',()=>{
 for(const captures of [0,1,16])assert.deepEqual(validateVisualExperimentRequest(req(captures)),req(captures));
 const bad=req();bad.assertions=[{assertion_id:'visual',kind:'visual',subject_id:'subject',check:'subject_visible',expected:'YES'}];
 assert.throws(()=>validateVisualExperimentRequest(bad));
});
test('mob POV does not relax viewport, capture bounds or cardinal minimum',()=>{
 for(const mutate of [r=>r.visual_rig.viewport=[63,64],r=>r.visual_rig.fov=Infinity,r=>r.budgets.max_captures=17]){
  const r=req();mutate(r);assert.throws(()=>validateVisualExperimentRequest(r));
 }
 const cardinal=request();cardinal.budgets.max_captures=1;assert.throws(()=>validateVisualExperimentRequest(cardinal));
});
test('POV requires its own permission even with no snapshots; cardinal permission cannot substitute',async t=>{
 const f=await ownerPrelaunchFixture(t,null,undefined,r=>{r.visual_rig={mode:'mob-eye-live-v1',fov:60,viewport:[64,64]};});
 await assert.rejects(prepareOwnerControl(f.options),/PERMISSION/);
 assert.deepEqual(await readdir(f.runDir),[]);
 f.operator.worldRegistration.permissions.push('CARDINAL_CAPTURE_PAUSE_CAMERA');f.options.operatorRegistration=await f.select();
 await assert.rejects(prepareOwnerControl(f.options),/PERMISSION/);
 f.operator.worldRegistration.permissions=['BOUNDED_DIAGNOSTIC_CONTROL','MOB_POV_CAMERA'];f.options.operatorRegistration=await f.select();
 const p=await prepareOwnerControl(f.options),loaded=await readPreparedOwnerControl({runDir:f.runDir,envelopeHash:p.envelopeHash});
 assert.equal(loaded.request.visual_rig.mode,'mob-eye-live-v1');assert.equal(loaded.grant.maxCaptures,0);
});
test('command validation refuses foreign subjects, undeclared mode, injection and invalid duration/index',()=>{
 assert.equal(typeof api.validateMobPovCommand,'function','mob POV command validator must exist');
 const prepared={request:req(),grant:{subjects:[{uuid:req().subjects[0].uuid}]}},command={commandIndex:0,operation:'attach',subjectUuid:req().subjects[0].uuid,durationMs:1000};
 assert.doesNotThrow(()=>api.validateMobPovCommand(command,prepared));
 for(const delta of [{subjectUuid:'ffffffff-ffff-ffff-ffff-ffffffffffff'},{durationMs:0},{durationMs:120001},{durationMs:true},{commandIndex:32},{commandIndex:-1},{executable:'cmd.exe'},{operation:'set_target'}]){
  assert.throws(()=>api.validateMobPovCommand({...command,...delta},prepared));
 }
 assert.throws(()=>api.validateMobPovCommand(command,{...prepared,request:request()}));
 assert.throws(()=>api.validateMobPovCommand({commandIndex:1,operation:'snapshot',subjectUuid:command.subjectUuid},prepared));
});
async function live(t,capture=false){
 const f=await preparedOwner(t,{mobPov:true,capture});f.status.leaseRemainingMs=4000;
 await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));return f;
}
test('explicit attach publishes one intent and no images; duplicate cannot create a second effect',async t=>{
 const f=await live(t),command={...f.controlOptions,commandIndex:0,operation:'attach',subjectUuid:f.prepared.grant.subjects[0].uuid,durationMs:1000};
 const published=await api.publishMobPovCommand(command);assert.equal(published.status,'REQUESTED');assert.equal(published.execution,'NOT_CONFIRMED');
 const marker=JSON.parse(await readFile(path.join(f.runDir,'control/mob-pov/00/request.json'),'utf8'));
 assert.equal(marker.subjectUuid,command.subjectUuid);assert.equal(marker.ownerEnvelopeHash,f.prepared.envelopeHash);
 assert.deepEqual(await readdir(path.join(f.runDir,'control/mob-pov/00')),['request.json']);
 await assert.rejects(readdir(path.join(f.runDir,'evidence/raw/visual')),{code:'ENOENT'});
 assert.equal((await api.publishMobPovCommand(command)).status,'ALREADY_REQUESTED');
 await assert.rejects(api.publishMobPovCommand({...command,durationMs:2000}),/REPLAY/);
 await assert.rejects(api.publishMobPovCommand({...f.controlOptions,commandIndex:1,operation:'return'}));
});
test('zero image budget and stale owner cannot publish capture intent',async t=>{
 const f=await live(t);
 await assert.rejects(api.publishMobPovCommand({...f.controlOptions,commandIndex:0,operation:'snapshot'}),/VIEW_ONLY/);
 f.status.observedAt='2000-01-01T00:00:00.000Z';await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));
 await assert.rejects(api.publishMobPovCommand({...f.controlOptions,commandIndex:0,operation:'attach',subjectUuid:f.prepared.grant.subjects[0].uuid,durationMs:1000}),/CURRENT/);
 await assert.rejects(readdir(path.join(f.runDir,'control/mob-pov')),{code:'ENOENT'});
});
test('previous receipt must belong to the exact owner, request and operation before next intent',async t=>{
 const f=await live(t);const command={...f.controlOptions,commandIndex:0,operation:'attach',subjectUuid:f.prepared.grant.subjects[0].uuid,durationMs:1000};
 await api.publishMobPovCommand(command);
 const receipt={schemaVersion:1,kind:'mob_pov_operation_receipt',ownerEnvelopeHash:f.prepared.envelopeHash,runSnapshotHash:f.prepared.snapshot.snapshotHash,
  requestHash:f.prepared.envelope.requestHash,commandIndex:0,operation:'attach',observedAt:new Date().toISOString(),status:'ATTACHED',result:{status:'ATTACHED'}};
 const file=path.join(f.runDir,'control/mob-pov/00/receipt.json');
 for(const delta of [{ownerEnvelopeHash:'f'.repeat(64)},{requestHash:'f'.repeat(64)},{commandIndex:1},{operation:'return'},{kind:'arbitrary'},{status:'RUNNING'}]){
  await writeFile(file,JSON.stringify({...receipt,...delta}));
  await assert.rejects(api.publishMobPovCommand({...f.controlOptions,commandIndex:1,operation:'return'}),/RECEIPT/);
 }
 await writeFile(file,JSON.stringify(receipt));assert.equal((await api.publishMobPovCommand({...f.controlOptions,commandIndex:1,operation:'return'})).status,'REQUESTED');
});
function rawFrame(f,png){
 const g=f.prepared.grant,id=Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch','experimentId'].map(k=>[k,g[k]]));
 const identity={...id,generation:g.generation,requestHash:g.requestHash,arenaId:g.arenaId,arenaEpoch:g.arenaEpoch,arenaRevision:0,baselineHash:g.baselineHash};
 delete identity.worldName;delete identity.dimension;
 const subject=f.prepared.request.subjects[0],matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
 const imageHash=sha256(png);
 return {schemaVersion:1,kind:'mob_pov_raw_frame',rig:'mob-eye-live-v1',identity,subjectUuid:subject.uuid,entityType:subject.entity_type,dimension:'minecraft:overworld',clientTick:2,renderFrame:3,
  captureId:'mob-pov-0',imageHash,imageBytes:png.length,imagePath:`evidence/raw/visual/${imageHash}.png`,captureStage:'AFTER_LEVEL_BEFORE_POST_EFFECT_HAND_HUD',artifactRole:'RAW_SCENE_RGB',
  partialTick:0.5,clientGameTime:4,serverReference:{identity,serverTick:5,serverGameTime:6,subjectUuid:subject.uuid,validatedAtNanos:1,reservationToken:'capture-token',position:[1,2,3]},
  timePairing:'INDEPENDENT_ASYNC_SERVER_SAMPLE_NOT_SAME_TICK',aiPerceptionVerdict:'NOT_ESTABLISHED',cameraEffect:'NONE',
  camera:{position:[1,2,3],quaternion:[0,0,0,1],yaw:0,pitch:0,fov:60,projectionMatrix:matrix,viewMatrix:matrix,viewport:[64,64],matrixConvention:'JOML_COLUMN_MAJOR_CAMERA_RELATIVE'}};
}
test('mob raw retrieval binds exact subject/identity and validates complete PNG; RGB does not prove AI perception',async t=>{
 const f=await live(t,true),png=encodePngRgba({width:64,height:64,rgba:Buffer.alloc(64*64*4)}),frame=rawFrame(f,png);
 assert.equal(typeof api.readMobPovImage,'function');
 await api.publishMobPovCommand({...f.controlOptions,commandIndex:0,operation:'snapshot'});
 const receipt={schemaVersion:1,kind:'mob_pov_operation_receipt',ownerEnvelopeHash:f.prepared.envelopeHash,runSnapshotHash:f.prepared.snapshot.snapshotHash,requestHash:f.prepared.envelope.requestHash,
  commandIndex:0,operation:'snapshot',observedAt:new Date().toISOString(),status:'CAPTURED',observationPayloadHash:'a'.repeat(64)};
 async function put(raw){await writeFile(path.join(f.runDir,'control/mob-pov/00/receipt.json'),JSON.stringify({...receipt,imageHash:raw.imageHash,imageBytes:raw.imageBytes,imagePath:raw.imagePath,result:{...raw,status:'CAPTURED',observationPayloadHash:receipt.observationPayloadHash}}));}
 await mkdir(path.join(f.runDir,'evidence/raw/visual'),{recursive:true});await writeFile(path.join(f.runDir,frame.imagePath),png);
 await put(frame);assert.deepEqual(await api.readMobPovImage({...f.controlOptions,commandIndex:0}),png);
 assert.equal(typeof api.sealMobPovArtifacts,'function');
 await assert.rejects(api.sealMobPovArtifacts(f.runDir,[],[]),/SOURCE/);
 const source={payload:frame,debugSessionId:frame.identity.debugSessionId,runId:frame.identity.runId,runSnapshotId:frame.identity.runSnapshotId,processEpoch:frame.identity.processEpoch,
  arenaEpoch:frame.identity.arenaEpoch,scope:{kind:'EXPERIMENT',experimentId:frame.identity.experimentId},epistemicStatus:'OBSERVED',completeness:{complete:true}};
 const artifacts=[];await api.sealMobPovArtifacts(f.runDir,[source],artifacts);assert.equal(artifacts.filter(a=>a.path.endsWith('.png')).length,1);
 for(const change of [r=>r.identity.requestHash='f'.repeat(64),r=>r.subjectUuid='ffffffff-ffff-ffff-ffff-ffffffffffff',r=>r.camera.viewport=[65,64],r=>r.timePairing='SAME_TICK',r=>r.aiPerceptionVerdict='VERIFIED',r=>r.camera.projectionMatrix[0]=Infinity]){
  const bad=structuredClone(frame);change(bad);await put(bad);await assert.rejects(api.readMobPovImage({...f.controlOptions,commandIndex:0}));
 }
 const extra=Buffer.concat([png,Buffer.from('extra')]),bad={...frame,imageHash:sha256(extra),imageBytes:extra.length,imagePath:`evidence/raw/visual/${sha256(extra)}.png`};
 await put(bad);await writeFile(path.join(f.runDir,bad.imagePath),extra);await assert.rejects(api.readMobPovImage({...f.controlOptions,commandIndex:0}));
});
