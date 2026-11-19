import test from 'node:test';
import assert from 'node:assert/strict';
import { buildReplayIndex, controlledSeek, createFrameSequence, labelCardinalTiming, step, validateFrameSequence } from '../frame-sequence.mjs';
import { buildInspectorModel, elevationSvg, spatialSheetSvg, validateInspection } from '../spatial-timeline.mjs';
import { replayViewerArtifact, replayViewerHtml } from '../replay-viewer.mjs';
import { ACTOR, binding, cue, frames, h, inspection, sampleBase, sequence, sequenceBody } from './fixtures.mjs';

const ids = () => [cue().cueId];

test('a synthetic sequence validates and its seal is enforced', () => {
  const s = sequence(ids());
  assert.equal(validateFrameSequence(s).mode, 'RECORD_REPLAY');
  assert.throws(() => validateFrameSequence({ ...s, origin: 'REAL_CLIENT' }), /FRAME_SEQUENCE_INTEGRITY/);
});

test('only RECORD_REPLAY and the Cardinal-4 capture stage are accepted in v1', () => {
  assert.throws(() => createFrameSequence({ ...sequenceBody(ids()), mode: 'CONTROLLED_SEEK' }), /ONLY_RECORD_REPLAY_SUPPORTED/);
  assert.throws(() => createFrameSequence({ ...sequenceBody(ids()), captureStage: 'AFTER_POST_EFFECT' }), /CAPTURE_STAGE_NOT_ALLOWED_IN_V1/);
  assert.deepEqual(controlledSeek({ controlledSeek: 'UNAVAILABLE' }), { status: 'UNAVAILABLE', reason: 'PROVIDER_CLOCK_CONTROL_NOT_PROVEN' });
});

test('false COMPLETE, lost restoration uncertainty and broken clocks are rejected', () => {
  assert.throws(() => sequence(ids(), { frames: frames(4, { missing: [2] }) }), /FALSE_COMPLETE_SEQUENCE/);
  assert.ok(sequence(ids(), { frames: frames(4, { missing: [2] }), result: { status: 'PARTIAL', gaps: ['frame-2-missing'] } }));
  assert.throws(() => sequence(ids(), { restoration: 'UNKNOWN' }), /RESTORATION_UNCERTAINTY_LOST/);
  const f = frames(); f[2].renderFrame = f[1].renderFrame;
  assert.throws(() => sequence(ids(), { frames: f }), /FRAME_CLOCK_NOT_MONOTONIC/);
  const g = frames(); g[1].imagePath = '../../../secret.png';
  assert.throws(() => sequence(ids(), { frames: g }), /RAW_ARTIFACT_BINDING_MISMATCH/);
  const m = frames(4, { missing: [1] }); m[1].imageHash = h('ghost');
  assert.throws(() => sequence(ids(), { frames: m, result: { status: 'PARTIAL', gaps: [] } }), /MISSING_FRAME_HAS_IMAGE/);
});

test('frame and byte budgets are enforced', () => {
  assert.throws(() => sequence(ids(), { budget: { maxFrames: 3, maxTotalBytes: 10_000_000, maxDurationTicks: 40 } }), /FRAME_BUDGET_EXCEEDED/);
  assert.throws(() => sequence(ids(), { budget: { maxFrames: 120, maxTotalBytes: 3999, maxDurationTicks: 40 } }), /BYTE_BUDGET_EXCEEDED/);
  assert.throws(() => sequence(ids(), { budget: { maxFrames: 601, maxTotalBytes: 1, maxDurationTicks: 1 } }), /SEQUENCE_BUDGET/);
});

test('replay index exposes drops, stale images and skew without causal claims', () => {
  const f = frames(5);
  f[3].renderFrame = 1010; f[4].renderFrame = 1011; // 7 render frames (1003..1009) dropped before #3
  f[4].imageHash = f[3].imageHash; f[4].imagePath = f[3].imagePath; f[4].clientTick = f[3].clientTick + 1;
  const idx = buildReplayIndex(sequence(ids(), { frames: f }));
  assert.equal(idx.semantics, 'RECORDED_IMAGE_REPLAY_NOT_WORLD_REWIND');
  assert.ok(idx.rows[3].flags.includes('DROPPED_RENDER_FRAMES:7'));
  assert.ok(idx.rows[4].flags.includes('IDENTICAL_IMAGE_WHILE_TIME_ADVANCED'));
  assert.ok(idx.rows[0].flags.includes('VFX_TIME_NOT_EXPOSED'));
  assert.equal(typeof idx.rows[4].clientMinusServerTicks, 'number');
  assert.deepEqual(step(idx, 0, -1), { cursor: 0, moved: false, row: idx.rows[0] });
  assert.equal(step(idx, 0, 99 > idx.frameCount ? idx.frameCount : 99).cursor, idx.frameCount - 1);
});

test('Cardinal timing is SAME_VFX_INSTANT only with identical directly observed clocks', () => {
  const four = frames(4);
  assert.equal(labelCardinalTiming(four, Array(4).fill({ status: 'DIRECT_OBSERVED', ticks: 3 })).label, 'SAME_VFX_INSTANT');
  const skew = labelCardinalTiming(four, [0, 1, 2, 3].map(t => ({ status: 'DIRECT_OBSERVED', ticks: t })));
  assert.equal(skew.label, 'SEQUENTIAL_TIME_SKEW'); assert.equal(skew.vfxSpanTicks, 3); assert.equal(skew.sameFrame, false);
  assert.equal(labelCardinalTiming(four, Array(4).fill({ status: 'DERIVED', ticks: 3 })).label, 'UNKNOWN_VFX_CLOCK');
  const shuffled = frames(4); shuffled[2].renderFrame = 1;
  assert.throws(() => labelCardinalTiming(shuffled, Array(4).fill({ status: 'DIRECT_OBSERVED', ticks: 3 })), /FRAME_CLOCK_NOT_MONOTONIC/);
});

test('replay viewer embeds data safely and binds raw sources', () => {
  const s = sequence(ids());
  const html = replayViewerHtml(s);
  assert.match(html, /RECORDED_IMAGE_REPLAY_NOT_WORLD_REWIND/);
  assert.ok(!/<\/script><script>alert/.test(html));
  const { ref } = replayViewerArtifact(s, { runId: 'run-1' });
  assert.equal(ref.role, 'DERIVED_REPLAY_VIEWER'); assert.equal(ref.rawSourceHashes.length, 4);
  assert.match(ref.path, /^evidence\/derived\/visual\/[a-f0-9]{64}\.html$/);
});

test('inspection rejects mixed runs, unregistered subjects and exposed particle claims', () => {
  assert.ok(validateInspection(inspection()));
  const mixed = inspection(); mixed.samples[0].binding = { ...binding(), arenaEpoch: 4 };
  assert.throws(() => validateInspection(mixed), /MIXED_RUN_OR_EPOCH/);
  const stranger = inspection(); stranger.samples[0].subjectUuid = '00000000-0000-4000-8000-000000000000';
  assert.throws(() => validateInspection(stranger), /UNREGISTERED_SUBJECT/);
  const particles = inspection(); Object.assign(particles.samples[3], { status: 'OBSERVED', epistemic: 'DIRECT_OBSERVED', position: [1, 2, 3], observationId: 'x' });
  assert.throws(() => validateInspection(particles), /PARTICLE_POSITIONS_NOT_EXPOSED_IN_V1/);
  const clocks = inspection(); clocks.samples[1].serverTick = 100;
  assert.throws(() => validateInspection(clocks), /CLIENT_SAMPLE_HAS_SERVER_TICK/);
  const outside = inspection({ blockSamples: { roi: { min: [0, 50, 0], max: [4, 64, 4] }, blocks: [] } });
  assert.throws(() => validateInspection(outside), /BLOCK_ROI_OUTSIDE_ARENA/);
  const big = inspection({ arenaBounds: { min: [0, 60, 0], max: [32, 76, 16] }, blockSamples: { roi: { min: [0, 60, 0], max: [32, 76, 16] }, blocks: [] } });
  assert.throws(() => validateInspection(big), /BLOCK_ROI_TOO_LARGE/);
  const blocks = inspection({ blockSamples: { roi: { min: [0, 60, 0], max: [4, 64, 4] }, blocks: [{ pos: [1, 60, 1], state: 'minecraft:stone' }, { pos: [1, 60, 1], state: 'minecraft:dirt' }] } });
  assert.throws(() => validateInspection(blocks), /DUPLICATE_BLOCK_SAMPLE/);
});

test('inspector model keeps WORLD vs ARENA_LOCAL, UNKNOWN subjects and non-causal correlation', () => {
  const model = buildInspectorModel(inspection());
  const row = model.rows.find(r => r.gameTime === 5100);
  const actor = row.samples.find(s => s.sampleId === 's-actor');
  assert.deepEqual(actor.world, { x: 4, y: 64, z: 8 });
  assert.deepEqual(actor.arenaLocal, { x: 4, y: 4, z: 8 });
  assert.equal(row.samples.find(s => s.sampleId === 's-particles').world, 'UNKNOWN');
  assert.equal(row.missingSubjects.length, 1); // target has no server state at this time
  const start = model.correlation.find(c => c.kind === 'START');
  assert.equal(start.clientMinusServerGameTicks, 1); assert.equal(start.causality, 'NOT_ESTABLISHED');
  assert.equal(model.correlation.find(c => c.kind === 'HIT').status, 'UNPAIRED');
});

test('elevation and sheet SVGs draw provenance-tagged points and list UNKNOWN', () => {
  const x = inspection();
  const model = buildInspectorModel(x);
  const side = elevationSvg(model, x, 5100, 'X').toString();
  assert.match(side, /data-source-kind="CLIENT_RENDER_POSE"/);
  assert.match(side, /data-world-y="65.4"/);
  assert.match(side, /UNKNOWN · FX_PARTICLE_FIELD fx-1: NOT_EXPOSED/);
  assert.match(side, /UNKNOWN · SERVER_ENTITY_STATE B: UNKNOWN/);
  const sheet = spatialSheetSvg(model, x, 5100).toString();
  assert.match(sheet, /Exact X\/Z schematic/); assert.match(sheet, /Exact Z\/Y elevation/);
  assert.throws(() => elevationSvg(model, x, 5100, 'Y'), /INVALID_ELEVATION_AXIS/);
  const hostile = inspection(); hostile.samples.push(sampleBase({ sampleId: 's-x', sourceKind: 'FX_EMITTER', fxInstanceId: 'fx-<script>', renderFrame: 1, partialTick: 0, observationId: 'o', position: [1, 61, 1] }));
  assert.throws(() => validateInspection(hostile), /INVALID_IDENTIFIER/);
  assert.equal(ACTOR < model.labels[1].uuid, true);
});
