import test from 'node:test';
import assert from 'node:assert/strict';
import {sha256,stableJson} from '../json.mjs';
async function api(){return import('../owner-action-adapter.mjs');}
function state(){
 const identity={debugSessionId:'session',runId:'run',runSnapshotId:'snapshot',processEpoch:1};
 const prepared={envelope:{...identity,requestHash:'a'.repeat(64)},envelopeHash:'b'.repeat(64),grant:{leaseId:'lease',arenaId:'arena',arenaEpoch:0,expectedArenaRevision:0,baselineHash:'c'.repeat(64),timeBudgetMs:30000},snapshot:{snapshotHash:'sha256:'+'d'.repeat(64)},materialDescriptor:{linkageMode:'OBSERVED_CLASS_RESOURCE_AND_CONTAINER_LINKAGE',targetModId:'example',buildArtifactHash:'e'.repeat(64),classResources:[{className:'Example',sha256:'f'.repeat(64)}]},worldRegistration:{canonicalWorldRoot:'/private/world',worldName:'KNEEKURA_DEBUG_WORLD',dimensionId:'minecraft:overworld'}};
 prepared.envelope.grantHash='1'.repeat(64);prepared.envelope.worldRegistrationHash='2'.repeat(64);
 const receipt={schemaVersion:1,kind:'owner_installation_receipt',status:'INSTALLED_SCOPED_CONTROL',...identity,runSnapshotHash:prepared.snapshot.snapshotHash,ownerEnvelopeHash:prepared.envelopeHash,grantHash:prepared.envelope.grantHash,leaseId:'lease',arenaId:'arena',arenaEpoch:0,arenaRevision:0,baselineHash:'c'.repeat(64),scope:'BOUNDED_DIAGNOSTIC_CONTROL',observedAt:'2026-10-01T00:00:00.000Z',materialLinkage:{mode:prepared.materialDescriptor.linkageMode,targetModId:'example',buildArtifactHash:'e'.repeat(64),containerIdentity:'private-container',classResources:prepared.materialDescriptor.classResources,configCertainty:'ON_DISK_NOT_LOADED',resourceCertainty:'ON_DISK_NOT_LOADED',transformedClassCertainty:'NOT_ESTABLISHED',fullTargetAttestation:'NOT_ESTABLISHED'},worldObservation:{...prepared.worldRegistration,registrationHash:prepared.envelope.worldRegistrationHash},error:null};
 receipt.receiptHash=sha256(stableJson(receipt));
 const status={schemaVersion:1,...identity,ownerEnvelopeHash:prepared.envelopeHash,installedReceiptHash:receipt.receiptHash,leaseId:'lease',arenaId:'arena',arenaEpoch:0,arenaRevision:0,idle:true,unsafe:false,nextActionId:'wait',status:'ACTIVE_SCOPED_CONTROL',observedAt:'2026-10-01T00:00:01.000Z'};
 return {prepared,receipt,status,now:Date.parse('2026-10-01T00:00:02.000Z')};
}
test('active scoped owner exposes hashes and incomplete target certainty only',async()=>{
 const {validateControlState}=await api();const f=state();const v=validateControlState(f.prepared,f.receipt,f.status,{now:f.now});
 assert.equal(v.installedReceiptHash,f.receipt.receiptHash);assert.equal(v.fullTargetAttestation,'NOT_ESTABLISHED');assert.equal(JSON.stringify(v).includes('/private/'),false);
});

test('fresh lease budget is checked independently of cached preflight and at selected publication',async t=>{
 const {validateControlState,submitSelectedAction}=await api();const f=state();f.prepared.grant.timeBudgetMs=120000;
 f.status.leaseRemainingMs=46000;
 assert.doesNotThrow(()=>validateControlState(f.prepared,f.receipt,f.status,{now:f.now,minRemainingMs:45000}));
 assert.throws(()=>validateControlState(f.prepared,f.receipt,f.status,{now:f.now+1,minRemainingMs:45000}),/LEASE_BUDGET/);
 delete f.status.leaseRemainingMs;
 assert.throws(()=>validateControlState(f.prepared,f.receipt,f.status,{now:f.now,minRemainingMs:45000}),/LEASE_BUDGET/);
 const live=await preparedOwner(t),file=path.join(live.runDir,'control/owner-status.json');
 const value=JSON.parse(await readFile(file,'utf8'));value.leaseRemainingMs=4000;value.observedAt=new Date().toISOString();
 await writeFile(file,JSON.stringify(value));
 const result=await submitSelectedAction({...live.controlOptions,selectedActionId:'wait',minRemainingMs:1000});
 const marker=JSON.parse(await readFile(path.join(live.runDir,'control/actions',sha256(result.idempotencyKey),'dispatch.json'),'utf8'));
 assert.equal(marker.minRemainingMs,1000);
});
test('receipt status must bind exact run snapshot envelope world and material',async()=>{
 const {validateControlState}=await api();
 for(const change of ['run','envelope','world','material','hash','scope']){
  const f=state();if(change==='run')f.receipt.runId='other';if(change==='envelope')f.receipt.ownerEnvelopeHash='3'.repeat(64);if(change==='world')f.receipt.worldObservation.canonicalWorldRoot='/wrong';if(change==='material')f.receipt.materialLinkage.buildArtifactHash='4'.repeat(64);if(change==='scope')f.receipt.scope='FULL_RUNTIME';
  if(change!=='hash'){delete f.receipt.receiptHash;f.receipt.receiptHash=sha256(stableJson(f.receipt));f.status.installedReceiptHash=f.receipt.receiptHash;}else f.receipt.receiptHash='0'.repeat(64);
  assert.throws(()=>validateControlState(f.prepared,f.receipt,f.status,{now:f.now}),change);
 }
});
test('stale busy unsafe expired or other revision state cannot authorize submission',async()=>{
 const {validateControlState}=await api();
 for(const change of ['stale','future','busy','unsafe','expired','epoch']){
  const f=state();if(change==='stale')f.status.observedAt='2026-09-30T23:59:00.000Z';if(change==='future')f.status.observedAt='2026-10-01T01:00:00.000Z';if(change==='busy')f.status.idle=false;if(change==='unsafe')f.status.unsafe=true;if(change==='expired')f.now+=60000;if(change==='epoch')f.status.arenaEpoch=1;
  assert.throws(()=>validateControlState(f.prepared,f.receipt,f.status,{now:f.now}),change);
 }
});

import {writeFile,readFile,readdir} from 'node:fs/promises';
import path from 'node:path';
import {preparedOwner} from './owner-action-fixture.mjs';
import {prepareOwnerControl,readPreparedOwnerControl} from '../owner-prelaunch.mjs';
test('default control clock is sampled after asynchronous owner inputs and heartbeat reads',async t=>{
 const f=await preparedOwner(t),{readInstalledControl}=await api(),sample=Date.parse(f.status.observedAt);
 f.status.leaseRemainingMs=4000;await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));
 let clock=sample-2,moved=false;t.mock.method(Date,'now',()=>clock);
 setImmediate(()=>{clock=sample+2;moved=true;});
 const result=await readInstalledControl({...f.controlOptions,minRemainingMs:100});
 assert.equal(moved,true);assert.equal(result.status.leaseRemainingMs,4000);
});
import {buildRunSnapshot,writeImmutableRunSnapshot} from '../../core.mjs';

test('selected publication creates one exact existing-journal intent and does not claim applied',async t=>{
 const {submitSelectedAction}=await api(),f=await preparedOwner(t);
 const result=await submitSelectedAction({...f.controlOptions,selectedActionId:'wait'});
 assert.equal(result.status,'REQUESTED');assert.equal(result.execution,'NOT_CONFIRMED');assert.equal(result.fullTargetAttestation,'NOT_ESTABLISHED');
 const directory=path.join(f.runDir,'control/actions',sha256(result.idempotencyKey));
 const dispatch=JSON.parse(await readFile(path.join(directory,'dispatch.json'),'utf8'));
 assert.equal(dispatch.ownerEnvelopeHash,f.prepared.envelopeHash);assert.equal(dispatch.selectedActionId,'wait');assert.equal(dispatch.handshakeNonce,f.identity.handshakeNonce);
 assert.equal(JSON.stringify(result).includes(f.identity.handshakeNonce),false);
 const again=await submitSelectedAction({...f.controlOptions,selectedActionId:'wait'});assert.equal(again.status,'ALREADY_RECORDED');
 assert.equal((await readdir(path.join(f.runDir,'control/actions'))).length,1);
});
test('foreign selected action creates no runtime intent',async t=>{
 const {submitSelectedAction}=await api(),f=await preparedOwner(t);
 await assert.rejects(submitSelectedAction({...f.controlOptions,selectedActionId:'injected'}));
 await assert.rejects(readdir(path.join(f.runDir,'control/actions')),{code:'ENOENT'});
});

test('capture requests use sealed rig and one immutable bounded slot',async t=>{
 const {requestDeclaredCapture}=await api(),f=await preparedOwner(t,{capture:true});
 const result=await requestDeclaredCapture({...f.controlOptions,captureIndex:0});
 assert.equal(result.status,'REQUESTED');assert.equal(result.execution,'NOT_CONFIRMED');
 const file=path.join(f.runDir,'control/captures',result.captureKey,'request.json');
 const marker=JSON.parse(await readFile(file,'utf8'));assert.equal(marker.captureId,'capture-'+result.captureKey);
 assert.equal(Object.hasOwn(marker,'fov'),false);assert.equal(marker.expectedArenaRevision,0);
 const again=await requestDeclaredCapture({...f.controlOptions,captureIndex:0});assert.equal(again.status,'ALREADY_RECORDED');
 await assert.rejects(requestDeclaredCapture({...f.controlOptions,captureIndex:1}));
});
test('capture requires an operator-approved declared visual rig',async t=>{
 const {requestDeclaredCapture}=await api(),f=await preparedOwner(t);
 await assert.rejects(requestDeclaredCapture({...f.controlOptions,captureIndex:0}));
 await assert.rejects(readdir(path.join(f.runDir,'control/captures')),{code:'ENOENT'});
});

test('owner action order cannot be inferred from a stale same-revision wait state',async t=>{
 const {submitSelectedAction}=await api(),f=await preparedOwner(t);
 f.status.nextActionId=null;await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));
 await assert.rejects(submitSelectedAction({...f.controlOptions,selectedActionId:'wait'}),/OWNER_ACTION_ORDER_MISMATCH/);
 await assert.rejects(readdir(path.join(f.runDir,'control/actions')),{code:'ENOENT'});
});
test('computed export destination cannot overlap sealed run even from an ancestor input root',async()=>{
 const {privateExportRoot}=await api(),hash='a'.repeat(64);
 assert.throws(()=>privateExportRoot('/private/exports/'+hash,'/private',hash),/EXPORT_MUST_STAY_OUTSIDE_SEALED_RUN/);
 assert.throws(()=>privateExportRoot('/private/exports','/private',hash),/EXPORT_MUST_STAY_OUTSIDE_SEALED_RUN/);
 assert.throws(()=>privateExportRoot('/sealed/run','/sealed/run/..transport',hash),/EXPORT_MUST_STAY_OUTSIDE_SEALED_RUN/);
 assert.throws(()=>privateExportRoot('/private/exports/'+hash+'/run','/private',hash),/EXPORT_MUST_STAY_OUTSIDE_SEALED_RUN/);
 assert.equal(privateExportRoot('/private/run','/private',hash),path.join('/private','exports',hash));
});

test('only explicit one-shot cleanup may publish while idle unsafe and cannot claim reset completion',async t=>{
 const {requestOwnerCleanup,inspectOwnerCleanup,submitSelectedAction}=await api(),f=await preparedOwner(t);
 f.status.unsafe=true;f.status.status='OUTCOME_UNKNOWN';
 await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));
 await assert.rejects(submitSelectedAction({...f.controlOptions,selectedActionId:'wait'}));
 const result=await requestOwnerCleanup(f.controlOptions);assert.equal(result.status,'REQUESTED');
 const marker=JSON.parse(await readFile(path.join(f.runDir,'control/owner-cleanup/request.json'),'utf8'));
 assert.equal(marker.cleanupKey,result.cleanupKey);assert.equal(marker.expectedArenaRevision,0);assert.equal(Object.hasOwn(marker,'args'),false);
 await assert.rejects(readdir(path.join(f.runDir,'control/actions')),{code:'ENOENT'});
 assert.equal((await requestOwnerCleanup(f.controlOptions)).status,'ALREADY_RECORDED');
 const reported=await inspectOwnerCleanup(f.controlOptions);assert.equal(reported.reportedStatus,'OUTCOME_UNKNOWN');
 assert.equal(reported.recordedStatus,null);assert.equal(reported.dispatchAllowed,false);
});
test('cleanup requires current idle ownership and absent intent is NEVER_SEEN',async t=>{
 const {requestOwnerCleanup,inspectOwnerCleanup}=await api(),f=await preparedOwner(t);
 assert.equal((await inspectOwnerCleanup(f.controlOptions)).reportedStatus,'NEVER_SEEN');
 f.status.idle=false;await writeFile(path.join(f.runDir,'control/owner-status.json'),JSON.stringify(f.status));
 await assert.rejects(requestOwnerCleanup(f.controlOptions));
 await assert.rejects(readdir(path.join(f.runDir,'control/owner-cleanup')),{code:'ENOENT'});
});
