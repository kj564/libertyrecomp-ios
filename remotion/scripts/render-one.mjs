// Minimal, memory-safe renderer for ONE composition at low concurrency.
// Usage: node scripts/render-one.mjs <id> [--scale=1] [--frames=N] [--concurrency=1]
// Defaults: scale=1, concurrency=1, full duration. --frames=N renders only the first N frames
// (useful for a quick sample clip in memory-constrained environments).
import { bundle } from '@remotion/bundler';
import { selectComposition, renderMedia } from '@remotion/renderer';
import { readFileSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const id = args.find((a) => !a.startsWith('--'));
const scaleArg = args.find((a) => a.startsWith('--scale='));
const concArg = args.find((a) => a.startsWith('--concurrency='));
const framesArg = args.find((a) => a.startsWith('--frames='));
const SCALE = scaleArg ? Number(scaleArg.split('=')[1]) : 1;
const CONC = concArg ? Number(concArg.split('=')[1]) : 1;
const MAX_FRAMES = framesArg ? Number(framesArg.split('=')[1]) : null;

if (!id) {
  console.error('usage: node scripts/render-one.mjs <id> [--scale=1] [--concurrency=1] [--frames=N]');
  process.exit(1);
}

const outDir = path.join(root, 'out');
mkdirSync(outDir, { recursive: true });
const out = path.join(outDir, `${id}.mp4`);

console.log(`bundling (publicDir=../media)...`);
const t0 = Date.now();
const serveUrl = await bundle({
  entryPoint: path.join(root, 'src', 'index.ts'),
  publicDir: path.join(root, '..', 'media'),
});
console.log(`  bundled in ${((Date.now() - t0) / 1000).toFixed(1)}s`);

const composition = await selectComposition({ serveUrl, id });
const renderFrames = MAX_FRAMES
  ? Math.min(MAX_FRAMES, composition.durationInFrames)
  : composition.durationInFrames;
console.log(`rendering ${id}: ${composition.width}x${composition.height}@${composition.fps}fps, ` +
            `${renderFrames}/${composition.durationInFrames} frames, scale=${SCALE}, concurrency=${CONC}`);

const t1 = Date.now();
await renderMedia({
  serveUrl,
  composition,
  outputLocation: out,
  scale: SCALE,
  overwrite: true,
  codec: 'h264',
  pixelFormat: 'yuv420p',
  imageFormat: 'jpeg',
  crf: 18,
  concurrency: CONC,
  onProgress: ({ progress }) => process.stdout.write(`\r  ${id}: ${Math.round(progress * 100)}%   `),
  // render only the first N frames if --frames was given
  ...(MAX_FRAMES ? { durationInFrames: renderFrames } : {}),
});
process.stdout.write('\n');
console.log(`  rendered in ${((Date.now() - t1) / 1000).toFixed(1)}s`);
console.log(`  -> ${path.relative(root, out)} (${(readFileSync(out).length / 1024 / 1024).toFixed(1)}MB)`);
