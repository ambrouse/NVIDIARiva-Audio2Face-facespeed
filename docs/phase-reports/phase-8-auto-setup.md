# Phase 8 Auto Setup Report

Time: 2026-05-17

## Completed

- Changed `scripts/setup.sh` default mode from check-only to `--auto`.
- Added platform detection for Linux, WSL Linux and Windows Git Bash.
- Added Docker GPU verification through CUDA test image.
- Added local backend/frontend dependency installation.
- Added clearer NGC/Riva setup flow with `NGC_RIVA_QUICKSTART_RESOURCE`.
- Kept NVIDIA account/license steps explicit and non-hardcoded.

## Important behavior

Running `./scripts/setup.sh` now performs:

1. System checks.
2. Local dependency install where possible.
3. NGC check.
4. Riva quickstart discovery/download attempt if configured.
5. Riva start attempt if quickstart scripts exist.
6. Riva and Audio2Face checks.

## Remaining manual requirements

- User must install/configure NGC CLI and run `ngc config set`.
- User must set `NGC_RIVA_QUICKSTART_RESOURCE` to the exact licensed NVIDIA Riva quickstart resource/version.
- User must install/start Audio2Face and expose a known automation/health endpoint.
