import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import path from 'node:path';
import { fixture as visualFixture, request } from '../../evidence/tests/visual-fixture.mjs';
import { compileVisualPacket, persistVisualPacket } from '../../evidence/visual-compiler.mjs';
import { derivedArtifact } from '../../evidence/visual-artifacts.mjs';
import { validatePacket } from '../../evidence/visual-packet.mjs';
import { finalizeEvidenceRun } from '../../evidence/finalize.mjs';
import { beginAction, recordActionOutcome } from '../action-journal.mjs';
import { sha256, stableJson } from '../json.mjs';
import * as exporter from '../result-export.mjs';
import { fixture } from './result-export-fixture.mjs';
test('exports exact private snapshot and selected source bytes without public paths or false PASS',async t=>{
 const f=await fixture(t);const canonicalBefore=await readFile(f.store.evidenceFile);const out=await exporter.exportFinalizedExperiment(f);
 assert.equal(out.result.execution.status,'COMPLETED');assert.equal(out.result.execution.cleanup,'UNKNOWN');
 assert.equal(out.result.execution.action_receipts[0].status,'APPLIED');assert.ok(out.result.assertions.every(a=>a.status==='INCONCLUSIVE'));
 assert.ok(out.result.gaps.some(g=>g.code==='UNKNOWN'));assert.equal(out.result.gaps.some(g=>g.code==='PARTIAL'),false);
 const snapshot=out.blobs.find(b=>b.contentHash===out.result.run_snapshot_content_hash);
 assert.deepEqual(snapshot.bytes,f.snapshotBytes);assert.equal(snapshot.classification,'PRIVATE_RUN_SNAPSHOT');
 for(const b of out.blobs)assert.equal(sha256(b.bytes),b.contentHash);
 assert.equal(out.manifest.contains_private_evidence,true);assert.equal(out.manifest.runtime_attestation,'NOT_ESTABLISHED');
 assert.doesNotMatch(JSON.stringify(out.manifest)+JSON.stringify(out.result),/\/private|process\.log|runDir/);
 assert.equal(out.blobs.some(b=>b.bytes.includes('DO NOT EXPORT')),false);
 assert.deepEqual(await readFile(f.store.evidenceFile),canonicalBefore);
 assert.equal(sha256(out.resultBytes),out.manifest.result_hash);
});
for(const state of ['MISSING','ACCEPTED','NO_EFFECT','CORRUPT'])test(`unproven action stays UNKNOWN: ${state}`,async t=>{
 const f=await fixture(t,{journal:state==='MISSING'?'MISSING':state==='ACCEPTED'?'ACCEPTED':'VERIFIED',effect:state!=='NO_EFFECT'});
 if(state==='CORRUPT')await writeFile(path.join(f.journalDir,'receipt-000003.json'),'{}');
 const out=await exporter.exportFinalizedExperiment(f);assert.equal(out.result.execution.action_receipts[0].status,'UNKNOWN');
 assert.notEqual(out.result.execution.status,'COMPLETED');assert.equal(out.result.execution.cleanup,'UNKNOWN');
});
test('explicit pre-dispatch NOT_RUN and rejection preserve exact recorded status',async t=>{
 for(const state of ['NOT_RUN','REJECTED']){const f=await fixture(t,{journal:state,effect:false});const out=await exporter.exportFinalizedExperiment(f);
 assert.equal(out.result.execution.action_receipts[0].status,state);assert.equal(out.result.execution.status,state==='NOT_RUN'?'NOT_RUN':'FAILED');}
});
test('finalization partial state and selected private data stay explicit gaps',async t=>{
 const f=await fixture(t,{partial:true});const out=await exporter.exportFinalizedExperiment(f);assert.ok(out.result.gaps.some(g=>g.code==='PARTIAL'));
 const cleanup=out.blobs.find(b=>b.contentHash===out.result.evidence.find(e=>e.kind==='cleanup_receipt').content_hash);
 assert.match(cleanup.bytes.toString(),/EVIDENCE_SEAL_NOT_ARENA_CLEANUP/);assert.doesNotMatch(cleanup.bytes.toString(),/\/private|process\.log/);
});
test('packet export binds raw RGB and derived bytes to the sealed canonical capture',async t=>{
 const f=await fixture(t,{visual:true});const out=await exporter.exportFinalizedExperiment(f);
 assert.equal(out.result.observations.visual_bundle,f.visualPacketHash);
 assert.equal(out.result.evidence.filter(e=>e.kind==='raw_scene').length,4);
 assert.ok(out.result.gaps.some(g=>g.code==='PERTURBED'));assert.ok(out.result.assertions.every(a=>a.status==='INCONCLUSIVE'));
});

test('finalized visual export rejects a self-consistently rehashed packet added after sealing',async t=>{
 const f=await fixture(t,{visual:true});
 const before=await readFile(f.final.file);
 const packet=JSON.parse(await readFile(path.join(f.runDir,`evidence/derived/visual/${f.visualPacketHash}.json`)));
 const ref=packet.topDown;
 const forged=derivedArtifact(Buffer.from('<svg xmlns="http://www.w3.org/2000/svg">unrelated image</svg>'),{
  role:ref.role,mediaType:ref.mediaType,extension:'svg',sourceObservationIds:ref.sourceObservationIds,
  rawSourceHashes:ref.rawSourceHashes,binding:ref.binding,details:ref.details});
 packet.topDown=forged.ref;packet.drilldown[0].artifacts[1]=forged.ref.artifactId;
 const {packetId,...body}=packet;packet.packetId=sha256(stableJson(body));
 assert.doesNotThrow(()=>validatePacket(packet));
 const bytes=Buffer.from(stableJson(packet)),hash=sha256(bytes);
 await writeFile(path.join(f.runDir,forged.ref.path),forged.bytes);
 await writeFile(path.join(f.runDir,`evidence/derived/visual/${hash}.json`),bytes);
 await assert.rejects(exporter.exportFinalizedExperiment({...f,visualPacketHash:hash}),/FINALIZED_ARTIFACT_MISSING/);
 assert.deepEqual(await readFile(f.final.file),before);
 assert.equal((await exporter.exportFinalizedExperiment(f)).result.observations.visual_bundle,f.visualPacketHash);
});

test('legacy finalization without derived inventory cannot certify a visual bundle',async t=>{
 const f=await fixture(t,{visual:true});
 const seal=JSON.parse(await readFile(f.final.file));
 seal.artifacts=seal.artifacts.filter(ref=>!ref.path.includes(path.join('evidence','derived','visual')));
 await writeFile(f.final.file,JSON.stringify(seal));
 await assert.rejects(exporter.exportFinalizedExperiment(f),/FINALIZED_ARTIFACT_MISSING/);
 assert.equal((await exporter.exportFinalizedExperiment({...f,visualPacketHash:null})).result.observations.visual_bundle,null);
});
test('missing finalization, stale snapshot, tampered canonical evidence and foreign action linkage reject',async t=>{
 for(const fault of ['unsealed','snapshot','canonical','action']){
  const f=await fixture(t);
  if(fault==='unsealed')await rm(f.final.file);
  if(fault==='snapshot')await writeFile(path.join(f.runDir,'run-snapshot.json'),Buffer.concat([f.snapshotBytes,Buffer.from(' ')]));
  if(fault==='canonical')await writeFile(f.store.evidenceFile,Buffer.from('[]\n'));
  if(fault==='action')f.actionKeys=[{actionId:'foreign',idempotencyKey:'key-1'}];
  await assert.rejects(exporter.exportFinalizedExperiment(f));
 }
});
test('same registration evidence hash uses exact supplied assertion bytes',async t=>{
 const f=await fixture(t);await assert.rejects(exporter.exportFinalizedExperiment({...f,assertionsBytes:Buffer.from('[]')}),/ASSERTION/);
});

test('actual producer sparse completeness normalizes through canonical ingestion without rewriting exported bytes',async t=>{
 const f=await fixture(t,{sparseProducer:true});const out=await exporter.exportFinalizedExperiment(f);
 assert.equal(out.result.execution.action_receipts[0].status,'APPLIED');
 assert.ok(out.blobs.some(b=>b.bytes.equals(f.effectBytes)));
});
test('visual bundle includes its exact sealed canonical source even without explicit row selection',async t=>{
 const f=await fixture(t,{visual:true});const out=await exporter.exportFinalizedExperiment({...f,observationIds:[]});
 const canonical=(await f.store.readObservations()).find(r=>r.observationId===f.sourceObservationId);
 assert.ok(out.blobs.some(b=>{try{return JSON.parse(b.bytes).observationId===canonical.observationId;}catch{return false;}}));
});
test('optional selected private fields are omitted with explicit source-hash lineage and UNAVAILABLE',async t=>{
 const f=await fixture(t,{privateRow:true});const out=await exporter.exportFinalizedExperiment(f);
 assert.ok(out.result.gaps.some(g=>g.code==='UNAVAILABLE'));
 assert.equal(out.blobs.some(b=>b.bytes.includes('selected-row-secret')),false);
 const summary=JSON.parse(out.blobs.find(b=>b.contentHash===out.result.observations.structured_summary).bytes);
 const row=summary.observations.find(r=>r.observationId==='obs:private:1');assert.equal(row.status,'PRIVATE_FIELDS_NOT_EXPORTED');assert.match(row.sourceContentHash,/^[a-f0-9]{64}$/);
});
test('export rejects changed retained visual pixels and out-of-budget row selections',async t=>{
 const f=await fixture(t,{visual:true});await writeFile(path.join(f.runDir,f.manifest.frames[0].imagePath),'changed');
 await assert.rejects(exporter.exportFinalizedExperiment(f),/HASH|PNG/);
 await assert.rejects(exporter.exportFinalizedExperiment({...f,observationIds:Array.from({length:33},(_,i)=>'obs:'+i)}),/LIMIT/);
});
for(const fault of ['side','revision','elapsed'])test(`effect evidence must match the server action post-state: ${fault}`,async t=>{
 const f=await fixture(t,{effectSide:fault==='side'?'CLIENT':'SERVER',effectOverride:fault==='revision'?{afterRevision:99}:fault==='elapsed'?{elapsedServerTicks:1}:{}});
 const out=await exporter.exportFinalizedExperiment(f);assert.equal(out.result.execution.action_receipts[0].status,'UNKNOWN');
});
test('explicitly sealed trailing producer loss preserves earlier exact action evidence and PARTIAL gap',async t=>{
 const f=await fixture(t,{trailingPartial:true,sparseProducer:true});assert.equal(f.final.manifest.status,'EVIDENCE_PARTIAL');
 assert.ok(f.final.manifest.counts.trailingPartialFiles>0);
 const out=await exporter.exportFinalizedExperiment(f);assert.equal(out.result.execution.action_receipts[0].status,'APPLIED');
 assert.ok(out.result.gaps.some(g=>g.code==='PARTIAL'));assert.equal(out.result.execution.cleanup,'UNKNOWN');
 const forged=JSON.parse(await readFile(f.final.file));forged.status='EVIDENCE_COMPLETE';forged.counts.trailingPartialFiles=0;
 await writeFile(f.final.file,JSON.stringify(forged));await assert.rejects(exporter.exportFinalizedExperiment(f));
});

test('production snapshot integer-like metadata keys retain original canonical hash and raw export bytes',async t=>{
 const f=await fixture(t,{numericSnapshotKeys:true}),out=await exporter.exportFinalizedExperiment(f);
 assert.deepEqual(out.blobs.find(b=>b.contentHash===out.result.run_snapshot_content_hash).bytes,f.snapshotBytes);
 assert.equal(out.manifest.runtime_attestation,'NOT_ESTABLISHED');
});

test('native owner effect rows use hash-only registration references to preserve exportable action facts',async t=>{
 const f=await fixture(t,{effectOverride:{ownerEnvelopeHash:'1'.repeat(64),ownerInstallationReceiptHash:'2'.repeat(64),
   materialDescriptorHash:'3'.repeat(64),worldRegistrationHash:'4'.repeat(64),fullTargetAttestation:'NOT_ESTABLISHED'}});
 const out=await exporter.exportFinalizedExperiment(f);assert.equal(out.result.execution.action_receipts[0].status,'APPLIED');
 assert.ok(out.blobs.some(b=>b.bytes.equals(f.effectBytes)));assert.equal(out.manifest.runtime_attestation,'NOT_ESTABLISHED');
 const privateSource=await fixture(t,{effectOverride:{worldObservation:{canonicalWorldRoot:'/private/operator/world'}}});
 const omitted=await exporter.exportFinalizedExperiment(privateSource);assert.equal(omitted.result.execution.action_receipts[0].status,'UNKNOWN');
 assert.ok(omitted.result.gaps.some(g=>g.code==='UNAVAILABLE'));
});
