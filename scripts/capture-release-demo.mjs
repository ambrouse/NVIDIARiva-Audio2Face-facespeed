#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const requireFromFrontend = createRequire(path.join(repoRoot, 'frontend', 'package.json'));
const { chromium } = requireFromFrontend('playwright');

const outputDir = path.join(repoRoot, 'test', 'release-readiness-2026-05-23', 'demo');
const outputGif = path.join(outputDir, 'facespeed-release-demo.gif');
const readmeGif = path.join(repoRoot, 'docs', 'assets', 'voice-rag-avatar-demo.gif');
const framesDir = path.join(outputDir, '.frames');
const frontendUrl = process.env.FRONTEND_URL ?? 'http://127.0.0.1:6310/';
const question = process.env.DEMO_QUESTION ?? 'What does this document prove about FaceSpeed Voice RAG?';
const localBrowserLibs = path.join(repoRoot, '.local-libs', 'playwright');

if (fs.existsSync(localBrowserLibs)) {
  process.env.LD_LIBRARY_PATH = `${localBrowserLibs}${process.env.LD_LIBRARY_PATH ? `:${process.env.LD_LIBRARY_PATH}` : ''}`;
}

fs.mkdirSync(outputDir, { recursive: true });
fs.mkdirSync(path.dirname(readmeGif), { recursive: true });
fs.rmSync(framesDir, { recursive: true, force: true });
fs.mkdirSync(framesDir, { recursive: true });

const width = 960;
const height = 540;
const frameDelay = 140;
let frameIndex = 0;

function toolPython() {
  const candidates = [
    path.join(repoRoot, 'backend', '.venv-linux', 'bin', 'python'),
    path.join(repoRoot, 'backend', '.venv', 'Scripts', 'python.exe'),
    'python3',
    'python',
  ];
  for (const candidate of candidates) {
    const check = spawnSync(candidate, ['-c', 'import PIL'], { stdio: 'ignore' });
    if (check.status === 0) {
      return candidate;
    }
  }
  throw new Error('Pillow is required to encode the GIF. Install it in the backend venv: backend/.venv-linux/bin/python -m pip install pillow');
}

async function addFrame(page) {
  frameIndex += 1;
  const framePath = path.join(framesDir, `${String(frameIndex).padStart(4, '0')}.png`);
  await page.screenshot({ path: framePath, type: 'png', clip: { x: 0, y: 0, width, height } });
}

async function captureHold(page, frameCount, delay = frameDelay) {
  for (let index = 0; index < frameCount; index += 1) {
    await addFrame(page);
    await page.waitForTimeout(delay);
  }
}

function encodeGif() {
  const python = toolPython();
  const script = `
from pathlib import Path
from PIL import Image
frames_dir = Path(${JSON.stringify(framesDir)})
output = Path(${JSON.stringify(outputGif)})
frames = []
for frame_path in sorted(frames_dir.glob("*.png")):
    image = Image.open(frame_path).convert("RGB")
    frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=192))
if not frames:
    raise SystemExit("no frames captured")
frames[0].save(
    output,
    save_all=True,
    append_images=frames[1:],
    duration=${frameDelay},
    loop=0,
    optimize=True,
    disposal=2,
)
`;
  const result = spawnSync(python, ['-c', script], { cwd: repoRoot, encoding: 'utf8' });
  if (result.status !== 0) {
    throw new Error(`GIF encode failed: ${result.stderr || result.stdout}`);
  }
}

async function closeDialog(page) {
  const close = page.getByRole('button', { name: 'Close dialog' });
  if (await close.count()) {
    await close.click();
    await page.waitForTimeout(180);
  }
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--autoplay-policy=no-user-gesture-required', '--use-gl=swiftshader', '--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(90_000);

  await page.goto(frontendUrl, { waitUntil: 'networkidle' });
  await page.waitForSelector('.faceCanvas[data-model-loaded="true"]');
  await page.waitForTimeout(1200);
  await captureHold(page, 8);

  await page.getByRole('button', { name: 'Sources' }).click();
  await page.waitForTimeout(220);
  await captureHold(page, 6);
  await closeDialog(page);

  await page.getByRole('button', { name: 'Runtime' }).click();
  await page.waitForTimeout(220);
  await captureHold(page, 6);
  await closeDialog(page);

  await page.getByRole('button', { name: 'Avatar' }).click();
  await page.waitForTimeout(220);
  await captureHold(page, 6);
  await closeDialog(page);

  await page.getByRole('textbox', { name: 'Message' }).fill(question);
  await page.getByRole('button', { name: 'Send message' }).click();
  await page.waitForSelector('audio[src]', { state: 'attached' });
  await page.waitForSelector('button[aria-label="Replay latest answer"]');
  await page.waitForSelector('.chatMessage.assistant:not(.thinking)');
  await captureHold(page, 34);

  await page.getByRole('button', { name: 'Operations' }).click();
  await page.waitForTimeout(400);
  await captureHold(page, 8);

  await page.getByRole('button', { name: 'Setup' }).click();
  await page.waitForTimeout(400);
  await captureHold(page, 8);

  encodeGif();
  const bytes = fs.readFileSync(outputGif);
  fs.copyFileSync(outputGif, readmeGif);
  fs.rmSync(framesDir, { recursive: true, force: true });
  await browser.close();

  const sizeMb = bytes.length / (1024 * 1024);
  if (bytes.length >= 100 * 1024 * 1024) {
    throw new Error(`GIF is too large: ${sizeMb.toFixed(2)} MB`);
  }
  console.log(JSON.stringify({
    outputGif,
    readmeGif,
    frames: frameIndex,
    width,
    height,
    sizeMb: Number(sizeMb.toFixed(2)),
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
