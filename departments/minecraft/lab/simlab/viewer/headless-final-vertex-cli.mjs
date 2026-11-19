import { renderBoundGoldenFrame } from './headless-final-vertex.mjs';

const args = process.argv.slice(2);
if (args.length < 4 || args.length > 5) {
  console.error(
    'usage: node simlab/viewer/headless-final-vertex-cli.mjs '
    + '<capture-dir> <pack-dir> <frame.json> <viewer.png> [viewer-render.json]',
  );
  process.exitCode = 64;
} else {
  const [captureDir, packDir, frameJsonPath, outputPngPath, metadataPath] = args;
  try {
    const result = await renderBoundGoldenFrame({
      captureDir,
      packDir,
      frameJsonPath,
      outputPngPath,
      ...(metadataPath ? { metadataPath } : {}),
    });
    console.log(JSON.stringify({
      outputPngPath,
      metadataPath: metadataPath || outputPngPath + '.json',
      identity: result.metadata.identity,
      gl: result.metadata.browser.gl,
      viewerPngSha256: result.metadata.output.viewerPngSha256,
    }, null, 2));
  } catch (error) {
    console.error(error?.stack ?? String(error));
    process.exitCode = 1;
  }
}
