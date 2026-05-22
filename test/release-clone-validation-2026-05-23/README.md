# Release Clone Validation

Date: 2026-05-23

## Result

Pass after two release-readiness fixes. This evidence proves a fresh release snapshot can install dependencies, create provider-backed config, verify tests/build, start on isolated ports, and run the Voice RAG pipeline.

## Clone Under Test

- Snapshot path: `/tmp/facespeed-release-clone-validation-2026-05-23`
- Backend: `http://127.0.0.1:8120`
- Frontend: `http://127.0.0.1:6410`
- Snapshot excludes local `.env`, venvs, `node_modules`, `dist`, `outputs`, `storage`, runtime logs, and caches.

## Fixes Found By Clone Test

- `./setup.sh --setup` now creates `.env` from `.env.example` so a downloaded repo starts on the provider-backed main path: `SERVICE_MANAGER_MODE=docker`, `PIPELINE_MODE=riva`.
- Backend/frontend bootstrap now uses `setsid nohup env ...` so `./setup.sh --bootstrap` exits cleanly while the cloned app keeps running.
- Unit/integration tests now isolate `.env` with `_env_file=None` where needed, so release verification stays deterministic after setup creates `.env`.

## Evidence Map

| Path | Purpose |
| --- | --- |
| `commands/05-clean-snapshot-setup.txt` | Fresh install from clean snapshot; proves `.env` is created and Python/npm deps install. |
| `commands/15-clean-snapshot-verify.txt` | Clone verification after env/test isolation fixes. |
| `commands/27-bootstrap-after-setsid-fix.txt` | Final bootstrap run from clone. |
| `commands/28-health-after-setsid.json` | Backend health after bootstrap command returned. |
| `commands/29-processes-after-setsid.txt` | Backend/frontend still alive as detached PID 1 children. |
| `commands/30-clone-rag-status.json` | Clone RAG runtime status with Docling and embedding/rerank providers. |
| `commands/31-clone-rag-ingest.json` | PDF ingested through clone backend using Docling. |
| `commands/32-clone-voice-chat.json` | Voice RAG answer with citation and agent trace. |
| `commands/33-clone-audio.wav` | Riva WAV answer produced by clone backend. |
| `commands/34-clone-animation.json` | Avatar animation timeline produced by clone backend. |
| `commands/35-clone-artifact-summary.json` | Artifact summary: RIFF audio, citation count, animation frames. |
| `app/01-clone-home-ready.png` | Clone frontend loaded with 3D avatar model. |
| `app/02-clone-rag-answer.png` | Clone frontend shows cited RAG answer, replay-only audio UX, and no audio bar. |
| `browser-report.json` | Browser metrics and console/network result. |

## Final Metrics

- `./setup.sh --verify` from clone: frontend `4 passed`, backend/setup `41 passed`, production build passed.
- RAG answer: `reviewStatus=pass`, `citationCount=1`, source `clone-rag-evidence.pdf`.
- Audio artifact: RIFF WAV, `1,201,964` bytes.
- Animation artifact: `1,636` frames, engine `browser-viseme-v2`.
- Browser: `consoleErrors=0`, `pageErrors=0`, `failedResponses=0`, `audioControlsCount=0`, `replayButtonCount=1`, horizontal overflow `false`.

## Current Host Warnings

- NGC CLI is not installed on this host.
- Audio2Face-3D gRPC/HTTP runtime is not detected on `127.0.0.1:8040/8041`.
- GPU free VRAM and memory commit reserve are below the configured 10% threshold because other GPU services are already running.
