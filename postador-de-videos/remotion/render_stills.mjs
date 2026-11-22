import path from 'path';
import { fileURLToPath } from 'url';
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition, openBrowser } from '@remotion/renderer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const id = 'agentesdeia_ia_20261121_222123';
const entryPoint = path.resolve(__dirname, `src/videos/${id}/index.ts`);
const publicDir = `D:/postador-de-videos/remotion/trabalhos/${id}/public`;
const quadrosDir = `D:/postador-de-videos/remotion/trabalhos/${id}/quadros`;

console.log('1. Bundling Remotion project with publicDir...');
const bundleLocation = await bundle({
  entryPoint,
  publicDir,
});
console.log('Bundle created at:', bundleLocation);

console.log('2. Selecting composition "Main"...');
const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: 'Main',
});
console.log('Composition details:', composition.width, 'x', composition.height, 'fps:', composition.fps, 'frames:', composition.durationInFrames);

console.log('3. Opening browser...');
const browser = await openBrowser('chrome');

// Quadros representativos: 20% e 80% de cada cena + o cartão final
// Cena 0 (0-163): 32, 80, 130
// Cena 1 (152-393): 200, 270, 350
// Cena 2 (383-596): 425, 490, 550
// Cena 3 (586-826): 634, 706, 780
// Cena 4 (816-935): 840, 880, 910
const frames = [32, 80, 130, 200, 270, 350, 425, 490, 550, 634, 706, 780, 840, 880, 910];

for (const f of frames) {
  const output = path.join(quadrosDir, `q_${String(f).padStart(3, '0')}.png`);
  console.log(`Rendering frame ${f} -> ${output}`);
  await renderStill({
    composition,
    serveUrl: bundleLocation,
    output,
    frame: f,
    puppeteerInstance: browser,
    logLevel: 'error',
  });
}

console.log('4. Closing browser...');
await browser.close();
console.log('ALL FRAMES RENDERED SUCCESSFULLY!');
