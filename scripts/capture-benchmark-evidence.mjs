#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const requireFromFrontend = createRequire(path.join(repoRoot, 'frontend', 'package.json'));
const { chromium } = requireFromFrontend('playwright');

const stamp = process.env.BENCH_EVIDENCE_STAMP ?? new Date().toISOString().slice(0, 10);
const outputDir = process.env.BENCH_EVIDENCE_DIR
  ? path.resolve(process.env.BENCH_EVIDENCE_DIR)
  : path.join(repoRoot, 'tests', 'benchmarks', 'evidence', `rag-voice-${stamp}`);
const frontendUrl = process.env.FRONTEND_URL ?? 'http://127.0.0.1:6310/';
const backendUrl = (process.env.BACKEND_URL ?? 'http://127.0.0.1:6320').replace(/\/$/, '');
const question = process.env.BENCH_EVIDENCE_QUESTION ?? 'Summarize the strongest cited evidence from the indexed PDFs.';
const audioInput = process.env.BENCH_AUDIO_INPUT ? path.resolve(process.env.BENCH_AUDIO_INPUT) : path.join(outputDir, 'audio-input.wav');
const localBrowserLibs = path.join(repoRoot, '.local-libs', 'playwright');

if (fs.existsSync(localBrowserLibs)) {
  process.env.LD_LIBRARY_PATH = `${localBrowserLibs}${process.env.LD_LIBRARY_PATH ? `:${process.env.LD_LIBRARY_PATH}` : ''}`;
}

fs.mkdirSync(outputDir, { recursive: true });

function writeToneWav(destination) {
  const sampleRate = 16000;
  const seconds = 1;
  const sampleCount = sampleRate * seconds;
  const dataBytes = sampleCount * 2;
  const buffer = Buffer.alloc(44 + dataBytes);
  buffer.write('RIFF', 0);
  buffer.writeUInt32LE(36 + dataBytes, 4);
  buffer.write('WAVE', 8);
  buffer.write('fmt ', 12);
  buffer.writeUInt32LE(16, 16);
  buffer.writeUInt16LE(1, 20);
  buffer.writeUInt16LE(1, 22);
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * 2, 28);
  buffer.writeUInt16LE(2, 32);
  buffer.writeUInt16LE(16, 34);
  buffer.write('data', 36);
  buffer.writeUInt32LE(dataBytes, 40);
  for (let index = 0; index < sampleCount; index += 1) {
    const value = Math.sin((index / sampleRate) * Math.PI * 2 * 440) * 0.2;
    buffer.writeInt16LE(Math.round(value * 32767), 44 + index * 2);
  }
  fs.writeFileSync(destination, buffer);
}

async function download(page, urlOrPath, destination) {
  if (!urlOrPath) {
    return { ok: false, reason: 'missing url' };
  }
  const url = urlOrPath.startsWith('http') ? urlOrPath : `${backendUrl}${urlOrPath}`;
  const response = await page.request.get(url);
  if (!response.ok()) {
    return { ok: false, reason: `HTTP ${response.status()}` };
  }
  const body = await response.body();
  fs.writeFileSync(destination, body);
  return { ok: true, path: path.relative(repoRoot, destination), bytes: body.length };
}

async function main() {
  if (!fs.existsSync(audioInput)) {
    writeToneWav(audioInput);
  }

  const browser = await chromium.launch({
    headless: true,
    args: ['--autoplay-policy=no-user-gesture-required', '--use-gl=swiftshader', '--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 920 }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(180_000);

  const consoleErrors = [];
  const failedResponses = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text());
    }
  });
  page.on('response', (response) => {
    if (response.status() >= 400) {
      failedResponses.push({ url: response.url(), status: response.status() });
    }
  });

  await page.goto(frontendUrl, { waitUntil: 'networkidle' });
  await page.waitForSelector('.faceCanvas[data-model-loaded="true"]');
  await page.getByRole('textbox', { name: 'Message' }).fill(question);
  await page.getByRole('button', { name: 'Send message' }).click();
  await page.waitForSelector('.chatMessage.assistant:not(.thinking)');
  await page.waitForSelector('audio[src]', { state: 'attached' });
  await page.screenshot({ path: path.join(outputDir, 'frontend-answer.png'), fullPage: true });

  const audioUrl = await page.locator('audio').first().getAttribute('src');
  const outputAudio = await download(page, audioUrl, path.join(outputDir, 'audio-output.wav'));
  const report = {
    createdAt: new Date().toISOString(),
    frontendUrl,
    backendUrl,
    question,
    audioInput: {
      path: path.relative(repoRoot, audioInput),
      bytes: fs.statSync(audioInput).size,
      synthetic: !process.env.BENCH_AUDIO_INPUT,
    },
    outputAudio,
    screenshot: path.relative(repoRoot, path.join(outputDir, 'frontend-answer.png')),
    consoleErrors,
    failedResponses,
  };
  fs.writeFileSync(path.join(outputDir, 'browser-report.json'), JSON.stringify(report, null, 2));
  await browser.close();
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
