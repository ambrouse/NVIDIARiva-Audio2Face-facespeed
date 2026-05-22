# Phase 10: Browser Viseme 3D Speaking Model

Time: 2026-05-22

## Goal

Deliver the usable product path requested by the user: text input generates speech and the browser shows a 3D model speaking with that audio. The old ACE Audio2Face image remains blocked on this host, while the newer Audio2Face-3D NIM 2.0 path must be verified separately for RTX PRO 5000 Blackwell.

## Implementation

- Added browser artifact fields to completed jobs:
  - `audioUrl`
  - `animationUrl`
- Added safe artifact endpoints:
  - `/api/artifacts/audio/{job_id}.wav`
  - `/api/artifacts/animation/{job_id}.json`
- Changed mock TTS to write a valid RIFF WAV instead of placeholder bytes.
- Changed the mock/A2F fallback output to `browser-viseme-v1` animation JSON with `jawOpen`, `mouthWide` and `mouthSmile` frames.
- Updated the pipeline UI to show playable audio and animation artifact links.
- Updated `FaceViewer` to fetch the animation timeline, play generated audio and drive the procedural Three.js mouth/jaw while audio plays.

## Verification

Commands:

```bash
backend/.venv-linux/bin/python -m pytest backend tests
npm --prefix frontend test
npm --prefix frontend run build
bash -n scripts/setup.sh
```

Results:

- Backend/setup tests: 28 passed.
- Frontend tests: 3 passed.
- Frontend build: PASS with existing Three.js chunk-size warning.
- Setup syntax: PASS.

Manual/API smoke:

- `GET http://127.0.0.1:8020/health` returned `{"status":"ok"}`.
- `POST /api/jobs` completed and returned artifact URLs.
- `GET /api/artifacts/audio/<job>.wav` returned RIFF bytes.
- `GET /api/artifacts/animation/<job>.json` returned `browser-viseme-v1` with 52 frames in the smoke run.
- Frontend dev server responded at `http://127.0.0.1:6210/`.

## Current limitations

- The 3D model is still procedural, not a user-provided GLB/VRM avatar.
- Browser playback requires user interaction because autoplay is intentionally not forced.
- Real Riva remains separate: the Riva image is pulled, but its runtime needs a model repository/quickstart initialization.
- Real Audio2Face remains optional until `nvcr.io/nim/nvidia/audio2face-3d:2.0` is profile-checked on this RTX PRO 5000 Blackwell host and the backend has a gRPC client for its blendshape output.

## Status

PASS for text → valid WAV → animation JSON → browser 3D speaking face in mock/non-GPU mode.
