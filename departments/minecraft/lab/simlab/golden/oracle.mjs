import { createHash } from 'node:crypto';
import { lstat, mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { assertRenderFrameIR } from '../contracts/render-v1/validator.mjs';
import { decodePng, encodePngRgba } from './png.mjs';

export const GOLDEN_REPORT_SCHEMA = 'kneekura.golden-oracle-report';
export const GOLDEN_REPORT_VERSION = 1;

export class GoldenOracleError extends Error {
  constructor(message) {
    super(message);
    this.name = 'GoldenOracleError';
  }
}

function sha256(bytes) {
  return 'sha256:' + createHash('sha256').update(bytes).digest('hex');
}

async function readRegular(path, label) {
  const stat = await lstat(path);
  if (stat.isSymbolicLink()) throw new GoldenOracleError(label + ' must not be a symbolic link');
  if (!stat.isFile()) throw new GoldenOracleError(label + ' must be a regular file');
  return readFile(path);
}

function ratio(value, label) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) {
    throw new GoldenOracleError(label + ' must be a finite number in [0,1]');
  }
  return value;
}

function nonNegative(value, label) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) {
    throw new GoldenOracleError(label + ' must be a finite number >= 0');
  }
  return value;
}

function normalizeThresholds(input) {
  const src = input || {};
  return {
    identicalRatioMin: ratio(src.identicalRatioMin ?? 1, 'identicalRatioMin'),
    meanAbsoluteRgbErrorMax: nonNegative(src.meanAbsoluteRgbErrorMax ?? 0, 'meanAbsoluteRgbErrorMax'),
    meanAbsoluteAlphaErrorMax: nonNegative(src.meanAbsoluteAlphaErrorMax ?? 0, 'meanAbsoluteAlphaErrorMax'),
    maxRgbErrorMax: nonNegative(src.maxRgbErrorMax ?? 0, 'maxRgbErrorMax'),
    maxAlphaErrorMax: nonNegative(src.maxAlphaErrorMax ?? 0, 'maxAlphaErrorMax'),
    silhouetteMismatchRatioMax: ratio(src.silhouetteMismatchRatioMax ?? 0, 'silhouetteMismatchRatioMax'),
    alphaThreshold: Math.min(255, Math.floor(nonNegative(src.alphaThreshold ?? 0, 'alphaThreshold'))),
    diffAmplification: Math.max(1, nonNegative(src.diffAmplification ?? 8, 'diffAmplification')),
  };
}

function identityFromFrame(frame) {
  if (!frame) return null;
  assertRenderFrameIR(frame);
  return {
    runId: frame.runId,
    entityUuid: frame.entityUuid,
    renderSequence: frame.renderSequence,
    gameTime: frame.gameTime,
    partialTick: frame.partialTick,
    modelId: frame.modelId,
    packHash: frame.packHash,
    layoutHash: frame.layoutHash,
    source: frame.source,
  };
}

export function compareDecodedImages(golden, viewer, thresholds) {
  const t = normalizeThresholds(thresholds);
  if (golden.width !== viewer.width || golden.height !== viewer.height) {
    throw new GoldenOracleError(
      'image dimensions differ: golden=' + golden.width + 'x' + golden.height
      + ', viewer=' + viewer.width + 'x' + viewer.height,
    );
  }

  const totalPixels = golden.width * golden.height;
  let identicalPixels = 0;
  let changedPixels = 0;
  let rgbAbsSum = 0;
  let alphaAbsSum = 0;
  let maxRgbError = 0;
  let maxAlphaError = 0;
  let silhouetteMismatchPixels = 0;
  const diff = new Uint8Array(totalPixels * 4);

  for (let i = 0; i < totalPixels; i++) {
    const p = i * 4;
    const dr = Math.abs(golden.rgba[p] - viewer.rgba[p]);
    const dg = Math.abs(golden.rgba[p + 1] - viewer.rgba[p + 1]);
    const db = Math.abs(golden.rgba[p + 2] - viewer.rgba[p + 2]);
    const da = Math.abs(golden.rgba[p + 3] - viewer.rgba[p + 3]);
    const rgbMax = Math.max(dr, dg, db);
    const same = rgbMax === 0 && da === 0;

    if (same) identicalPixels++;
    else changedPixels++;

    rgbAbsSum += dr + dg + db;
    alphaAbsSum += da;
    if (rgbMax > maxRgbError) maxRgbError = rgbMax;
    if (da > maxAlphaError) maxAlphaError = da;

    const goldenSolid = golden.rgba[p + 3] > t.alphaThreshold;
    const viewerSolid = viewer.rgba[p + 3] > t.alphaThreshold;
    if (goldenSolid !== viewerSolid) silhouetteMismatchPixels++;

    if (same) {
      diff[p] = 0;
      diff[p + 1] = 0;
      diff[p + 2] = 0;
      diff[p + 3] = 0;
    } else {
      diff[p] = Math.min(255, Math.round(dr * t.diffAmplification));
      diff[p + 1] = Math.min(255, Math.round(dg * t.diffAmplification));
      diff[p + 2] = Math.min(255, Math.round(db * t.diffAmplification));
      diff[p + 3] = 255;
    }
  }

  const metrics = {
    width: golden.width,
    height: golden.height,
    totalPixels,
    identicalPixels,
    changedPixels,
    identicalRatio: identicalPixels / totalPixels,
    meanAbsoluteRgbError: rgbAbsSum / (totalPixels * 3),
    meanAbsoluteAlphaError: alphaAbsSum / totalPixels,
    maxRgbError,
    maxAlphaError,
    silhouetteMismatchPixels,
    silhouetteMismatchRatio: silhouetteMismatchPixels / totalPixels,
  };

  const failures = [];
  if (metrics.identicalRatio < t.identicalRatioMin) {
    failures.push('identicalRatio ' + metrics.identicalRatio + ' < ' + t.identicalRatioMin);
  }
  if (metrics.meanAbsoluteRgbError > t.meanAbsoluteRgbErrorMax) {
    failures.push('meanAbsoluteRgbError ' + metrics.meanAbsoluteRgbError + ' > ' + t.meanAbsoluteRgbErrorMax);
  }
  if (metrics.meanAbsoluteAlphaError > t.meanAbsoluteAlphaErrorMax) {
    failures.push('meanAbsoluteAlphaError ' + metrics.meanAbsoluteAlphaError + ' > ' + t.meanAbsoluteAlphaErrorMax);
  }
  if (metrics.maxRgbError > t.maxRgbErrorMax) {
    failures.push('maxRgbError ' + metrics.maxRgbError + ' > ' + t.maxRgbErrorMax);
  }
  if (metrics.maxAlphaError > t.maxAlphaErrorMax) {
    failures.push('maxAlphaError ' + metrics.maxAlphaError + ' > ' + t.maxAlphaErrorMax);
  }
  if (metrics.silhouetteMismatchRatio > t.silhouetteMismatchRatioMax) {
    failures.push(
      'silhouetteMismatchRatio ' + metrics.silhouetteMismatchRatio
      + ' > ' + t.silhouetteMismatchRatioMax,
    );
  }

  return {
    pass: failures.length === 0,
    failures,
    thresholds: t,
    metrics,
    diff,
  };
}

function reportMarkdown(report) {
  const m = report.metrics;
  const pct = (x) => (x * 100).toFixed(6) + '%';
  const lines = [
    '# KNEEKURA Golden Oracle Report',
    '',
    'Result: **' + (report.pass ? 'PASS' : 'FAIL') + '**',
    '',
    '| Metric | Value |',
    '| --- | ---: |',
    '| Image size | ' + m.width + ' x ' + m.height + ' |',
    '| Identical pixels | ' + m.identicalPixels + ' / ' + m.totalPixels + ' (' + pct(m.identicalRatio) + ') |',
    '| Changed pixels | ' + m.changedPixels + ' |',
    '| Mean absolute RGB error | ' + m.meanAbsoluteRgbError.toFixed(6) + ' / 255 |',
    '| Mean absolute alpha error | ' + m.meanAbsoluteAlphaError.toFixed(6) + ' / 255 |',
    '| Maximum RGB channel error | ' + m.maxRgbError + ' / 255 |',
    '| Maximum alpha error | ' + m.maxAlphaError + ' / 255 |',
    '| Silhouette mismatch | ' + m.silhouetteMismatchPixels + ' / ' + m.totalPixels
      + ' (' + pct(m.silhouetteMismatchRatio) + ') |',
    '',
  ];
  if (report.frameIdentity) {
    lines.push('## Frame identity', '', JSON.stringify(report.frameIdentity, null, 2), '');
  }
  if (report.failures.length) {
    lines.push('## Failed gates', '', ...report.failures.map((x) => '- ' + x), '');
  }
  lines.push(
    '## Artifacts',
    '',
    '- report.json: machine-readable metrics and thresholds',
    '- diff.png: amplified absolute per-channel difference; identical pixels are transparent',
    '- report.md: this summary',
    '',
  );
  return lines.join('\n');
}

export async function compareGoldenOracle(options) {
  const {
    goldenPngPath,
    viewerPngPath,
    frameJsonPath = null,
    outputDir,
    thresholds = {},
  } = options || {};

  if (!goldenPngPath || !viewerPngPath || !frameJsonPath || !outputDir) {
    throw new GoldenOracleError(
      'goldenPngPath, viewerPngPath, frameJsonPath, and outputDir are required',
    );
  }

  const [goldenBytes, viewerBytes] = await Promise.all([
    readRegular(resolve(goldenPngPath), 'golden PNG'),
    readRegular(resolve(viewerPngPath), 'viewer PNG'),
  ]);
  const golden = decodePng(goldenBytes);
  const viewer = decodePng(viewerBytes);

  const frameBytes = await readRegular(resolve(frameJsonPath), 'RenderFrame JSON');
  const frame = JSON.parse(frameBytes.toString('utf8'));
  const frameIdentity = identityFromFrame(frame);
  const frameHash = sha256(frameBytes);

  const comparison = compareDecodedImages(golden, viewer, thresholds);
  const report = {
    schema: GOLDEN_REPORT_SCHEMA,
    schemaVersion: GOLDEN_REPORT_VERSION,
    pass: comparison.pass,
    failures: comparison.failures,
    thresholds: comparison.thresholds,
    metrics: comparison.metrics,
    frameIdentity,
    inputs: {
      goldenPngSha256: sha256(goldenBytes),
      viewerPngSha256: sha256(viewerBytes),
      renderFrameJsonSha256: frameHash,
    },
  };

  const out = resolve(outputDir);
  await mkdir(out, { recursive: true });
  await Promise.all([
    writeFile(resolve(out, 'report.json'), JSON.stringify(report, null, 2) + '\n', 'utf8'),
    writeFile(
      resolve(out, 'diff.png'),
      encodePngRgba({ width: golden.width, height: golden.height, rgba: comparison.diff }),
    ),
    writeFile(resolve(out, 'report.md'), reportMarkdown(report) + '\n', 'utf8'),
  ]);

  return report;
}