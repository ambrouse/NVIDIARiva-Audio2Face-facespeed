# Phase 11: Real Audio2Face-3D gRPC Client

Time: 2026-05-22

## Goal

Replace the legacy Audio2Face HTTP placeholder with a real NVIDIA Audio2Face-3D NIM gRPC client path.

## Implementation

- Added `A2F_TRANSPORT=grpc` as the default NVIDIA A2F transport.
- Added a real `NvidiaAudio2FaceClient` gRPC path for `ProcessAudioStream`.
- Vendor-copied NVIDIA's generated `nvidia_ace` proto/stub package from the official Audio2Face-3D Samples `v2.0` wheel into `backend/nvidia_ace`.
- Kept legacy HTTP adapter behind `A2F_TRANSPORT=http`.
- Added A2F-3D output timeline JSON with `engine: nvidia-audio2face-3d-v1`.
- Added A2F-3D container helper commands:
  - `bash scripts/setup.sh --a2f-profiles`
  - `bash scripts/setup.sh --start-a2f-nim`
- Added separate external localhost ports:
  - gRPC: `127.0.0.1:8040` -> container `52000`
  - HTTP health: `127.0.0.1:8041` -> container `8000`
- Changed default target A2F NIM container name to `facespeed-audio2face-3d`.

## Verification

Commands:

```bash
backend/.venv-linux/bin/python -m pip install -r backend/requirements.txt
backend/.venv-linux/bin/python -m pytest backend tests
npm --prefix frontend test
npm --prefix frontend run build
bash -n scripts/setup.sh
bash scripts/setup.sh --dry-run-containers
bash scripts/setup.sh --start-a2f-nim
```

Results:

- Backend/setup tests: 31 passed.
- Frontend tests: 3 passed.
- Frontend build: PASS with existing Three.js chunk-size warning.
- Setup syntax: PASS.
- `nvidia_ace` vendored import: PASS.
- A2F-3D dry-run: PASS and prints project-scoped command.
- A2F-3D real start: BLOCKED by resource hard gate.
- A2F-3D image pull: BLOCKED by NVIDIA license acceptance.
- Frontend Playwright browser launch: BLOCKED by missing host library `libasound.so.2`; sudo install is unavailable in this session.
- Backend runtime artifact check in mock mode: PASS.

## Current blocker

`--start-a2f-nim` did not pull or start the NIM because memory commit headroom was below the 10% reserve threshold:

```text
memory commit headroom: about 1.6 GiB of 69.8 GiB
```

The GPU also had active processes and about 6.1 GiB free VRAM at the time of the check. This project should not start A2F-3D NIM until the shared server has more headroom or the user explicitly changes the resource gate.

A later direct image pull also failed before runtime:

```text
DENIED: Please accept license on the browser to be able to download
```

This means the NGC account must accept the Audio2Face-3D NIM license/EULA before the image can be pulled.

Frontend browser verification was attempted with Playwright, but Chromium could not start because the host is missing `libasound.so.2`. Installing `alsa-lib` requires sudo password on this host.

## Runtime artifact check

With backend/frontend dev servers running in mock mode, a real API job completed and produced browser artifacts:

```text
job state: completed
audio: RIFF/WAVE mono PCM-16, 22050 Hz, 9.36s
animation engine: browser-viseme-v1
animation frames: 281
jawOpen range: 0.15 -> 0.9
mouthWide range: 0.268 -> 0.605
```

This verifies the browser artifact contract, but it is not proof of NVIDIA Riva speech or A2F-3D blendshape inference.

## Next pass criteria

- Free enough memory/GPU headroom.
- Run `bash scripts/setup.sh --a2f-profiles`.
- Run `bash scripts/setup.sh --start-a2f-nim`.
- Confirm `bash scripts/setup.sh --check-a2f` reaches gRPC or HTTP health.
- Run a small `PIPELINE_MODE=nvidia` job and verify `engine: nvidia-audio2face-3d-v1` with non-empty blendshape frames.
