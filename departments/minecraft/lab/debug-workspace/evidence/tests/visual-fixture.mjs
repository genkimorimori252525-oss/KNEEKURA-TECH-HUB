import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { EvidenceStore } from '../store.mjs';
import { sha256 } from '../../bridge/json.mjs';
import { encodePngRgba } from '../../../simlab/golden/png.mjs';
export const UUID = '00000000-0000-0000-0000-000000000001';
export const HASH = 'a'.repeat(64);
export function request() {
  return { schema_version: 1, experiment_id: 'experiment', generation: 1,
    target: { profile_id: HASH, index_snapshot_id: HASH, build_artifact_hash: HASH,
      source_revision: 'a'.repeat(40), dirty_hash: HASH, config_hash: HASH, resource_hash: HASH },
    arena: { arena_id: 'arena', preset: 'normal', baseline_hash: HASH, bounds: { min: [-8,0,-8], max: [8,16,8] } },
    subjects: [{ subject_id: 'subject', uuid: UUID, entity_type: 'minecraft:pig' }],
    initial_state: [], actions: [{ action_id: 'action-1', operation: 'wait_ticks', ticks: 5 }],
    observation_scopes: [{ kind: 'ENTITY_UUID', subject_id: 'subject', lanes: ['SERVER_ENTITY_STATE'], level: 'L1' }],
    visual_rig: { mode: 'cardinal-4-snapshot-v1', fov: 90, viewport: [64,64] },
    assertions: [{ assertion_id: 'behavior-1', kind: 'structured', subject_id: 'subject', field: 'health', operator: 'equals', expected: 20 }],
    budgets: { time_budget_ms: 1000, max_actions: 1, max_captures: 4 } };
}
export async function fixture(t, { run = 'run', tick = 30, mutate = () => {}, request: req = request() } = {}) {
  const runDir = await mkdtemp(path.join(os.tmpdir(), 'lab-visual-'));
  t.after(() => rm(runDir, { recursive: true, force: true }));
  const requestBytes = Buffer.from(JSON.stringify(req));
  const identity = { debugSessionId: 'session', runId: run, runSnapshotId: run + '-snapshot', processEpoch: 1,
    experimentId: req.experiment_id, generation: req.generation, requestHash: sha256(requestBytes), arenaId: 'arena',
    arenaEpoch: 0, arenaRevision: 1, baselineHash: HASH };
  const store = new EvidenceStore({ runDir, ...identity }); await store.init();
  await mkdir(path.join(runDir, 'evidence/raw/visual'), { recursive: true });
  const colors = [[255,0,0,255], [0,255,0,255], [0,0,255,255], [255,255,0,255]];
  const raw = [];
  const frames = [];
  for (const [i, view] of ['north','east','south','west'].entries()) {
    const rgba = Uint8Array.from({ length: 64*64*4 }, (_,j) => colors[i][j%4]);
    const bytes = encodePngRgba({ width: 64, height: 64, rgba }); raw.push(bytes);
    const imageHash = sha256(bytes); const imagePath = `evidence/raw/visual/${imageHash}.png`;
    await writeFile(path.join(runDir, imagePath), bytes);
    frames.push({ schemaVersion: 1, kind: 'cardinal4_raw_frame', captureId: 'capture-1', rig: 'cardinal-4-snapshot-v1',
      identity, subjects: [UUID], controlledStateHash: HASH, sameFrame: false, view, frameIndex: i,
      renderFrame: tick + i, clientTick: tick, serverTick: tick, serverGameTime: tick, partialTick: 0,
      imageHash, imageBytes: bytes.length, artifactRole: 'RAW_SCENE_RGB', captureStage: 'AFTER_LEVEL_BEFORE_HAND_HUD',
      imagePath, captureDurationNanos: 100, camera: { position: [0,2,10], quaternion: [0,0,0,1], yaw: 0, pitch: 0,
        fov: 90, projection: 'PERSPECTIVE', matrixConvention: 'JOML_COLUMN_MAJOR_CAMERA_RELATIVE', projectionMatrix: [1,0,0,0,0,1,0,0,0,0,-1,-1,0,0,-.2,0], viewMatrix: [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1], viewport: [64,64] } });
  }
  const manifest = { schemaVersion: 1, kind: 'cardinal4_capture_manifest', captureId: 'capture-1', rig: 'cardinal-4-snapshot-v1',
    identity, subjects: [UUID], controlledStateHash: HASH, sameFrame: false,
    result: { status: 'COMPLETE', sameFrame: false, restoration: 'RESTORED',
      perturbations: ['SERVER_TICK_HOLD','CLIENT_PAUSE','CAMERA_TAKEOVER','RENDER_ELIGIBILITY_CHANGED'],
      invalidatedAssertions: ['behavior-1'], frames: frames.map(f => ({ view: f.view, status: 'PRESENT', renderFrame: f.renderFrame,
        imageHash: f.imageHash, observationHash: HASH })), gaps: [] }, frames,
    structuredState: { dimension: 'minecraft:overworld', gameTime: tick, arenaBounds: { min: [-8,0,-8], max: [8,16,8] },
      subjects: [{ uuid: UUID, position: [1,1,2], velocity: [.25,0,-.5], yaw: 0, pitch: 0, bounds: [.5,0,1.5,1.5,2,2.5] }] },
    renderFrameStart: tick, renderFrameEnd: tick+4, clientTickStart: tick, clientTickEnd: tick, barrierDurationMs: 100, restorationProof: { basis: 'MINECRAFT_API_READBACK',
      expected: {cameraUuid:'camera',cameraType:'FIRST_PERSON',hideGui:false,bob:true,fov:70,paused:false,mouseGrabbed:true,screen:'NONE',x:1,y:2,z:3,yaw:0,pitch:0},
      observed: {cameraUuid:'camera',cameraType:'FIRST_PERSON',hideGui:false,bob:true,fov:70,paused:false,mouseGrabbed:true,screen:'NONE',x:1,y:2,z:3,yaw:0,pitch:0}},
    runtimeAttestation: 'OWNER_GATE_REQUIRED_NOT_INFERRED_FROM_CAPTURE', visualVerdict: 'NOT_RUN',
    behaviorVerdict: 'INCONCLUSIVE_CAPTURE_PERTURBATION' };
  mutate(manifest);
  const sourceObservationId = 'obs:capture:1';
  await store.appendObservation({ observationId: sourceObservationId, processEpoch: identity.processEpoch, arenaEpoch: identity.arenaEpoch,
    resourceEpoch: 0, writerId: 'capture', writerSeq: 1, level: 'L3', lane: 'VISUAL_CAPTURE',
    observedAt: '2026-10-01T00:00:00.000Z', gameTime: tick, scope: { kind: 'EXPERIMENT', experimentId: identity.experimentId },
    source: { side: 'CLIENT', method: 'cardinal4_manifest' }, epistemicStatus: 'OBSERVED', completeness: { complete: true }, payload: manifest });
  return { store, sourceObservationId, requestBytes, manifest, raw, colors, runDir };
}
