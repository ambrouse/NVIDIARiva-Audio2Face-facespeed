import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, vi } from 'vitest';
import { App } from '../src/App';
import { FaceViewer } from '../src/components/FaceViewer';

beforeEach(() => {
  Object.defineProperty(HTMLMediaElement.prototype, 'play', { configurable: true, value: vi.fn().mockResolvedValue(undefined) });
  Object.defineProperty(HTMLMediaElement.prototype, 'pause', { configurable: true, value: vi.fn() });
  Object.defineProperty(HTMLMediaElement.prototype, 'load', { configurable: true, value: vi.fn() });
  globalThis.fetch = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/api/rag/status')) {
      return Promise.resolve(new Response(JSON.stringify({
        asrAvailable: false,
        asrDetail: 'Riva ASR is disabled in the running Riva service; voice transcription is blocked.',
        documentCount: 0,
        chunkCount: 0,
        languages: ['en-US', 'vi-VN'],
        doclingBaseUrl: 'http://127.0.0.1:8005',
        embeddingBaseUrl: 'http://127.0.0.1:8006',
        parseProvider: 'docling',
        retrievalProvider: 'embedding-rerank',
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    }
    if (url.includes('/api/documents')) {
      return Promise.resolve(new Response(JSON.stringify([]), { status: 200, headers: { 'Content-Type': 'application/json' } }));
    }
    return Promise.resolve(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));
  }) as typeof fetch;
});

test('renders voice RAG navigation and main controls', async () => {
  render(<App />);
  expect(screen.getByRole('button', { name: 'Voice' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Operations' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Activity' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Setup' })).toBeInTheDocument();
  expect(screen.getByText('Voice RAG')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Hold to talk' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
  await waitFor(() => expect(screen.getByText('off')).toBeInTheDocument());
});

test('renders system safety commands and localhost ports', () => {
  render(<App />);
  fireEvent.click(screen.getByRole('button', { name: 'Setup' }));
  expect(screen.getByText('127.0.0.1:8020')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:6310')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:50051')).toBeInTheDocument();
  expect(screen.getByText('127.0.0.1:8040')).toBeInTheDocument();
  expect(screen.getByText('bash scripts/setup.sh --dry-run-nvidia-full')).toBeInTheDocument();
});

test('keeps RAG answer blocked until transcript and sources exist', () => {
  render(<App />);
  expect(screen.getByText('Hold to talk')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Send message' })).toBeDisabled();
});

test('uses autoplay audio with replay instead of a visible audio bar', () => {
  render(<FaceViewer isReady audioUrl="/api/artifacts/audio/latest.wav" />);
  expect(screen.getByRole('button', { name: 'Replay latest answer' })).toBeInTheDocument();
  expect(document.querySelector('audio')).not.toHaveAttribute('controls');
  expect(screen.queryByText('No speech rendered yet.')).not.toBeInTheDocument();
});
