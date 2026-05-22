# Changelog

## 0.3.0 - 2026-05-23

### Added

- Provider-backed Voice RAG product flow: PDF ingestion, Docling parse, embedding search, rerank, cited answer, Riva TTS, and 3D avatar playback.
- Commercial voice-first React UI with left icon navigation, hold-to-talk, chat history, avatar popup, model profile controls, face size/expression tuning, and replay-only voice playback.
- Release evidence package in `test/release-readiness-2026-05-23/`.
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
