# Phase 6 NVIDIA Integration Report

Time: 2026-05-17 local

## Completed

- Added configurable pipeline mode through `PIPELINE_MODE`.
- Added Riva TTS client abstraction with mock and NVIDIA Riva gRPC implementations.
- Added Audio2Face client abstraction with mock and HTTP API implementations.
- Updated job pipeline to use injected clients instead of hardcoded mock writes.
- Extended `.env.example` with Riva sample rate and Audio2Face endpoint path/timeout.

## How to enable real NVIDIA services

Set these values in `.env` on the NVIDIA host:

```env
PIPELINE_MODE=nvidia
RIVA_HOST=127.0.0.1
RIVA_PORT=50051
RIVA_SAMPLE_RATE_HZ=22050
A2F_HOST=127.0.0.1
A2F_PORT=8011
A2F_PROCESS_PATH=/api/process-audio
A2F_TIMEOUT_SECONDS=120
```

Install backend dependencies on the target host:

```bash
python -m pip install -r backend/requirements.txt
```

Then run:

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001
```

## Notes

- The Riva adapter expects NVIDIA Riva Python client packages and a reachable Riva TTS server.
- Audio2Face automation endpoint path is configurable because deployments differ between Omniverse/A2F service modes.
- Real smoke testing still requires a Linux NVIDIA host with Riva and Audio2Face running.
