# NVIDIA Host Setup

Time: 2026-05-22

## Requirements

- Linux host with NVIDIA GPU.
- NVIDIA driver visible through `nvidia-smi`.
- Docker Engine.
- NVIDIA Container Toolkit.
- NVIDIA NGC CLI.
- NGC account configured with `ngc config set`.
- NVIDIA Riva quickstart assets downloaded according to the Riva version you are licensed to use.
- NVIDIA Audio2Face-3D NIM access through NGC if using the target facial animation path.

## Safe preflight checks

Run these read-only checks before any NVIDIA download, container start, or smoke test:

```bash
bash scripts/setup.sh --check-ports
bash scripts/setup.sh --check-resources
bash scripts/setup.sh --check-gpu-light
bash scripts/setup.sh --check-docker-space
bash scripts/setup.sh --dry-run-nvidia-full
bash scripts/setup.sh --dry-run-containers
bash scripts/setup.sh --list-containers
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
export A2F_CONTAINER_IMAGE=nvcr.io/nim/nvidia/audio2face-3d:2.0
export CONTAINER_MEMORY_LIMIT=16g
export CONTAINER_CPU_LIMIT=8
export GPU_DEVICE_FLAG='--gpus device=0'
bash scripts/setup.sh --dry-run-containers
```

Current documentation findings:

- The fetched Riva quick-start page currently targets Jetson Thor / JetPack 7.0 and points x86 data-center users toward Riva NIM documentation. Do not assume an old x86 quickstart image/tag without verifying the exact supported path.
- The old `nvcr.io/nvidia/ace/audio2face:1.0.11` image is blocked on this RTX PRO 5000 Blackwell host.
- The current Audio2Face-3D NIM path is `nvcr.io/nim/nvidia/audio2face-3d:2.0`. Verify RTX PRO 5000 Blackwell with `nim_list_model_profiles`; if no pre-generated profile matches, use the documented local TensorRT generation path.
- Do not assume `A2F_PROCESS_PATH=/api/process-audio` is real. Audio2Face-3D NIM uses gRPC for audio input and blendshape output.

Real NVIDIA setup remains blocked until Riva model assets and the A2F-3D profile/API smoke are verified.

Rollback is scoped to project container names (`facespeed-riva`, `facespeed-audio2face`) and keeps cache/assets by default.

Stop only project-labeled running containers:

```bash
bash scripts/setup.sh --stop-containers
```

Default localhost ports:

```text
Backend API: 127.0.0.1:8020
Frontend:    127.0.0.1:6310
Riva gRPC:   127.0.0.1:50051
Audio2Face gRPC: 127.0.0.1:8040
Audio2Face HTTP: 127.0.0.1:8041
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

## Audio2Face-3D

Set these variables if your A2F service differs from defaults:

```bash
export A2F_HOST=127.0.0.1
export A2F_PORT=8040
export A2F_HTTP_PORT=8041
export A2F_HEALTH_PATH=/health
```

Then run the current project check:

```bash
./scripts/setup.sh --check-a2f
```

Check NIM profiles directly:

```bash
bash scripts/setup.sh --a2f-profiles
```

Start project-scoped A2F-3D NIM:

```bash
export NGC_API_KEY=<local-ngc-key>
bash scripts/setup.sh --start-a2f-nim
```

## Backend real mode

```env
PIPELINE_MODE=nvidia
RIVA_HOST=127.0.0.1
RIVA_PORT=50051
RIVA_SAMPLE_RATE_HZ=22050
A2F_HOST=127.0.0.1
A2F_PORT=8040
A2F_HTTP_PORT=8041
A2F_TRANSPORT=grpc
A2F_PROCESS_PATH=/api/process-audio
A2F_TIMEOUT_SECONDS=120
```

`A2F_PROCESS_PATH` is used only when `A2F_TRANSPORT=http`. The real A2F-3D path uses gRPC and stores `nvidia-audio2face-3d-v1` timeline JSON.

## Pass criteria

- `nvidia-smi` returns GPU details.
- Docker can access NVIDIA runtime.
- Riva gRPC port is reachable.
- Backend creates a real WAV from Riva TTS.
- Audio2Face-3D receives the WAV/audio stream and returns blendshape frames.
- Dashboard displays the 3D face viewer and pipeline result.
