import { readFile } from 'node:fs/promises';
import { compareBoundGoldenOracle } from './bound-oracle.mjs';

const args = process.argv.slice(2);
if (args.length < 4 || args.length > 5) {
  console.error(
    'usage: node simlab/golden/bound-cli.mjs <capture-dir> <viewer.png> <frame.json> <output-dir> [thresholds.json]',
  );
  process.exitCode = 64;
} else {
  const [captureDir, viewerPngPath, frameJsonPath, outputDir, thresholdsPath] = args;
  try {
    const thresholds = thresholdsPath ? JSON.parse(await readFile(thresholdsPath, 'utf8')) : {};
    const { oracle, binding } = await compareBoundGoldenOracle({
      captureDir, viewerPngPath, frameJsonPath, outputDir, thresholds,
    });
    console.log(JSON.stringify({
      pass: oracle.pass,
      metrics: oracle.metrics,
      failures: oracle.failures,
      binding: binding.identity,
      outputDir,
    }, null, 2));
    if (!oracle.pass) process.exitCode = 2;
  } catch (error) {
    console.error(error?.stack ?? String(error));
    process.exitCode = 1;
  }
}
