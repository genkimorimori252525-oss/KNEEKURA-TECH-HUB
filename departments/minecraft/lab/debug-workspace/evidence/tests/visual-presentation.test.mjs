import test from 'node:test';
import assert from 'node:assert/strict';
import { fixture,UUID } from './visual-fixture.mjs';
import { compileVisualPacket } from '../visual-compiler.mjs';
import * as presentation from '../visual-presentation.mjs';
import { sha256,stableJson } from '../../bridge/json.mjs';
test('three human modes are independent projections of the immutable AI packet',async t=>{
 const f=await fixture(t);const c=await compileVisualPacket(f);const original=stableJson(c.packet);
 const normal=presentation.createHumanPresentation({packet:c.packet,mode:'HumanNormal'});
 const debug=presentation.createHumanPresentation({packet:c.packet,mode:'HumanDebug',overlayIds:['subject_labels','bounds']});
 const review=presentation.createHumanPresentation({packet:c.packet,mode:'HumanEvidenceReview'});
 assert.deepEqual(normal.binding,debug.binding);assert.deepEqual(review.binding,c.packet.binding);
 assert.equal(normal.sceneRole,'RAW_SCENE_RGB');assert.equal(debug.overlayRole,'DERIVED_PRESENTATION');
 assert.equal(review.temporalStatus,'RETAINED_EVIDENCE_NOT_LIVE');
 assert.deepEqual(normal.overlays,[]);assert.equal(stableJson(c.packet),original);
 assert.notEqual(normal.presentationId,debug.presentationId);
 assert.throws(()=>presentation.createHumanPresentation({packet:c.packet,mode:'HumanNormal',overlayIds:['bounds']}));
 const tampered=structuredClone(c.packet);tampered.binding.generation++;
 assert.throws(()=>presentation.createHumanPresentation({packet:tampered,mode:'HumanDebug'}),/PACKET/);
});
test('unknown interactions fail closed and observation/mutation commands never execute through presentation',()=>{
 for(const type of ['panel_layout','select_evidence','overlay_visibility','contact_sheet_zoom','retained_timeline_browse'])assert.equal(presentation.classifyInteraction(type).classification,'PRESENTATION_ONLY');
 for(const type of ['free_camera_move','change_fov','force_render_view','open_pausing_screen'])assert.equal(presentation.classifyInteraction(type).classification,'OBSERVATION_AFFECTING');
 for(const type of ['pause','slow_motion','teleport','change_blocks','change_entities','change_time_weather','change_config','scenario_action'])assert.equal(presentation.classifyInteraction(type).classification,'EXPERIMENT_MUTATION');
 assert.equal(presentation.classifyInteraction('teleport').executionRoute,'TYPED_CONTROL_WITH_RECEIPT');
 assert.throws(()=>presentation.classifyInteraction('arbitrary_script'),/UNKNOWN/);
});
test('review HTML has bounded relative hashed assets and usable mode controls with no runtime or script connection',async t=>{
 const f=await fixture(t);const c=await compileVisualPacket(f);
 const a=presentation.createEvidenceReviewArtifact({packet:c.packet}); const html=a.bytes.toString();
 assert.match(html,/type="radio"/); assert.match(html,/Human Normal/);assert.match(html,/Human Debug/);assert.match(html,/Human Evidence Review/);
 assert.match(html,/Retained evidence, not current runtime/);assert.match(html,/default-src 'none'/);
 assert.doesNotMatch(html,/<script|https?:|fetch\(|WebSocket/);
 assert.match(html,new RegExp(`${c.packet.contactSheet.sha256}\\.png`));
 assert.equal(sha256(a.bytes),a.ref.sha256);assert.equal(a.ref.role,'DERIVED_HUMAN_EVIDENCE_REVIEW');
});
test('AI finding feedback remains attributed and bound to exact retained evidence',async t=>{
 const f=await fixture(t);const c=await compileVisualPacket({...f,visualChecks:[{checkId:'VIS-01',subjectUuid:UUID,question:'Feet below ground?',answer:'AMBIGUOUS',evidenceViews:['east']}]});
 const finding={findingId:'finding-1',epistemicStatus:'INFERRED',subjectUuid:UUID,view:'east',checkId:'VIS-01',
   result:'AMBIGUOUS',explanation:'Possible foot clipping',evidenceHashes:[c.packet.rawViews[1].imageHash]};
 const p=presentation.createHumanPresentation({packet:c.packet,mode:'HumanEvidenceReview',finding});
 assert.throws(()=>presentation.createHumanPresentation({packet:c.packet,mode:'HumanEvidenceReview',finding:{...finding,checkId:'unknown'}}),/CHECK/);
 assert.equal(p.finding.epistemicStatus,'INFERRED');assert.deepEqual(p.finding.stateWindow,c.packet.binding.stateWindow);
 assert.throws(()=>presentation.createHumanPresentation({packet:c.packet,mode:'HumanEvidenceReview',finding:{...finding,evidenceHashes:['f'.repeat(64)]}}),/EVIDENCE/);
});
test('rehashed packets cannot relabel stale nested artifacts or omit required packet fields',async t=>{
 const f=await fixture(t);const c=await compileVisualPacket(f);
 for(const fault of ['binding','raw_hash','artifact_hash','missing','subject']) {
  const packet=structuredClone(c.packet);
  if(fault==='binding')packet.binding.generation=99;
  if(fault==='raw_hash')packet.rawViews[0].imageHash='f'.repeat(64);
  if(fault==='artifact_hash')packet.contactSheet.artifactId='f'.repeat(64);
  if(fault==='missing')delete packet.structuredSummary;
  if(fault==='subject')packet.labels[0].uuid='00000000-0000-0000-0000-000000000002';
  const {packetId,...body}=packet;packet.packetId=sha256(stableJson(body));
  assert.throws(()=>presentation.createHumanPresentation({packet,mode:'HumanEvidenceReview'}),/PACKET|ARTIFACT|LABEL|IDENTITY/);
 }
});

test('retained review rejects rehashed visual answers without valid distinct camera evidence',async t=>{
 const f=await fixture(t);const c=await compileVisualPacket({...f,visualChecks:[{checkId:'VIS-01',subjectUuid:UUID,question:'Feet below ground?',answer:'YES',evidenceViews:['east']}]});
 const faults={
  missing_evidence:p=>{p.visualChecks[0].evidenceViews=[];p.visualChecks[0].evidence=[];},
  unknown_view:p=>{p.visualChecks[0].evidenceViews=['other'];p.visualChecks[0].evidence=[{view:'other'}];},
  duplicate_views:p=>{p.visualChecks[0].evidenceViews=['east','east'];p.visualChecks[0].evidence.push({...p.visualChecks[0].evidence[0]});},
  duplicate_check:p=>{p.visualChecks.push(structuredClone(p.visualChecks[0]));},
  blank_question:p=>{p.visualChecks[0].question='   ';},
  extra_authority:p=>{p.visualChecks[0].acceptance='PASS';},
  changed_semantics:p=>{p.visualChecks[0].semantics='OBSERVED_ACCEPTANCE';}
 };
 for(const [name,change] of Object.entries(faults))await t.test(name,()=>{
  const packet=structuredClone(c.packet);change(packet);
  const {packetId,...body}=packet;packet.packetId=sha256(stableJson(body));
  assert.throws(()=>presentation.createEvidenceReviewArtifact({packet}),/PACKET_VISUAL_CHECK/);
 });
 const pending=await compileVisualPacket({...f,visualChecks:[{checkId:'VIS-02',subjectUuid:UUID,question:'Texture visible?',answer:'NOT_RUN',evidenceViews:[]}]});
 assert.doesNotThrow(()=>presentation.createEvidenceReviewArtifact({packet:pending.packet}));
});
