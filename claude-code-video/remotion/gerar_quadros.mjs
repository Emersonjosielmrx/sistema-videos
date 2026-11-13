import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "path";

async function run() {
  console.log("Bundling...");
  const entry = path.resolve("src/videos/advance_novoestrela_20261101_162157/index.ts");
  const bundled = await bundle({
    entryPoint: entry,
  });

  const composition = await selectComposition({
    serveUrl: bundled,
    id: "Main",
  });

  const publicDir = "D:/claude-code-video/trabalhos/advance_novoestrela_20261101_162157/public";
  const quadrosDir = "D:/claude-code-video/trabalhos/advance_novoestrela_20261101_162157/quadros";

  const frames = [36, 210, 420, 600, 760];

  for (const frame of frames) {
    console.log(`Rendering frame ${frame}...`);
    const output = path.join(quadrosDir, `q_${frame}.png`);
    await renderStill({
      composition,
      serveUrl: bundled,
      output,
      frame,
      publicDir,
    });
    console.log(`Rendered frame ${frame} -> ${output}`);
  }

  console.log("ALL DONE!");
}

run().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
