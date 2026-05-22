# Production End-User Evidence - 2026-05-22

This folder records the browser QA pass for the production-style FaceSpeed Studio rebuild.

## Runtime

- Frontend: `http://127.0.0.1:6310/`
- Backend: `http://127.0.0.1:8020`
- Browser: Playwright Chromium, 1440x980 desktop plus 390x900 mobile
- Test time: `2026-05-22T08:02:11.297Z`

## Result

- Browser title: `FaceSpeed Studio`
- Console errors: none
- Page errors: none
- HTTP 4xx/5xx responses: none
- Job id: `17309abe-6bd3-4d77-b91d-a6d21a46ca12`
- Animation engine: `browser-viseme-v2`
- Animation frames: `451`
- 3D model: ReadyPlayer ARKit GLB, `208` morph targets, `modelHasMorphs=true`
- Mouth drive: timeline-driven morphs

## Audio Report

- File: `generated-audio.wav`
- Format: RIFF/WAVE PCM
- Channels: `1`
- Sample rate: `22050 Hz`
- Duration: `7.512 s`
- RMS: `1949.23`
- Peak absolute sample: `17342`
- Non-silent: `true`

## Evidence Images

| File | Function/state proven |
| --- | --- |
| `screenshots/01-studio-ready.png` | Studio loads with real 3D avatar model and input controls. |
| `screenshots/02-avatar-speaking-output.png` | Generate speech creates audio, animation JSON, completed job state, and speaking avatar mouth pose. |
| `screenshots/03-operations-status.png` | Operations tab loads project service/container status and refreshes. |
| `screenshots/04-activity-logs-filtered.png` | Activity tab loads backend-worker logs and filters to `restart`. |
| `screenshots/05-setup-readiness.png` | Setup tab loads machine readiness checks. |
| `screenshots/06-mobile-studio.png` | Studio layout remains usable on a narrow mobile viewport. |

## Demo Asset

- `facespeed-demo.gif` was generated from a captured browser frame sequence.
- The README banner copy is `docs/assets/facespeed-demo.gif`.
- Intermediate GIF frames and raw WAV audio are local-only generated artifacts ignored by git; the tracked proof is the GIF, screenshots, `browser-report.json`, and `audio-report.json`.

## Hygiene

- Duplicate screenshot hash scan: no duplicate screenshot hashes.
- Raw browser report: `browser-report.json`.
- Audio metric report: `audio-report.json`.
