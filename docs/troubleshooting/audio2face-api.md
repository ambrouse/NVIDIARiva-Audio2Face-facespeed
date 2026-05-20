# Troubleshooting: Audio2Face API

Time: 2026-05-20

## Current status

The backend has a configurable HTTP Audio2Face adapter, but the real Audio2Face container image/tag/API contract has not been verified yet.

Do not claim real Audio2Face pass until all of these are known:

1. Official container image/tag.
2. Required runtime mode: GUI, headless/service, container or HTTP automation endpoint.
3. Health endpoint.
4. WAV submission endpoint.
5. Expected request payload.
6. Expected result/artifact format.

## Backend configuration

```env
A2F_HOST=127.0.0.1
A2F_PORT=8040
A2F_PROCESS_PATH=/api/process-audio
A2F_TIMEOUT_SECONDS=120
```

`A2F_PROCESS_PATH=/api/process-audio` is only a placeholder until the real API is verified.

## Safe verification process

1. Run resource and port preflight.
2. Verify image/tag and API docs.
3. Generate dry-run container command:

```bash
export A2F_CONTAINER_IMAGE=<verified-audio2face-image>
bash scripts/setup.sh --dry-run-containers
```

4. Ask before pulling/starting the container.
5. Start only on `127.0.0.1:8040` with the project label.
6. Test a small WAV once.
7. Capture result metadata and resource before/after snapshots.

## Failure handling

- If health endpoint is missing, mark blocked and document the actual available API.
- If A2F requires GUI/display, do not force headless mode without confirming support.
- If endpoint returns an error, log safe status and do not retry in a loop.
- Do not log NVIDIA keys, authorization headers or large payloads.
