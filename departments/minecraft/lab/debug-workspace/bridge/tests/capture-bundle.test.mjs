import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from '../../evidence/tests/visual-fixture.mjs';
import {preparedOwner} from './owner-action-fixture.mjs';
import {requestDeclaredCapture} from '../owner-action-adapter.mjs';
import {readFile,writeFile,cp,mkdir} from 'node:fs/promises';
import path from 'node:path';
import {EvidenceRuntime} from '../../evidence/runtime.mjs';
import {sha256,stableJson} from '../json.mjs';
const bundles=await import('../capture-bundle.mjs').catch(e=>{if(e.code==='ERR_MODULE_NOT_FOUND')return {};throw e;});

test('successful owner-bound bundle accepts native signed UUID order while preserving raw producer order',async t=>{
 const seed=await preparedOwner(t,{capture:true}),request=JSON.parse(seed.requestBytes);
 request.subjects.push({subject_id:'pig2',uuid:'80000000-0000-0000-0000-000000000001',entity_type:'minecraft:pig'});
 const f=await preparedOwner(t,{requestBytesOverride:Buffer.from(JSON.stringify(request))});
 const intent=await requestDeclaredCapture({...f.controlOptions,captureIndex:0}),p=f.prepared;
 const identity=Object.fromEntries(['debugSessionId','runId','runSnapshotId','processEpoch','experimentId','generation','requestHash','arenaId','arenaEpoch','baselineHash'].map(k=>[k,p.grant[k]]));identity.arenaRevision=0;
 const order=request.subjects.map(s=>s.uuid).reverse();
 const v=await fixture(t,{request,run:'r',mutate:m=>{
  m.identity=identity;m.captureId='capture-'+intent.captureKey;m.subjects=order;
  m.structuredState.arenaBounds=request.arena.bounds;
  m.structuredState.subjects.push({...m.structuredState.subjects[0],uuid:order[0]});
  m.structuredState.subjects.reverse();
  for(const frame of m.frames){frame.identity=identity;frame.captureId=m.captureId;frame.subjects=order;frame.camera.fov=60;}
 }});
 const runtime=new EvidenceRuntime({runDir:f.runDir,...p.identity});await runtime.init();
 await runtime.store.appendObservation((await v.store.readObservations())[0]);
 await mkdir(path.join(f.runDir,'evidence/raw/visual'),{recursive:true});await cp(path.join(v.runDir,'evidence/raw/visual'),path.join(f.runDir,'evidence/raw/visual'),{recursive:true});
 const base={schemaVersion:1,debugSessionId:identity.debugSessionId,runId:identity.runId,runSnapshotId:identity.runSnapshotId,processEpoch:1,
  ownerEnvelopeHash:p.envelopeHash,requestHash:p.grant.requestHash,runSnapshotHash:p.snapshot.snapshotHash,leaseId:p.grant.leaseId,arenaId:p.grant.arenaId,arenaEpoch:0,arenaRevision:0};
 const dir=path.join(f.runDir,'control/captures',intent.captureKey);
 await writeFile(path.join(dir,'native-reservation.json'),stableJson(base));
 await writeFile(path.join(dir,'receipt.json'),stableJson({...base,kind:'owner_capture_receipt',captureKey:intent.captureKey,captureIndex:0,captureId:v.manifest.captureId,status:'COMPLETE',manifestPayloadHash:sha256(stableJson(v.manifest)),manifest:v.manifest}));
 const result=await bundles.captureBundle({...f.controlOptions,captureIndex:0});
 assert.equal(result.status,'COMPLETE');assert.equal(result.bundle.sourceBinding,'CANONICAL_OWNER_CAPTURE');
 assert.deepEqual(result.bundle.identity,identity);assert.deepEqual(v.manifest.subjects,order);
});
test('original capture slot inspection stays unknown without completion and never resubmits',async t=>{
 assert.equal(typeof bundles.captureBundle,'function');const f=await preparedOwner(t,{capture:true});
 const intent=await requestDeclaredCapture({...f.controlOptions,captureIndex:0}),file=path.join(f.runDir,'control/captures',intent.captureKey,'request.json'),before=await readFile(file);
 const result=await bundles.captureBundle({...f.controlOptions,captureIndex:0});assert.equal(result.status,'UNKNOWN');assert.equal(result.execution,'NOT_CONFIRMED');
 assert.deepEqual(await readFile(file),before);
});
test('bundle reader verifies four raw images, keeps their order and exposes integrity failure',async t=>{
 assert.equal(typeof bundles.bundleFromManifest,'function');const f=await fixture(t);
 const b=await bundles.bundleFromManifest({runDir:f.runDir,manifest:f.manifest});assert.equal(b.status,'COMPLETE');assert.equal(b.artifactRole,'REFERENCES_TO_RAW_AND_STRUCTURED_EVIDENCE');
 assert.deepEqual(b.views.map(v=>v.view),['north','east','south','west']);assert.equal(b.restoration,'RESTORED');
 const file=path.join(f.runDir,f.manifest.frames[0].imagePath);await writeFile(file,'corrupted fixture bytes');
 const broken=await bundles.bundleFromManifest({runDir:f.runDir,manifest:f.manifest});assert.equal(broken.status,'UNKNOWN');assert.equal(broken.views[0].verification,'UNKNOWN_INTEGRITY');
});
