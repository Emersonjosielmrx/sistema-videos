const { bundle } = require('@remotion/bundler');
const { renderStill, selectComposition } = require('@remotion/renderer');
const path = require('path');

async function main() {
  const entryPoint = path.resolve('src/videos/followupia_ia_20261116_052420/index.ts');
  const publicDir = path.resolve('trabalhos/followupia_ia_20261116_052420/public');
  const outputDir = path.resolve('trabalhos/followupia_ia_20261116_052420/quadros');

  console.log('Bundling...');
  const bundled = await bundle({
    entryPoint,
    publicDir,
  });

  console.log('Selecting composition...');
  const composition = await selectComposition({
    serveUrl: bundled,
    id: 'Main',
  });

  const frames = [260, 420, 490, 560, 760, 860, 910];

  for (const frame of frames) {
    const outputFile = path.join(outputDir, `q_${frame}.png`);
    console.log(`Rendering frame ${frame}...`);
    try {
      await renderStill({
        composition,
        serveUrl: bundled,
        output: outputFile,
        frame,
        logLevel: 'error',
        timeoutInMilliseconds: 120000,
      });
      console.log(`Rendered frame ${frame} successfully!`);
    } catch (e) {
      console.error(`Error rendering frame ${frame}:`, e.message);
    }
  }
  console.log('All stills rendered successfully!');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
