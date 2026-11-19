import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { compareBoundGoldenOracle } from '../golden/bound-oracle.mjs';
import { renderBoundGoldenFrame } from '../viewer/headless-final-vertex.mjs';

const args = process.argv.slice(2);
if (args.length !== 5) {
  console.error(
    'usage: node simlab/golden/render-and-compare.mjs '
    + '<capture-dir> <pack-dir> <frame.json> <viewer.png> <report-dir>',
  );
  process.exitCode = 64;
} else {
  const [captureDir, packDir, frameJsonPath, viewerPngPath, reportDir] = args;
  try {
    const out = resolve(reportDir);
    await mkdir(out, { recursive: true });
    const render = await renderBoundGoldenFrame({
      captureDir,
      packDir,
      frameJsonPath,
      outputPngPath: viewerPngPath,
      metadataPath: resolve(out, 'viewer-render.json'),
    });
    const comparison = await compareBoundGoldenOracle({
      captureDir,
      viewerPngPath,
      frameJsonPath,
      outputDir: out,
    });
    const pipelineReport = {
      schema: 'kneekura.bound-pixel-parity-pipeline',
      schemaVersion: 1,
      pass: comparison.oracle.pass,
      identity: comparison.binding.identity,
      render: render.metadata,
      oracle: {
        metrics: comparison.oracle.metrics,
        failures: comparison.oracle.failures,
      },
    };
    await writeFile(
      resolve(out, 'pipeline.json'),
      JSON.stringify(pipelineReport, null, 2) + '\n',
      'utf8',
    );
    console.log(JSON.stringify({
      pass: pipelineReport.pass,
      identity: pipelineReport.identity,
      gl: render.metadata.browser.gl,
      metrics: comparison.oracle.metrics,
      failures: comparison.oracle.failures,
      reportDir: out,
    }, null, 2));
    if (!pipelineReport.pass) process.exitCode = 2;
  } catch (error) {
    console.error(error?.stack ?? String(error));
    process.exitCode = 1;
  }
}
