const { bundle } = require('@remotion/bundler');
const { renderStill, selectComposition } = require('@remotion/renderer');
const path = require('path');

async function main() {
  const entryPoint = path.resolve('src/videos/inovareagenda_20261121_024218/index.ts');
  const publicDir = path.resolve('trabalhos/inovareagenda_20261121_024218/public');

  console.log('Bundling Remotion project with publicDir...');
  const bundleLocation = await bundle({ entryPoint, publicDir });
  console.log('Bundle complete. Selecting composition...');
  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: 'Main',
  });

  const frames = [31, 125, 192, 331, 424, 593, 687, 831, 892, 963];
  for (const frame of frames) {
    const output = path.resolve(`trabalhos/inovareagenda_20261121_024218/quadros/q_${frame}.png`);
    console.log(`Rendering frame ${frame}...`);
    await renderStill({
      composition,
      serveUrl: bundleLocation,
      output,
      frame,
      publicDir,
    });
    console.log(`Rendered frame ${frame} -> ${output}`);
  }
  console.log('All frames rendered successfully.');
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
