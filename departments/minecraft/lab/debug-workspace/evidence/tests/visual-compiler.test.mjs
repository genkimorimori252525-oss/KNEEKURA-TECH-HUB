import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, symlink, mkdir } from 'node:fs/promises';
import path from 'node:path';
import { decodePng } from '../../../simlab/golden/png.mjs';
import { sha256 } from '../../bridge/json.mjs';
import { fixture, UUID } from './visual-fixture.mjs';
import * as compiler from '../visual-compiler.mjs';
const artifact = (c, ref) => c.artifacts.find(a => a.ref.artifactId === ref.artifactId);
test('compiler produces actual ordered 2x2 RGB pixels with immutable raw lineage and exact topdown facts', async t => {
  const f = await fixture(t); const before = await f.store.readObservations();
  const c = await compiler.compileVisualPacket(f);
  const sheet = decodePng(artifact(c,c.packet.contactSheet).bytes);
  assert.deepEqual([sheet.width,sheet.height], [128,164]);
  for (let i=0;i<4;i++) {
    const x=(i%2)*64+20, y=Math.floor(i/2)*82+40;
    assert.deepEqual([...sheet.rgba.slice((y*128+x)*4,(y*128+x)*4+4)], f.colors[i]);
  }
  assert.deepEqual(c.packet.labels, [{ label:'A',uuid:UUID,uuidSuffix:'000001' }]);
  assert.deepEqual(c.packet.structuredSummary.subjects[0].position,[1,1,2]);
  const top = artifact(c,c.packet.topDown).bytes.toString();
  assert.match(top,/data-world-x="1" data-world-z="2"/);
  assert.match(top,/A.*000001/s);
  assert.equal(c.packet.sameFrame,false);
  assert.equal(c.packet.benchmark.status,'DEFERRED_REAL_TASK_REQUIRED');
  for(const a of c.artifacts) { assert.equal(sha256(a.bytes),a.ref.sha256); assert.equal(a.ref.derived,true); assert.deepEqual(a.ref.sourceObservationIds,[f.sourceObservationId]); }
  assert.deepEqual(c.packet.rawViews.map(v=>v.artifactRole),Array(4).fill('RAW_SCENE_RGB'));
  assert.deepEqual(await f.store.readObservations(),before);
  await compiler.persistVisualPacket({store:f.store,compiled:c});
  for(const a of c.artifacts) assert.equal(sha256(await readFile(path.join(f.runDir,a.ref.path))),a.ref.sha256);
});
test('strict canonical identity, missing facts, image tamper, and incomplete capture fail closed',async t=>{
  const f=await fixture(t); await assert.rejects(compiler.compileVisualPacket({...f,sourceObservationId:'absent'}),/OBSERVATION/);
  const missing=await fixture(t,{mutate:m=>{m.structuredState.subjects=[];}});
  await assert.rejects(compiler.compileVisualPacket(missing),/SUBJECT/);
  const foreign=await fixture(t,{mutate:m=>{m.identity.runId='foreign';}});
  await assert.rejects(compiler.compileVisualPacket(foreign),/IDENTITY/);
  const partial=await fixture(t,{mutate:m=>{m.result.status='PARTIAL';m.result.gaps=['FRAME_MISSING'];}});
  await assert.rejects(compiler.compileVisualPacket(partial),/COMPLETE/);
  await writeFile(path.join(f.runDir,f.manifest.frames[0].imagePath),Buffer.from('tampered'));
  await assert.rejects(compiler.compileVisualPacket(f),/HASH/);
});
test('visual answers stay unresolved without explicit bounded evidence and never change facts',async t=>{
  const f=await fixture(t);const checks=[{checkId:'VIS-01',subjectUuid:UUID,question:'Feet below the ground?',answer:'NOT_VISIBLE',evidenceViews:['east']}];
  const c=await compiler.compileVisualPacket({...f,visualChecks:checks});
  assert.equal(c.packet.visualChecks[0].resolution,'UNRESOLVED');
  assert.equal(c.packet.visualChecks[0].epistemicStatus,'INFERRED');
  assert.equal(c.packet.visualVerdict,'NOT_RUN');
  assert.equal(c.packet.behaviorVerdict,'INCONCLUSIVE_CAPTURE_PERTURBATION');
  for(const bad of [{...checks[0],answer:'PASS'},{...checks[0],answer:'YES',evidenceViews:[]},{...checks[0],subjectUuid:'foreign'}])
    await assert.rejects(compiler.compileVisualPacket({...f,visualChecks:[bad]}));
  assert.deepEqual(c.packet.drilldown.map(x=>x.level),[0,1,2,3]);
  assert.equal(c.packet.drilldown[3].availability,'NOT_IMPLEMENTED_NO_PROVEN_NEED');
});
test('bounded crop keeps raw camera source and rejects out-of-bounds or enormous regions',async t=>{
  const f=await fixture(t);const crop=await compiler.createVisualCrop({...f,view:'east',region:{x:4,y:5,width:10,height:12}});
  const decoded=decodePng(crop.bytes); assert.deepEqual([decoded.width,decoded.height],[10,12]);
  assert.deepEqual([...decoded.rgba.slice(0,4)],f.colors[1]);
  assert.equal(crop.ref.rawSourceHashes[0],f.manifest.frames[1].imageHash);
  for(const region of [{x:-1,y:0,width:1,height:1},{x:63,y:0,width:2,height:1},{x:0,y:0,width:1e9,height:1}])
    await assert.rejects(compiler.createVisualCrop({...f,view:'east',region}));
});
test('derived persistence cannot traverse symlinks or rewrite finalized evidence',async t=>{
  const f=await fixture(t);const c=await compiler.compileVisualPacket(f);
  await mkdir(path.join(f.runDir,'elsewhere')); await symlink(path.join(f.runDir,'elsewhere'),path.join(f.runDir,'evidence/derived'),process.platform==='win32'?'junction':'dir');
  await assert.rejects(compiler.persistVisualPacket({store:f.store,compiled:c}),/SYMLINK/);
  const g=await fixture(t); const d=await compiler.compileVisualPacket(g);
  await writeFile(g.store.finalizationFile,'{}');
  await assert.rejects(compiler.persistVisualPacket({store:g.store,compiled:d}),/FINALIZED/);
});

test('raw view references distinguish canonical manifest identity from producer frame receipt hash',async t=>{
 const f=await fixture(t);const c=await compiler.compileVisualPacket(f);const view=c.packet.rawViews[0];
 assert.equal(view.manifestObservationId,f.sourceObservationId);
 assert.equal(view.producerFrameObservationHash,f.manifest.result.frames[0].observationHash);
 assert.equal(view.producerFrameObservationHashSemantics,'EXACT_PRODUCER_FRAME_ROW_BYTES');
 assert.equal(Object.hasOwn(view,'sourceObservationHash'),false);
});
test('timeline preserves exact subject scope and source and marks unrelated context',async t=>{
 const f=await fixture(t);const row=(await f.store.readObservations())[0];
 const other='00000000-0000-0000-0000-000000000099';
 await f.store.appendObservation({...row,observationId:'obs:entity:1',writerId:'entity',writerSeq:1,lane:'SERVER_ENTITY_STATE',
  scope:{kind:'ENTITY_UUID',entityUuid:other},source:{side:'SERVER',method:'entity_probe'},payload:{health:0}});
 const c=await compiler.compileVisualPacket({...f,timelineObservationIds:['obs:entity:1']});
 assert.deepEqual(c.packet.timeline[0].scope,{kind:'ENTITY_UUID',entityUuid:other});
 assert.deepEqual(c.packet.timeline[0].source,{side:'SERVER',method:'entity_probe'});
 assert.equal(c.packet.timeline[0].contextRole,'CONTEXT_ONLY_UNSELECTED_SUBJECT');
 assert.equal(c.packet.timeline[0].payload.health,0);
});
test('persist refuses a self-consistent foreign artifact even beside an authentic packet',async t=>{
 const f=await fixture(t);const c=await compiler.compileVisualPacket(f);
 const ref=structuredClone(c.artifacts[0].ref);c.artifacts[0].ref=ref;ref.binding.runId='foreign';const {artifactId,...body}=ref;
 const {stableJson}=await import('../../bridge/json.mjs');ref.artifactId=sha256(stableJson(body));
 await assert.rejects(compiler.persistVisualPacket({store:f.store,compiled:c}),/IDENTITY|LINEAGE|PACKET/);
});
