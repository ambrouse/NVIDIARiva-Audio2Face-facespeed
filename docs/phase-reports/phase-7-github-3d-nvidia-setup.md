# Phase 7 GitHub, 3D Viewer and NVIDIA Setup Report

Time: 2026-05-17

## Completed

- Created plan `plans/plan-real-nvidia-riva-a2f-3d-face-github.md`.
- Initialized git repository at project root and configured origin remote.
- Added `.gitignore`, `VERSION` and GitHub Actions CI.
- Added README following repository style guidance.
- Added NVIDIA host setup documentation.
- Extended `scripts/setup.sh` with NVIDIA-specific modes:
  - `--check-nvidia`
  - `--install-ngc`
  - `--install-riva`
  - `--start-riva`
  - `--check-riva`
  - `--check-a2f`
  - `--nvidia-full`
- Added browser 3D face preview through lazy-loaded Three.js component.

## Test results

- Backend/setup tests: 11 passed.
- Frontend tests: 1 passed.
- Frontend production build: passed.

## Known blocker

Real NVIDIA smoke testing was not completed on this Windows host. Pass-true criteria require a Linux NVIDIA host with GPU, Docker NVIDIA runtime, configured NGC CLI, Riva server and Audio2Face automation endpoint.

## Next required real test

Run on NVIDIA host:

```bash
./scripts/setup.sh --check-nvidia
./scripts/setup.sh --check-riva
./scripts/setup.sh --check-a2f
PIPELINE_MODE=nvidia python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

Then create a job from the dashboard and verify that Riva generates a real WAV and Audio2Face returns a real animation/result.
