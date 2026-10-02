import assert from 'node:assert/strict';
import { mkdtemp, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { decodePng, encodePngRgba } from '../png.mjs';
import { compareGoldenOracle, GoldenOracleError } from '../oracle.mjs';
async function symlinkOrSkip(t, target, linkPath) {
  try {
    await symlink(target, linkPath);
    return true;
  } catch (error) {
    if (process.platform === 'win32' &&
        (error?.code === 'EPERM' || error?.code === 'EACCES')) {
      t.skip(
        'Windows runner cannot create symbolic links; symlink security check is not executable in this environment'
      );
      return false;
    }
    throw error;
  }
}


function rgba(pixels) {
  return Uint8Array.from(pixels.flat());
}

async function setupPair(goldenPixels, viewerPixels, width = 2, height = 2) {
  const dir = await mkdtemp(join(tmpdir(), 'kneekura-golden-'));
  const golden = join(dir, 'golden.png');
  const viewer = join(dir, 'viewer.png');
  const frame = join(dir, 'frame.json');
  const out = join(dir, 'out');

  await writeFile(golden, encodePngRgba({ width, height, rgba: rgba(goldenPixels) }));
  await writeFile(viewer, encodePngRgba({ width, height, rgba: rgba(viewerPixels) }));
  const frameFixture = await readFile('simlab/contracts/render-v1/fixtures/render-frame.valid.json');
  await writeFile(frame, frameFixture);

  return { dir, golden, viewer, frame, out };
}

async function cleanup(state) {
  await rm(state.dir, { recursive: true, force: true });
}

const BASE = [
  [10, 20, 30, 255],
  [40, 50, 60, 255],
  [70, 80, 90, 0],
  [100, 110, 120, 255],
];

test('PNG codec round-trips deterministic RGBA fixtures', () => {
  const bytes = encodePngRgba({ width: 2, height: 2, rgba: rgba(BASE) });
  const decoded = decodePng(bytes);
  assert.equal(decoded.width, 2);
  assert.equal(decoded.height, 2);
  assert.deepEqual([...decoded.rgba], [...rgba(BASE)]);
});

test('exact golden and viewer images pass strict oracle gates', async () => {
  const state = await setupPair(BASE, BASE);
  try {
    const report = await compareGoldenOracle({
      goldenPngPath: state.golden,
      viewerPngPath: state.viewer,
      frameJsonPath: state.frame,
      outputDir: state.out,
    });
    assert.equal(report.pass, true);
    assert.equal(report.metrics.identicalPixels, 4);
    assert.equal(report.metrics.identicalRatio, 1);
    assert.equal(report.metrics.meanAbsoluteRgbError, 0);
    assert.equal(report.metrics.maxRgbError, 0);
    assert.equal(report.metrics.silhouetteMismatchPixels, 0);
    assert.equal(report.frameIdentity.modelId, 'test:reimu');
    assert.match(report.inputs.goldenPngSha256, /^sha256:[0-9a-f]{64}$/);

    const reportJson = JSON.parse(await readFile(join(state.out, 'report.json'), 'utf8'));
    assert.equal(reportJson.pass, true);
    const diff = decodePng(await readFile(join(state.out, 'diff.png')));
    assert.ok([...diff.rgba].every((x) => x === 0));
    assert.match(await readFile(join(state.out, 'report.md'), 'utf8'), /Result: \*\*PASS\*\*/);
  } finally {
    await cleanup(state);
  }
});

test('one RGB error fails strict oracle and produces a visible diff pixel', async () => {
  const changed = BASE.map((p) => [...p]);
  changed[1][0] += 5;
  const state = await setupPair(BASE, changed);
  try {
    const report = await compareGoldenOracle({
      goldenPngPath: state.golden,
      viewerPngPath: state.viewer,
      frameJsonPath: state.frame,
      outputDir: state.out,
    });
    assert.equal(report.pass, false);
    assert.equal(report.metrics.identicalPixels, 3);
    assert.equal(report.metrics.changedPixels, 1);
    assert.equal(report.metrics.maxRgbError, 5);
    assert.equal(report.metrics.meanAbsoluteRgbError, 5 / 12);
    assert.ok(report.failures.some((x) => x.includes('identicalRatio')));
    assert.ok(report.failures.some((x) => x.includes('maxRgbError')));

    const diff = decodePng(await readFile(join(state.out, 'diff.png')));
    const p = 1 * 4;
    assert.equal(diff.rgba[p], 40);
    assert.equal(diff.rgba[p + 3], 255);
  } finally {
    await cleanup(state);
  }
});

test('alpha occupancy mismatch is reported as silhouette mismatch', async () => {
  const changed = BASE.map((p) => [...p]);
  changed[2][3] = 255;
  const state = await setupPair(BASE, changed);
  try {
    const report = await compareGoldenOracle({
      goldenPngPath: state.golden,
      viewerPngPath: state.viewer,
      frameJsonPath: state.frame,
      outputDir: state.out,
    });
    assert.equal(report.pass, false);
    assert.equal(report.metrics.silhouetteMismatchPixels, 1);
    assert.equal(report.metrics.silhouetteMismatchRatio, 0.25);
    assert.equal(report.metrics.maxAlphaError, 255);
  } finally {
    await cleanup(state);
  }
});

test('explicit tolerances can pass a known small raster difference without hiding metrics', async () => {
  const changed = BASE.map((p) => [...p]);
  changed[0][2] += 1;
  const state = await setupPair(BASE, changed);
  try {
    const report = await compareGoldenOracle({
      goldenPngPath: state.golden,
      viewerPngPath: state.viewer,
      frameJsonPath: state.frame,
      outputDir: state.out,
      thresholds: {
        identicalRatioMin: 0.75,
        meanAbsoluteRgbErrorMax: 1,
        maxRgbErrorMax: 1,
      },
    });
    assert.equal(report.pass, true);
    assert.equal(report.metrics.changedPixels, 1);
    assert.equal(report.metrics.maxRgbError, 1);
  } finally {
    await cleanup(state);
  }
});

test('dimension mismatch fails instead of rescaling either image', async () => {
  const state = await setupPair(BASE, BASE);
  try {
    await writeFile(
      state.viewer,
      encodePngRgba({ width: 1, height: 1, rgba: rgba([[10, 20, 30, 255]]) }),
    );
    await assert.rejects(
      compareGoldenOracle({
        goldenPngPath: state.golden,
        viewerPngPath: state.viewer,
        frameJsonPath: state.frame,
        outputDir: state.out,
      }),
      (error) => error instanceof GoldenOracleError && /dimensions differ/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('symlinked image inputs are rejected', async (t) => {
  const state = await setupPair(BASE, BASE);
  try {
    const target = join(state.dir, 'target.png');
    await writeFile(target, await readFile(state.golden));
    await rm(state.golden);
    if (!(await symlinkOrSkip(t, target, state.golden))) {
      return;
    }
    await assert.rejects(
      compareGoldenOracle({
        goldenPngPath: state.golden,
        viewerPngPath: state.viewer,
        frameJsonPath: state.frame,
        outputDir: state.out,
      }),
      (error) => error instanceof GoldenOracleError && /symbolic link/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});

test('missing RenderFrame metadata is rejected for evidence-grade reports', async () => {
  const state = await setupPair(BASE, BASE);
  try {
    await assert.rejects(
      compareGoldenOracle({
        goldenPngPath: state.golden,
        viewerPngPath: state.viewer,
        outputDir: state.out,
      }),
      (error) => error instanceof GoldenOracleError && /frameJsonPath/.test(error.message),
    );
  } finally {
    await cleanup(state);
  }
});