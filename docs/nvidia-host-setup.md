# NVIDIA Host Setup

Time: 2026-05-20

## Requirements

- Linux host with NVIDIA GPU.
- NVIDIA driver visible through `nvidia-smi`.
- Docker Engine.
- NVIDIA Container Toolkit.
- NVIDIA NGC CLI.
- NGC account configured with `ngc config set`.
- NVIDIA Riva quickstart assets downloaded according to the Riva version you are licensed to use.
- NVIDIA Audio2Face installed and running with an automation/API endpoint.

## Safe preflight checks

Run these read-only checks before any NVIDIA download, container start, or smoke test:

```bash
bash scripts/setup.sh --check-ports
bash scripts/setup.sh --check-resources
bash scripts/setup.sh --check-gpu-light
bash scripts/setup.sh --check-docker-space
bash scripts/setup.sh --dry-run-nvidia-full
bash scripts/setup.sh --dry-run-containers
```

The preflight checks are allowed to inspect ports, RAM, memory commit headroom, disk, GPU/VRAM, current GPU processes and Docker disk usage. They must not kill processes, free ports, prune Docker resources, download NVIDIA assets, or start containers.

`--dry-run-containers` prints project-scoped Docker pull/run/rollback commands only. It does not execute them. All project containers must use:

```text
name prefix: facespeed-
label: com.facespeed.project=NVIDIARiva-Audio2Face-facespeed
bind: 127.0.0.1 only
restart policy: no
```

Set image names only after verifying the official NVIDIA image/tag and license/API requirements:

```bash
export RIVA_CONTAINER_IMAGE=<verified-riva-image>
export A2F_CONTAINER_IMAGE=<verified-audio2face-image>
export CONTAINER_MEMORY_LIMIT=16g
export CONTAINER_CPU_LIMIT=8
export GPU_DEVICE_FLAG='--gpus device=0'
bash scripts/setup.sh --dry-run-containers
```

Rollback is scoped to project container names (`facespeed-riva`, `facespeed-audio2face`) and keeps cache/assets by default.

Default localhost ports:

```text
Backend API: 127.0.0.1:8020
Frontend:    127.0.0.1:6210
Riva gRPC:   127.0.0.1:50100
Audio2Face:  127.0.0.1:8040
```

If any target port is busy, stop and choose a new port with the user. Do not kill the owner process.

Hard gates for heavy work:

- RAM available must stay above 10%.
- Memory commit headroom must stay above 10%.
- Disk free must stay above 10%.
- GPU free VRAM must stay above 10%.
- Existing GPU processes are treated as important and must not be stopped.
- Docker cleanup is limited to stopped/unused resources after explicit confirmation.

## Checks

```bash
bash scripts/setup.sh --check-nvidia
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
export A2F_PORT=8040
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
RIVA_PORT=50100
RIVA_SAMPLE_RATE_HZ=22050
A2F_HOST=127.0.0.1
A2F_PORT=8040
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
