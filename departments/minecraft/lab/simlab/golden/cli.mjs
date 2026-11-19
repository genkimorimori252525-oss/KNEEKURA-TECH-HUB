import { readFile } from 'node:fs/promises';
import { compareGoldenOracle } from './oracle.mjs';

function usage() {
  console.error(
    'usage: node simlab/golden/cli.mjs <golden.png> <viewer.png> <frame.json> <output-dir> [thresholds.json]',
  );
}

const args = process.argv.slice(2);
if (args.length < 4 || args.length > 5) {
  usage();
  process.exitCode = 64;
} else {
  const [goldenPngPath, viewerPngPath, frameJsonPath, outputDir, thresholdsPath] = args;
  try {
    let thresholds = {};
    if (thresholdsPath) {
      thresholds = JSON.parse(await readFile(thresholdsPath, 'utf8'));
    }
    const report = await compareGoldenOracle({
      goldenPngPath,
      viewerPngPath,
      frameJsonPath,
      outputDir,
      thresholds,
    });
    console.log(JSON.stringify({
      pass: report.pass,
      metrics: report.metrics,
      failures: report.failures,
      outputDir,
    }, null, 2));
    if (!report.pass) process.exitCode = 2;
  } catch (error) {
    console.error(error && error.stack ? error.stack : String(error));
    process.exitCode = 1;
  }
}