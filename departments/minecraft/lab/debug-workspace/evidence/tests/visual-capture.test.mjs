import test from 'node:test';
import assert from 'node:assert/strict';
import { validateVisualManifest, validateRawFrame } from '../visual-capture.mjs';
import { identity, frame, manifest } from './visual-capture-fixtures.mjs';
export { identity, frame, manifest };
test('four sequential raw frames retain exact identity and explicit perturbation', () => {
  assert.equal(validateVisualManifest(manifest()).result.status, 'COMPLETE');
});
for (const fault of ['stale', 'sameFrame', 'duplicate', 'tick', 'projection', 'path', 'restoration', 'missing', 'unknown']) {
  test(`reject false capture completeness: ${fault}`, () => {
    const m = manifest();
    if (fault === 'stale') m.frames[1].identity.arenaRevision++;
    if (fault === 'sameFrame') m.sameFrame = true;
    if (fault === 'duplicate') m.frames[1].renderFrame = m.frames[0].renderFrame;
    if (fault === 'tick') m.frames[1].serverGameTime++;
    if (fault === 'projection') m.frames[1].camera.fov = Infinity;
    if (fault === 'path') m.frames[1].imagePath = '/tmp/private';
    if (fault === 'restoration') m.result.restoration = 'UNKNOWN';
    if (fault === 'missing') m.frames.pop();
    if (fault === 'unknown') m.script = 'anything';
    assert.throws(() => validateVisualManifest(m));
  });
}
test('missing and uncertain frames remain explicit historical partial evidence', () => {
  const m = manifest(); m.result.status = 'PARTIAL'; m.result.gaps = ['DEADLINE_EXPIRED'];
  m.frames = m.frames.slice(0, 1);
  m.result.frames = m.result.frames.map((f, i) => i ?
    { view: f.view, status: 'MISSING', renderFrame: null, imageHash: null, observationHash: null } : f);
  assert.equal(validateVisualManifest(m).result.frames[1].status, 'MISSING');
});
test('raw frame cannot claim derived annotation or gameplay pass', () => {
  const f = frame(); f.artifactRole = 'DERIVED_ANNOTATED_FRAME';
  assert.throws(() => validateRawFrame(f));
});

for (const fault of ['uuid', 'bounds', 'time', 'extra']) test(`structured facts fail closed: ${fault}`, () => {
  const m = manifest();
  if (fault === 'uuid') m.structuredState.subjects[0].uuid = 'foreign';
  if (fault === 'bounds') m.structuredState.arenaBounds.max[0] = 100;
  if (fault === 'time') m.structuredState.gameTime++;
  if (fault === 'extra') m.structuredState.inferredPath = [];
  assert.throws(() => validateVisualManifest(m));
});

test('restoration requires actual unpaused matching presentation readback', () => {
  const m = manifest(); m.restorationProof.observed.paused = true;
  assert.throws(() => validateVisualManifest(m));
});

test('raw image reader checks full PNG framing and content, not just dimensions', async t => {
  const { mkdtemp, mkdir, writeFile, rm } = await import('node:fs/promises');
  const { tmpdir } = await import('node:os'); const path = await import('node:path');
  const { createHash } = await import('node:crypto');
  const { encodePngRgba } = await import('../../../simlab/golden/png.mjs');
  const { readRawVisualImage } = await import('../visual-capture.mjs');
  const root = await mkdtemp(path.join(tmpdir(), 'raw-visual-')); t.after(() => rm(root, { recursive: true, force: true }));
  const dir = path.join(root, 'evidence', 'raw', 'visual'); await mkdir(dir, { recursive: true });
  const png = encodePngRgba({ width: 64, height: 64, rgba: Buffer.alloc(64 * 64 * 4) });
  const f = frame(); f.camera.viewport = [64, 64]; f.imageHash = createHash('sha256').update(png).digest('hex');
  f.imageBytes = png.length; f.imagePath = `evidence/raw/visual/${f.imageHash}.png`;
  await writeFile(path.join(root, f.imagePath), png); assert.deepEqual(await readRawVisualImage(root, f), png);
  const bad = Buffer.concat([png, Buffer.from('extra')]); f.imageHash = createHash('sha256').update(bad).digest('hex');
  f.imageBytes = bad.length; f.imagePath = `evidence/raw/visual/${f.imageHash}.png`;
  await writeFile(path.join(root, f.imagePath), bad); await assert.rejects(readRawVisualImage(root, f));
});

test('process epoch follows Java positive int contract independently of experiment generation', () => {
  const m = manifest(); m.identity.processEpoch = 2147483647;
  m.frames.forEach(f => { f.identity.processEpoch = 2147483647; });
  assert.equal(validateVisualManifest(m).identity.processEpoch, 2147483647);
});
