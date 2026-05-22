# Release Notes: v0.3.0

Date: 2026-05-23

## Summary

v0.3.0 is the first GitHub-ready Voice RAG avatar release. It turns the project into a local product workspace for PDF-grounded voice answers with Riva speech and a browser 3D face.

## Supported Machine Profiles

| Profile | Status | Notes |
| --- | --- | --- |
| Linux workstation with NVIDIA RTX GPU, Docker, Node 20+, Python 3.10+ | Supported target | Required for local Riva/Docling/embedding provider runtime. |
| WSL2 with NVIDIA GPU passthrough and Docker Desktop | Best effort | Works only if `nvidia-smi`, Docker GPU, ports, and memory checks pass. |
| CPU-only Linux/macOS/Windows | UI/dev only | Can install/build frontend/backend, but provider-backed Riva/Docling/embedding runtime will not be complete. |
| No terminal/network | Unsupported | Setup requires shell and package/network access. |

## Release Checklist

- `./setup.sh --check`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests`
- `node scripts/capture-release-demo.mjs`

## Evidence

- Release evidence: `test/release-readiness-2026-05-23/`
- README banner GIF: `docs/assets/voice-rag-avatar-demo.gif`
- Browser report: `test/release-readiness-2026-05-23/browser-report.json`

## Known Limits

- NVIDIA Riva, Docling, and embedding/rerank providers must be running and reachable for the true main path.
- The repository does not bundle NVIDIA licensed model assets or NGC credentials.
- Audio2Face-3D NIM remains optional; the current product path uses Riva voice plus browser-side ARKit morph animation.
