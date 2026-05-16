# NVIDIA Host Setup

Time: 2026-05-17

## Requirements

- Linux host with NVIDIA GPU.
- NVIDIA driver visible through `nvidia-smi`.
- Docker Engine.
- NVIDIA Container Toolkit.
- NVIDIA NGC CLI.
- NGC account configured with `ngc config set`.
- NVIDIA Riva quickstart assets downloaded according to the Riva version you are licensed to use.
- NVIDIA Audio2Face installed and running with an automation/API endpoint.

## Checks

```bash
./scripts/setup.sh --check-nvidia
```

## Riva

```bash
./scripts/setup.sh --install-ngc
ngc config set
./scripts/setup.sh --install-riva
./scripts/setup.sh --start-riva
./scripts/setup.sh --check-riva
```

`--install-riva` expects Riva quickstart assets in `RIVA_QUICKSTART_DIR` or `./riva_quickstart`. The script does not hardcode NGC org/team/version or credentials.

## Audio2Face

Set these variables if your A2F service differs from defaults:

```bash
export A2F_HOST=127.0.0.1
export A2F_PORT=8011
export A2F_HEALTH_PATH=/health
```

Then run:

```bash
./scripts/setup.sh --check-a2f
```

## Backend real mode

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

## Pass criteria

- `nvidia-smi` returns GPU details.
- Docker can access NVIDIA runtime.
- Riva gRPC port is reachable.
- Backend creates a real WAV from Riva TTS.
- Audio2Face receives the WAV and returns a result.
- Dashboard displays the 3D face viewer and pipeline result.
