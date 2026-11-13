import test from 'node:test';
import assert from 'node:assert/strict';
import { applyRepair, buildEvidencePacket, compareSetups, createRepairProposal } from '../repair.mjs';
import { createAssetManifest, invalidateForRig } from '../asset-manifest.mjs';
import { verifySeal } from '../common.mjs';
import { cue, frames, ref, sequence } from './fixtures.mjs';

const proposal = (c, overrides = {}) => createRepairProposal({
  targetCueId: c.cueId, runtimeAssetHash: c.runtimeAssetHash, generation: c.generation, scope: ['startOffsetTicks'],
  changes: [{ param: 'startOffsetTicks', expectedOld: 0, next: 2 }],
  finding: { summary: 'Afterglow appears 2 ticks before the weapon bone reaches the swing arc', epistemic: 'SAMPLED_OBSERVED', evidenceRefs: ['obs-b', 'obs-c'] },
  ...overrides,
});

test('a bounded repair changes only the named parameter and bumps generation', () => {
  const c = cue();
  const r = applyRepair(c, proposal(c));
  assert.equal(r.after.params.startOffsetTicks, 2);
  assert.equal(r.after.generation, 2);
  assert.notEqual(r.after.cueId, c.cueId);
  assert.deepEqual({ ...r.after.params, startOffsetTicks: 0 }, c.params);
  assert.deepEqual(r.diff, [{ param: 'startOffsetTicks', before: 0, after: 2 }]);
});

test('stale generation, wrong expected value, asset swap and wrong target are rejected', () => {
  const c = cue();
  const r = applyRepair(c, proposal(c));
  assert.throws(() => applyRepair(r.after, proposal(c)), /REPAIR_TARGET_MISMATCH/);
  assert.throws(() => applyRepair(r.after, proposal(r.after, { generation: 1 })), /STALE_REPAIR_GENERATION/);
  assert.throws(() => applyRepair(c, proposal(c, { changes: [{ param: 'startOffsetTicks', expectedOld: 5, next: 2 }] })), /EXPECTED_OLD_MISMATCH/);
  assert.throws(() => applyRepair(c, proposal(c, { runtimeAssetHash: ref('other') })), /REPAIR_ASSET_CHANGED/);
});

test('proposals cannot reach outside the FX parameter schema', () => {
  const c = cue();
  assert.throws(() => proposal(c, { scope: ['bone'] }), /MODEL_EDIT_DELEGATED_TO_BLOCKBENCH_GUARD/);
  assert.throws(() => proposal(c, { scope: ['shader'] }), /FX_PARAMETER_NOT_ALLOWED/);
  assert.throws(() => proposal(c, { changes: [{ param: 'lifetime', expectedOld: 12, next: 14 }] }), /CHANGE_OUTSIDE_SCOPE/);
  assert.throws(() => proposal(c, { changes: [{ param: 'startOffsetTicks', expectedOld: 0, next: 9999 }] }), /OUT_OF_RANGE/);
  assert.throws(() => proposal(c, { finding: { summary: 'looks off', epistemic: 'VISUAL_INFERRED', evidenceRefs: [] } }), /FINDING_EVIDENCE_REQUIRED/);
});

const cell = (verdict, evidenceRefs = ['obs-1']) => ({ verdict, evidenceRefs, note: null });
const allNotRun = () => Object.fromEntries(['structure', 'visual', 'gameplay', 'performance', 'human_preference'].map(k => [k, cell('NOT_RUN', [])]));

test('synthetic evidence can never certify runtime columns; packet is never complete', () => {
  const c = cue(); const r = applyRepair(c, proposal(c));
  const before = sequence([c.cueId]); const after = sequence([r.after.cueId]);
  const verdicts = { ...allNotRun(), structure: cell('PASS') };
  const packet = buildEvidencePacket({ repair: r, beforeSequence: before, afterSequence: after, verdicts });
  verifySeal(packet, 'packetId', 'X');
  assert.equal(packet.complete, false); assert.equal(packet.origin, 'SYNTHETIC_OR_MIXED');
  assert.equal(packet.setup.status, 'SAME_SETUP');
  assert.throws(() => buildEvidencePacket({ repair: r, beforeSequence: before, afterSequence: after, verdicts: { ...verdicts, visual: cell('PASS') } }), /SYNTHETIC_EVIDENCE_CANNOT_PASS_RUNTIME/);
  assert.throws(() => buildEvidencePacket({ repair: r, beforeSequence: before, afterSequence: after, verdicts: { ...verdicts, structure: cell('PASS', []) } }), /VERDICT_WITHOUT_EVIDENCE/);
  assert.throws(() => buildEvidencePacket({ repair: r, beforeSequence: before, afterSequence: after, humanDecision: 'PENDING',
    verdicts: { ...verdicts, human_preference: cell('PASS') } }), /HUMAN_PREFERENCE_NOT_APPROVED/);
});

test('real-client packet requires same setup and restoration for visual PASS', () => {
  const c = cue(); const r = applyRepair(c, proposal(c));
  const before = sequence([c.cueId], { origin: 'REAL_CLIENT' });
  const moved = frames(); moved.forEach(f => { f.camera.position = [1, 66, 10]; });
  const after = sequence([r.after.cueId], { origin: 'REAL_CLIENT', frames: moved });
  assert.deepEqual(compareSetups(before, after), { status: 'INCONCLUSIVE', differences: ['camera'] });
  const pass = Object.fromEntries(['structure', 'visual', 'gameplay', 'performance', 'human_preference'].map(k => [k, cell('PASS')]));
  assert.throws(() => buildEvidencePacket({ repair: r, beforeSequence: before, afterSequence: after, verdicts: pass, humanDecision: 'APPROVED' }), /SAME_SETUP_AND_RESTORATION/);
  const same = sequence([r.after.cueId], { origin: 'REAL_CLIENT' });
  const ok = buildEvidencePacket({ repair: r, beforeSequence: before, afterSequence: same, verdicts: pass, humanDecision: 'APPROVED' });
  assert.equal(ok.complete, true);
  const forged = { ...r, diff: [{ param: 'startOffsetTicks', before: 0, after: 7 }] };
  assert.throws(() => buildEvidencePacket({ repair: forged, beforeSequence: before, afterSequence: same, verdicts: pass, humanDecision: 'APPROVED' }), /REPAIR_RECORD_INCONSISTENT/);
});

const RIG = ref('rig-v1');
const event = (o) => ({ fromCandidate: null, type: 'SELECT', provider: { name: 'img2blockbench', revision: 'b'.repeat(40), license: 'MIT' },
  inputRef: ref('input'), outputRef: ref(`out-${o.eventId}`), reason: 'clear front reference image', rejectedAlternatives: [],
  externalSend: { sent: false, destination: null, costEstimate: null, approvalRef: null }, measuredQuality: 'NOT_MEASURED', unverifiedAreas: ['back_side'], ...o });
function manifestBody(overrides = {}) {
  return {
    assetId: 'kneekura:test_mob', profileRef: ref('profile'),
    model: { method: 'mosaicary.gltf', candidate: 'B', sourceRef: ref('src'), bbmodelRef: ref('bb'), geoRef: ref('geo'), textureRefs: [ref('atlas')], rigRef: RIG,
      losses: [{ kind: 'CURVE_EASING', detail: 'Bezier tangents sampled to linear keys' }] },
    animations: { attack: { method: 'procedural_baked', candidate: 'atk1', clipRef: ref('attack'), rigRef: RIG, losses: [] } },
    vfx: [{ method: 'photon_candidate', candidate: 'fx1', cueRef: ref('cue'), boneLayoutRef: RIG }],
    methodHistory: [
      event({ eventId: 'm1', stage: 'model', toCandidate: 'A', method: 'img2blockbench.direct' }),
      event({ eventId: 'm2', stage: 'model', type: 'SWITCH', fromCandidate: 'A', toCandidate: 'B', method: 'mosaicary.gltf', reason: 'licensed GLB with rig available',
        provider: { name: 'mosaicary', revision: 'c'.repeat(40), license: 'MIT' } }),
      event({ eventId: 'a1', stage: 'animation:attack', toCandidate: 'atk1', method: 'procedural_baked' }),
      event({ eventId: 'v1', stage: 'vfx', toCandidate: 'fx1', method: 'photon_candidate', provider: { name: 'photon', revision: '507499fbe5a3fc72bb90993e059848cbb31f13ca', license: 'GPL-3.0' } }),
    ],
    verificationRefs: [ref('structure-check')], humanReview: 'NOT_REQUESTED', ...overrides,
  };
}

test('asset manifest keeps switched-away candidates and marks lossy conversion', () => {
  const r = createAssetManifest(manifestBody());
  assert.equal(r.conversion.model, 'LOSSY_CONVERSION');
  assert.equal(r.conversion.clips.attack, 'NO_LOSS_RECORDED');
  assert.ok(r.retainedCandidates.some(c => c.stage === 'model' && c.candidate === 'A'));
});

test('asset manifest rejects stale rigs, excluded methods, placeholders and unapproved sends', () => {
  const body = manifestBody();
  assert.throws(() => createAssetManifest({ ...body, animations: { attack: { ...body.animations.attack, rigRef: ref('rig-v0') } } }), /CLIP_BOUND_TO_DIFFERENT_RIG/);
  assert.throws(() => createAssetManifest({ ...body, animations: { attack: { ...body.animations.attack, method: 'kimodo' } } }), /METHOD_EXCLUDED_BY_USER/);
  assert.throws(() => createAssetManifest({ ...body, profileRef: 'sha256:<profile>' }), /INVALID_CONTENT_REF/);
  const sent = manifestBody(); sent.methodHistory[0].externalSend = { sent: true, destination: 'api.example.com', costEstimate: '$0.10', approvalRef: null };
  assert.throws(() => createAssetManifest(sent), /EXTERNAL_SEND_APPROVAL_REQUIRED/);
  const smuggled = manifestBody(); smuggled.methodHistory[2].provider = { name: 'Kimodo-wrapper', revision: null, license: 'MIT' };
  assert.throws(() => createAssetManifest(smuggled), /METHOD_EXCLUDED_BY_USER/);
  const orphan = manifestBody(); orphan.methodHistory[1].fromCandidate = 'Z';
  assert.throws(() => createAssetManifest(orphan), /SWITCH_FROM_UNKNOWN_CANDIDATE/);
  const twice = manifestBody(); twice.methodHistory[1] = event({ eventId: 'm2', stage: 'model', toCandidate: 'B', method: 'mosaicary.gltf' });
  assert.throws(() => createAssetManifest(twice), /SECOND_SELECT_USE_SWITCH/);
  assert.throws(() => createAssetManifest({ ...body, model: { ...body.model, candidate: 'A' } }), /MODEL_CANDIDATE_NOT_FINAL_IN_HISTORY/);
});

test('a rig change invalidates clips and bone emitters instead of rebinding them', () => {
  const { manifest } = createAssetManifest(manifestBody());
  assert.equal(invalidateForRig(manifest, RIG).status, 'UNCHANGED');
  const r = invalidateForRig(manifest, ref('rig-v2'));
  assert.deepEqual(r.invalidated.map(i => `${i.kind}:${i.id}`), ['CLIP:attack', 'BONE_EMITTER:fx1']);
});
