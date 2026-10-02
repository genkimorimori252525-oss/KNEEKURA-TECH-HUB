const hash = 'a'.repeat(64);
export function identity() {
  return { debugSessionId: 'session', runId: 'run', runSnapshotId: 'snapshot', processEpoch: 1,
    experimentId: 'experiment', generation: 1, requestHash: hash, arenaId: 'arena',
    arenaEpoch: 0, arenaRevision: 1, baselineHash: hash };
}
export function frame(view = 'north', index = 0) {
  return { schemaVersion: 1, kind: 'cardinal4_raw_frame', captureId: 'capture-1',
    rig: 'cardinal-4-snapshot-v1', identity: identity(), subjects: ['00000000-0000-0000-0000-000000000001'],
    controlledStateHash: hash, sameFrame: false, view, frameIndex: index, renderFrame: 100 + index,
    clientTick: 10, serverTick: 20, serverGameTime: 30, partialTick: 0,
    imageHash: hash, imageBytes: 100, artifactRole: 'RAW_SCENE_RGB',
    captureStage: 'AFTER_LEVEL_BEFORE_HAND_HUD', imagePath: `evidence/raw/visual/${hash}.png`,
    captureDurationNanos: 100, camera: { position: [0, 1, -10], quaternion: [0, 0, 0, 1],
      yaw: 0, pitch: 0, fov: 70, projection: 'PERSPECTIVE', projectionMatrix: Array(16).fill(1), viewMatrix: Array(16).fill(1), matrixConvention: 'JOML_COLUMN_MAJOR_CAMERA_RELATIVE', viewport: [640, 480] } };
}
export function manifest() {
  const frames = ['north', 'east', 'south', 'west'].map(frame);
  return { schemaVersion: 1, kind: 'cardinal4_capture_manifest', captureId: 'capture-1', rig: 'cardinal-4-snapshot-v1',
    identity: identity(), subjects: frames[0].subjects, controlledStateHash: hash, sameFrame: false,
    result: { status: 'COMPLETE', sameFrame: false, restoration: 'RESTORED',
      perturbations: ['SERVER_TICK_HOLD', 'CLIENT_PAUSE', 'CAMERA_TAKEOVER', 'RENDER_ELIGIBILITY_CHANGED'],
      invalidatedAssertions: ['behavior-1'], frames: frames.map(f => ({ view: f.view, status: 'PRESENT',
        renderFrame: f.renderFrame, imageHash: hash, observationHash: hash })), gaps: [] },
    frames, structuredState: { dimension: 'minecraft:overworld', gameTime: 30, arenaBounds: { min: [0,0,0], max: [16,16,16] },
      subjects: [{ uuid: frames[0].subjects[0], position: [1,1,1], velocity: [0,0,0], yaw: 0, pitch: 0, bounds: [0,0,0,2,2,2] }] },
    renderFrameStart: 100, renderFrameEnd: 104, clientTickStart: 10, clientTickEnd: 10,
    barrierDurationMs: 100, restorationProof: { basis: 'MINECRAFT_API_READBACK',
      expected: {cameraUuid:'camera',cameraType:'FIRST_PERSON',hideGui:false,bob:true,fov:70,paused:false,mouseGrabbed:true,screen:'NONE',x:1,y:2,z:3,yaw:0,pitch:0},
      observed: {cameraUuid:'camera',cameraType:'FIRST_PERSON',hideGui:false,bob:true,fov:70,paused:false,mouseGrabbed:true,screen:'NONE',x:1,y:2,z:3,yaw:0,pitch:0}}, runtimeAttestation: 'OWNER_GATE_REQUIRED_NOT_INFERRED_FROM_CAPTURE',
    visualVerdict: 'NOT_RUN', behaviorVerdict: 'INCONCLUSIVE_CAPTURE_PERTURBATION' };
}
