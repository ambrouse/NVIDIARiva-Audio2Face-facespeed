# Changelog

## Unreleased - 2026-05-26

### Added

- Nginx single-port dev proxy on `127.0.0.1:6300`, managed by Docker Compose and `./setup.sh`.
- tmux runtime naming with `facespeed-riva-*` sessions for Docker, Riva TTS, Riva ASR, backend, and frontend.
- Real Postgres/Qdrant-backed RAG storage with provider URLs documented for Docling `8005`, embedding/rerank `8006`, and vLLM `8007`.
- Benchmark and smoke evidence under `tests/benchmarks/` and `tests/nginx-proxy/`.
- New README banner from the real app Sources popup showing 100 indexed PDFs.

### Changed

- README rebuilt as a Vietnamese docs hub with runtime, ports, architecture, flow, test reports, troubleshooting notes, and repo map.
- Voice chat spoken preview is limited with `VOICE_CHAT_TTS_MAX_CHARS=150` while preserving the full cited answer in chat text.
- Setup/run workflow now starts and stops project-owned runtime through `./setup.sh` and tmux, without separate `start.sh`/`stop.sh` wrappers.

### Verification

- `bash -n scripts/setup.sh`
- `docker compose config --quiet`
- `curl http://127.0.0.1:6300/api/rag/status`
- `POST http://127.0.0.1:6300/api/voice/chat`
- Playwright screenshot of Sources popup through nginx proxy.

## 0.3.0 - 2026-05-23

### Added

- Provider-backed Voice RAG product flow: PDF ingestion, Docling parse, embedding search, rerank, cited answer, Riva TTS, and 3D avatar playback.
- Commercial voice-first React UI with left icon navigation, hold-to-talk, chat history, avatar popup, model profile controls, face size/expression tuning, and replay-only voice playback.
- Release evidence package in `.cache/facespeed/evidence/release-readiness-2026-05-23/`.
- GIF demo banner generated from the real browser app.
- Root `LICENSE`, `CONTRIBUTING.md`, `CONTRIBUTORS.md`, `VERSION`, and release notes.
- Log cleanup workflow via `scripts/manage-logs.sh`.

### Changed

- Removed visible audio bar from the product surface; the latest RAG answer now autoplays and can be replayed with one icon.
- Consolidated duplicated evidence folders into a single release-readiness folder.
- Operations page now reports the provider-backed RAG main path instead of mock/container-manager status.

### Removed

- Unused browser model assets that failed visual QA: `a2f-james-v3.glb` and `head.fbx`.
- Duplicated/stale evidence folders and runtime job logs from source.

### Verification

- Frontend tests: `4 passed`.
- Frontend build: passed with Vite's non-fatal Three.js chunk-size warning.
- Backend tests: `39 passed`.
- Browser evidence: no console errors, no failed responses, no visible audio controls, one replay button, avatar morphs active.
