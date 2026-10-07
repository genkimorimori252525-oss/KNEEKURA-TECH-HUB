/** Read-only acceptance audit of an already finalized finite pilot, including late evidence. */
import assert from 'node:assert/strict';
import {readFile,readdir} from 'node:fs/promises';
import path from 'node:path';
import {readMobPovImage} from '../mob-pov.mjs';
import {readPreparedOwnerControl} from '../owner-prelaunch.mjs';
import {sha256} from '../json.mjs';
import {readRegisteredFile} from '../materials.mjs';

const reportFile=process.argv[2];assert(reportFile&&path.isAbsolute(reportFile),'Absolute immutable pilot report required');
const reportBytes=await readFile(reportFile),report=JSON.parse(reportBytes),runDir=report.runDir;
assert(path.isAbsolute(runDir));
const envelopeHash=sha256((await readRegisteredFile({root:runDir,relativePath:'control/owner-envelope.json',maxBytes:16384})).bytes);
const prepared=await readPreparedOwnerControl({runDir,envelopeHash,requireSnapshot:true});
const finalBytes=(await readRegisteredFile({root:runDir,relativePath:'evidence/finalization.json',maxBytes:2*1024*1024})).bytes,final=JSON.parse(finalBytes);
assert.equal(final.status,'EVIDENCE_COMPLETE');assert.equal(final.shutdown.clean,true);
for(const key of ['debugSessionId','runId','runSnapshotId','processEpoch'])assert.equal(final[key],prepared.envelope[key]);
assert.equal(final.runSnapshotHash,prepared.snapshot.snapshotHash);
const artifact=relative=>{const file=path.join(runDir,relative),row=final.artifacts.find(a=>a.path===file);assert(row,'Sealed artifact missing: '+relative);return row;};
async function sealed(relative,maxBytes){const a=artifact(relative),file=await readRegisteredFile({root:runDir,relativePath:relative,expectedSha256:a.sha256.replace(/^sha256:/,''),maxBytes});assert.equal(file.sizeBytes,a.size);return file.bytes;}
const observations=JSON.parse('['+(await sealed('evidence/observations.jsonl',16*1024*1024)).toString('utf8').trim().split('\n').join(',')+']');
const receipts=[];for(let i=0;i<4;i++)receipts.push(JSON.parse(await sealed('control/mob-pov/'+String(i).padStart(2,'0')+'/receipt.json',16384)));
assert.deepEqual(receipts.map(r=>r.status),['ATTACHED','CAPTURED','RETURNED','ATTACHED']);assert.equal(receipts[2].restoration,'RESTORED');
assert.equal(report.viewOnly.imageCount,0);assert(report.viewOnly.serverTickAfter>report.viewOnly.serverTickBefore);assert(report.viewOnly.gameTimeAfter>report.viewOnly.gameTimeBefore);
for(const tick of [report.viewOnly.serverTickBefore,report.viewOnly.serverTickAfter])assert(observations.some(r=>r.lane==='SERVER_TICK'&&r.payload?.localServerTick===tick));
const raw=receipts[1].result;
assert.equal(raw.subjectUuid,prepared.request.subjects[0].uuid);assert.equal(raw.entityType,prepared.request.subjects[0].entity_type);
assert.deepEqual(raw.camera.viewport,[640,480]);assert(Math.abs(raw.camera.fov-60)<.001);assert.equal(raw.aiPerceptionVerdict,'NOT_ESTABLISHED');
assert.equal(raw.timePairing,'INDEPENDENT_ASYNC_SERVER_SAMPLE_NOT_SAME_TICK');assert.equal(raw.artifactRole,'RAW_SCENE_RGB');
assert(observations.some(r=>r.payload?.kind==='mob_pov_raw_frame'&&r.payload.imageHash===raw.imageHash));
for(const reason of ['EXPLICIT_RETURN','EXPIRED'])assert(observations.some(r=>r.payload?.kind==='mob_pov_return'&&r.payload.reason===reason&&r.payload.restoration==='RESTORED'));
assert.equal((await readdir(path.join(runDir,'evidence/raw/visual'))).filter(s=>s.endsWith('.png')).length,1);
const image=await readMobPovImage({runDir,envelopeHash,commandIndex:1});assert.deepEqual(image,await sealed(raw.imagePath,4*1024*1024));
const ack=JSON.parse((await readRegisteredFile({root:runDir,relativePath:'control/shutdown-ack.json',maxBytes:65536})).bytes);
assert.equal(ack.status,'CLEAN_EVIDENCE_SHUTDOWN');assert.equal(ack.writerDroppedTotal,0);
assert.equal(report.originalWorld.status,'UNCHANGED');assert.equal(report.originalWorld.files,85);
console.log(JSON.stringify({schema:'kneekura.mob-pov-sealed-audit/v1',status:'PASS',originalPilotStatus:report.status,pilotReportHash:sha256(reportBytes),finalizationHash:sha256(finalBytes),
 labRevision:report.labRevision,hostRevision:report.hostRevision,runDir,imagePath:path.join(runDir,raw.imagePath),imageHash:raw.imageHash,imageBytes:image.length,
 viewOnly:report.viewOnly,explicitReturn:'RESTORED',expiryReturn:'RESTORED',finalization:final.status,originalWorld:report.originalWorld,
 limitations:report.limitations}));
