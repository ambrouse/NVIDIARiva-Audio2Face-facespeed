# Troubleshooting: Audio2Face / Audio2Face-3D

Time: 2026-05-22

## Current decision

The old container `nvcr.io/nvidia/ace/audio2face:1.0.11` should not be the target path for this host. It was pulled and start-tested earlier, but exited on the local NVIDIA RTX PRO 5000 Blackwell machine.

The current path to verify is NVIDIA Audio2Face-3D NIM:

```text
nvcr.io/nim/nvidia/audio2face-3d:2.0
```

This keeps the project aligned with ready NVIDIA inference instead of building a facial animation model from scratch.

## What A2F-3D provides

Audio2Face-3D is an animation-data service. It takes audio through gRPC and returns timed blendshape values. It does not provide a finished 3D character by itself.

For a product-quality result, pair it with one of these:

| Asset path | Fit |
|---|---|
| Unreal MetaHuman + NVIDIA ACE plugin | Best high-quality 3D runtime path |
| ARKit-compatible FBX/GLB avatar | Good browser/native path if blendshape names map cleanly |
| Existing local FBX with added/verified blendshapes | Practical if the asset can be rigged correctly |
| Browser ARKit viseme timeline | Current release path for Riva voice playback |

## Blackwell notes

NVIDIA's current Audio2Face-3D NIM docs list pre-generated profiles for several GPUs, including RTX 5080, RTX 5090, RTX PRO 6000 Blackwell, and B200. The local GPU is:

```text
NVIDIA RTX PRO 5000 Blackwell, driver 590.48.01, 48935 MiB VRAM
```

RTX PRO 5000 Blackwell is not listed by exact name in the current profile table. The safe sequence is:

1. Run profile listing on the host.
2. Try automatic profile selection.
3. If no compatible pre-generated profile matches, generate TensorRT engines locally with the documented `NIM_DISABLE_MODEL_DOWNLOAD=true` path.
4. Run a small backend job with `PIPELINE_MODE=nvidia` and `A2F_TRANSPORT=grpc`.

Official references:

- NVIDIA Audio2Face-3D Getting Started: https://docs.nvidia.com/ace/audio2face-3d-microservice/latest/text/getting-started/getting-started.html
- NVIDIA Audio2Face-3D Support Matrix: https://docs.nvidia.com/ace/audio2face-3d-microservice/latest/text/support-matrix.html
- NVIDIA Audio2Face-3D Microservice architecture: https://docs.nvidia.com/ace/audio2face-3d-microservice/latest/text/architecture/audio2face-ms.html

## Safe verification commands

List project containers:

```bash
bash scripts/setup.sh --list-containers
```

Stop only running project-labeled containers:

```bash
bash scripts/setup.sh --stop-containers
```

Check available A2F-3D model profiles:

```bash
docker run -it --rm --network=host --gpus all \
  --entrypoint nim_list_model_profiles \
  nvcr.io/nim/nvidia/audio2face-3d:2.0
```

Project helper:

```bash
bash scripts/setup.sh --a2f-profiles
```

Try automatic profile selection:

```bash
docker run -it --rm --network=host --gpus all \
  -e NGC_API_KEY=$NGC_API_KEY \
  nvcr.io/nim/nvidia/audio2face-3d:2.0
```

Project-scoped start:

```bash
export NGC_API_KEY=<local-ngc-key>
bash scripts/setup.sh --start-a2f-nim
```

Do not paste or commit `NGC_API_KEY`.

## Current browser animation contract

Completed local jobs expose:

```text
/api/artifacts/audio/<job-id>.wav
/api/artifacts/animation/<job-id>.json
```

The animation JSON uses `engine: browser-viseme-v2` with `jawOpen`, `mouthWide`, `mouthSmile`, and ARKit-style `blendShapes` frames. `FaceViewer` uses those values to animate the current browser 3D preview while the WAV plays. This is the release path for the current browser product, not an error fallback.

## Backend configuration

```env
A2F_HOST=127.0.0.1
A2F_PORT=8040
A2F_HTTP_PORT=8041
A2F_TRANSPORT=grpc
A2F_PROCESS_PATH=/api/process-audio
A2F_TIMEOUT_SECONDS=120
```

`A2F_PROCESS_PATH=/api/process-audio` is still present only for the legacy HTTP transport. With `A2F_TRANSPORT=grpc`, the backend uses Audio2Face-3D `ProcessAudioStream` and writes `engine: nvidia-audio2face-3d-v1`.

## Failure handling

- If the NIM cannot match RTX PRO 5000 Blackwell automatically, record the exact profile output and try local TensorRT generation.
- If local engine generation fails, keep `PIPELINE_MODE=riva` and document the Audio2Face-3D blocker without secrets.
- If a real A2F-3D service starts, capture the gRPC endpoint, model name, blendshape names, FPS behavior, GPU memory, and one small WAV smoke result.
- Do not retry in loops on GPU/service failure.
- Do not log NVIDIA keys, authorization headers, large audio payloads, or private assets.
