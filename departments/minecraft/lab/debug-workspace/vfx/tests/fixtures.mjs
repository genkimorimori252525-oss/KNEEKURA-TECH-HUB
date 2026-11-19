// Synthetic fixtures. Every sequence built here is origin SYNTHETIC_FIXTURE and can never certify runtime.
import { createHash } from 'node:crypto';
import { createCue } from '../cue-contract.mjs';
import { createFrameSequence } from '../frame-sequence.mjs';

export const h = s => createHash('sha256').update(String(s)).digest('hex');
export const ref = s => `sha256:${h(s)}`;
export const ACTOR = '11111111-2222-4333-8444-555555555555';
export const TARGET = '66666666-7777-4888-9999-aaaaaaaaaaaa';
export const PROVIDER = { providerId: 'photon-1.20.1-forge', providerSourceRevision: '507499fbe5a3fc72bb90993e059848cbb31f13ca' };
export const ASSET = ref('slash-asset-v1');
export const LAYOUT = ref('bone-layout-v1');

export function cueBody(overrides = {}) {
  return {
    effectId: 'kneekura:slash_afterglow', ...PROVIDER, runtimeAssetHash: ASSET,
    profile: { profileHash: ref('profile'), buildHash: ref('build'), resourceHash: ref('resource'), configHash: ref('config') },
    generation: 1, attackInstanceId: 'attack-1', eventKind: 'START', actorUuid: ACTOR, targetUuid: TARGET,
    dimension: 'minecraft:overworld',
    attachment: { kind: 'BONE', entityUuid: ACTOR, bone: 'weapon_tip', modelVersion: 'test_mob-1', boneLayoutHash: LAYOUT, localOffset: [0, 0, 0.5] },
    timing: { serverTick: 100, serverGameTime: 5100, durationTicks: 12 },
    params: { color: [0.6, 0.85, 1], lifetime: 12, spawnRate: 200, trailWidth: 0.4, intensity: 1.5, startOffsetTicks: 0, emitterLocalOffset: [0, 0, 0] },
    limits: { maxConcurrentEffects: 4, maxParticles: 512, maxTrailLength: 32, maxCumulativeGlow: 4, maxRecordedFrames: 120,
      maxCpuMillisPerFrame: 2, maxGpuMillisPerFrame: 4, maxMemoryBytes: 16 * 1024 * 1024 },
    ...overrides,
  };
}
export const cue = (overrides = {}) => createCue(cueBody(overrides));

export const identity = () => ({ debugSessionId: 'debug-1', runId: 'run-1', runSnapshotId: 'snap-1', processEpoch: 1, experimentId: 'exp-1',
  generation: 1, requestHash: h('request'), arenaId: 'arena-1', arenaEpoch: 3, arenaRevision: 7, baselineHash: h('baseline') });

export const camera = () => ({ position: [0, 66, 10], quaternion: [0, 0, 0, 1], yaw: 180, pitch: 0, fov: 70, projection: 'PERSPECTIVE',
  projectionMatrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, -1, 0, 0, -0.2, 0], viewMatrix: [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  matrixConvention: 'JOML_COLUMN_MAJOR_CAMERA_RELATIVE', viewport: [320, 180] });

export function frames(count = 4, { startRender = 1000, missing = [] } = {}) {
  return Array.from({ length: count }, (_, i) => {
    const imageHash = h(`frame-${i}`);
    const absent = missing.includes(i);
    return { index: i, status: absent ? 'MISSING' : 'PRESENT', serverTick: 100 + Math.floor(i / 2), serverGameTime: 5100 + Math.floor(i / 2),
      clientTick: 200 + Math.floor(i / 2), renderFrame: startRender + i, partialTick: (i % 2) * 0.5, captureTimeNanos: 1_000_000 + i * 16_000_000,
      vfxTime: i === 0 ? { status: 'NOT_EXPOSED' } : { status: 'DERIVED', ticks: i * 0.5 }, camera: camera(),
      imageHash: absent ? null : imageHash, imageBytes: absent ? null : 1000, imagePath: absent ? null : `evidence/raw/visual/${imageHash}.png`,
      sourceObservationId: absent ? null : `obs-${i}` };
  });
}

export function sequenceBody(cueIds, overrides = {}) {
  return { origin: 'SYNTHETIC_FIXTURE', identity: identity(), subjects: [ACTOR, TARGET],
    fx: { effectId: 'kneekura:slash_afterglow', runtimeAssetHash: ASSET, attackInstanceId: 'attack-1', fxInstanceId: 'fx-1', cueIds },
    cameraId: 'fixed-east', budget: { maxFrames: 120, maxTotalBytes: 10_000_000, maxDurationTicks: 40 },
    frames: frames(), restoration: 'RESTORED', result: { status: 'COMPLETE', gaps: [] }, ...overrides };
}
export const sequence = (cueIds, overrides = {}) => createFrameSequence(sequenceBody(cueIds, overrides));

export const binding = () => ({ runId: 'run-1', processEpoch: 1, arenaId: 'arena-1', arenaEpoch: 3 });
export function sampleBase(overrides) {
  return { status: 'OBSERVED', epistemic: 'DIRECT_OBSERVED', subjectUuid: null, fxInstanceId: null, bone: null, modelHash: null,
    boneLayoutHash: null, gameTime: 5100, serverTick: null, renderFrame: null, partialTick: null, position: null, velocity: null,
    yaw: null, pitch: null, aabb: null, binding: binding(), observationId: null, ...overrides };
}
export function inspection(overrides = {}) {
  return {
    schemaVersion: 1, kind: 'kneekura_spatial_timeline_inspection', binding: binding(), dimension: 'minecraft:overworld',
    arenaBounds: { min: [0, 60, 0], max: [16, 76, 16] }, subjects: [ACTOR, TARGET], window: { start: 5090, end: 5130 },
    samples: [
      sampleBase({ sampleId: 's-actor', sourceKind: 'SERVER_ENTITY_STATE', subjectUuid: ACTOR, serverTick: 100, observationId: 'obs-a',
        position: [4, 64, 8], velocity: [0.1, 0, 0], yaw: -90, pitch: 0, aabb: [3.7, 64, 7.7, 4.3, 65.9, 8.3] }),
      sampleBase({ sampleId: 's-bone', sourceKind: 'CLIENT_RENDER_POSE', subjectUuid: ACTOR, bone: 'weapon_tip', modelHash: ref('model'),
        boneLayoutHash: LAYOUT, renderFrame: 1001, partialTick: 0.5, observationId: 'obs-b', position: [5.2, 65.4, 8] }),
      sampleBase({ sampleId: 's-emitter', sourceKind: 'FX_EMITTER', fxInstanceId: 'fx-1', renderFrame: 1001, partialTick: 0.5,
        observationId: 'obs-c', position: [5.3, 65.4, 8], epistemic: 'SAMPLED_OBSERVED' }),
      sampleBase({ sampleId: 's-particles', sourceKind: 'FX_PARTICLE_FIELD', fxInstanceId: 'fx-1', renderFrame: 1001, partialTick: 0.5,
        status: 'NOT_EXPOSED', epistemic: 'NOT_EXPOSED' }),
    ],
    events: [
      { eventId: 'e-server-start', kind: 'START', side: 'SERVER', attackInstanceId: 'attack-1', gameTime: 5100, renderFrame: null, observationId: 'obs-e1' },
      { eventId: 'e-client-start', kind: 'START', side: 'CLIENT', attackInstanceId: 'attack-1', gameTime: 5101, renderFrame: 1002, observationId: 'obs-e2' },
      { eventId: 'e-server-hit', kind: 'HIT', side: 'SERVER', attackInstanceId: 'attack-1', gameTime: 5104, renderFrame: null, observationId: 'obs-e3' },
    ],
    blockSamples: null, ...overrides,
  };
}
