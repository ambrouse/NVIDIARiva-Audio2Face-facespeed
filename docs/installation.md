# Installation

Date: 2026-05-23

## Supported Machines

| Machine | Support | Notes |
| --- | --- | --- |
| Linux workstation with NVIDIA RTX GPU, recent driver, Docker, Node 20+, Python 3.10+ | Supported target | Required for the full local provider-backed Riva/Docling/embedding flow. |
| WSL2 with NVIDIA GPU passthrough and Docker Desktop | Best effort | Must pass `nvidia-smi`, Docker GPU, memory, disk, and port checks. |
| CPU-only Linux/macOS/Windows | Development only | Can run tests/build and inspect UI, but the full Riva/Docling/embedding runtime is not complete. |
| Terminal without network | Unsupported | Setup needs package and model/provider access. |

## One Command

```bash
./setup.sh
```

The default root command is `./setup.sh --setup-run`.

On a fresh clone, `./setup.sh --setup` and `./setup.sh --setup-run` create `.env` from `.env.example` when `.env` is missing. The generated config uses the provider-backed main path: `SERVICE_MANAGER_MODE=docker` and `PIPELINE_MODE=riva`.

## Setup Modes

| Command | Purpose |
| --- | --- |
| `./setup.sh --check` | Detect OS, Python, Node, npm, Docker, GPU, ports, memory, disk, Riva, and Audio2Face availability. |
| `./setup.sh --setup` | Install project-local backend/frontend dependencies. |
| `./setup.sh --run` | Start backend and frontend on localhost. |
| `./setup.sh --setup-run` | Check, install, and run local app. |
| `./setup.sh --verify` | Run frontend tests, frontend build, backend tests, and setup checks. |
| `./setup.sh --capture-demo` | Recreate the release GIF from the real app. |
| `./setup.sh --logs-clean` | Remove disposable runtime logs. |

## NVIDIA Requirements

Full Voice RAG runtime needs reachable providers:

| Provider | Default |
| --- | --- |
| Riva TTS | `127.0.0.1:50051` |
| Riva ASR | `127.0.0.1:50151` |
| Docling parse | `http://127.0.0.1:8005` |
| Embedding/rerank | `http://127.0.0.1:8006` |

The repository does not ship NVIDIA licensed model assets or credentials. Keep `NGC_API_KEY` in your local shell only.

Backend and frontend processes started by setup are detached with project PID files under `logs/runtime/`, so the app stays available after setup exits. Stop them with `./setup.sh --stop`.

## Failure Policy

The main path does not silently fall back. If Riva, Docling, embedding, or rerank is unavailable, setup and runtime status should report the exact blocker.
