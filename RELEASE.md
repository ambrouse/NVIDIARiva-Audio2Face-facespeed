# Release Notes: v0.3.0

Date: 2026-05-26

## Summary

v0.3.0 is the current local Voice RAG avatar release. It turns the project into a local product workspace for PDF-grounded voice answers with Riva speech, Docling parsing, embedding/rerank retrieval, vLLM teacher/review, and a browser 3D face.

## Supported Machine Profiles

| Profile | Status | Notes |
| --- | --- | --- |
| Linux workstation with NVIDIA RTX GPU, Docker, Node 20+, Python 3.10+ | Supported target | Required for local Riva/Docling/embedding provider runtime. |
| WSL2 with NVIDIA GPU passthrough and Docker Desktop | Best effort | Works only if `nvidia-smi`, Docker GPU, ports, and memory checks pass. |
| CPU-only Linux/macOS/Windows | UI/dev only | Can install/build frontend/backend, but provider-backed Riva/Docling/embedding runtime will not be complete. |
| No terminal/network | Unsupported | Setup requires shell and package/network access. |

## Release Checklist

- `./setup.sh --check`
- `bash -n scripts/setup.sh`
- `docker compose config --quiet`
- `curl http://127.0.0.1:6300/api/rag/status`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- `backend/.venv-linux/bin/python -m pytest tests`

## Evidence

- Benchmark summary: `tests/benchmarks/README.md`
- Benchmark report: `tests/benchmarks/REPORT-2026-05-25-rag-voice.md`
- Nginx proxy smoke: `tests/nginx-proxy/test-nginx-proxy-20260526-v1.md`
- README banner image: `docs/assets/facespeed-readme-banner.png`

## Known Limits

- NVIDIA Riva, Docling, embedding/rerank, and vLLM providers must be running and reachable for the true main path.
- The repository does not bundle NVIDIA licensed model assets or NGC credentials.
- Audio2Face-3D NIM remains optional; the current product path uses Riva voice plus browser-side ARKit morph animation.
- Local Riva TTS can timeout on long spoken text; `VOICE_CHAT_TTS_MAX_CHARS=150` keeps audio preview short while preserving the full answer in chat.
