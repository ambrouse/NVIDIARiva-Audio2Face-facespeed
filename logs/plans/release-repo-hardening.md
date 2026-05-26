# Release Repo Hardening Log

## 2026-05-23 01:22

Started release-readiness cleanup after user requested a GitHub-ready repository, smooth GIF demo, consolidated test/evidence folders, clean docs/logs, license/contribution/release metadata, and terminal-only setup automation.

Reference scan:

- HeyGen/Synthesia/Beyond Presence emphasize direct avatar presence, natural voice, avatar selection, low-friction workflow, and minimal technical chrome.
- This repository should keep the product surface voice-first: chat history, hold-to-talk, avatar face, replay icon, and provider-backed runtime details in compact popups/pages.

Initial repo findings:

- `.cache/facespeed/evidence/` has multiple overlapping evidence folders for the same product surface.
- The old mixed evidence folder combined test fixtures, provider proof, UI screenshots, audio, video, and reports.
- `logs/jobs/` contains many per-job runtime logs that should not remain as permanent source artifacts.
- Root metadata is missing `LICENSE`, `CONTRIBUTING.md`, changelog/release notes, and explicit version file.
- Existing setup scripts need a single root entrypoint that can check/install prerequisites or fail closed with readable machine-support guidance.

Completed release hardening:

- Consolidated all release evidence into `.cache/facespeed/evidence/release-readiness-2026-05-23/` and removed stale duplicate evidence folders.
- Captured the production UI flow as `.cache/facespeed/evidence/release-readiness-2026-05-23/demo/facespeed-release-demo.gif` and published it to `docs/assets/voice-rag-avatar-demo.gif` for the README banner.
- Added GitHub metadata: `LICENSE`, `CONTRIBUTORS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `RELEASE.md`, and `VERSION`.
- Updated version metadata in the backend FastAPI app and frontend package files to `0.3.0`.
- Added folder-level READMEs for `backend/`, `frontend/`, `docs/`, `scripts/`, `tests/`, `.cache/facespeed/evidence/`, `logs/`, and `plans/`.
- Hardened setup and operations flow through root `setup.sh`, `scripts/setup.sh`, `scripts/manage-logs.sh`, `docs/installation.md`, and `docs/operations.md`.
- Rebuilt `README.md` as a product-facing GitHub entry with banner GIF, quick start, support matrix, evidence links, test commands, and repository map.
- Cleaned runtime log folders and configured `.gitignore` so durable plan logs stay tracked while disposable logs stay out of source.

Verification completed:

- `npm --prefix frontend test -- --run`: 4 passed.
- `npm --prefix frontend run build`: passed; Vite reported a non-blocking chunk-size warning for the Three.js/avatar bundle.
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests`: 41 passed.
- `bash -n setup.sh && bash -n scripts/setup.sh && bash -n scripts/manage-logs.sh`: passed.
- `./setup.sh --check-support`: printed the support matrix successfully.
- `./setup.sh --check`: completed with current-host warnings for missing NGC CLI, busy ports from already-running services, low memory/VRAM reserve, and no detected Audio2Face-3D runtime. Main Riva/Docling/embedding/backend/frontend checks were reachable.
- Browser evidence confirmed no visible audio controls, replay-only audio UX, model morph animation, avatar selection, mobile layout, and clean console/network report.
- Final hygiene scan found no stale evidence paths, no source `__pycache__`/`.pytest_cache` outside ignored dependency folders, and no runtime disposable log paths.
- GIF validation: `facespeed-release-demo.gif` is 960x540, 45 decoded frames, 2.1 MB.

Clone validation follow-up:

- Created a clean release snapshot at `/tmp/facespeed-release-clone-validation-2026-05-23` without `.env`, venvs, `node_modules`, `dist`, `outputs`, `storage`, runtime logs, or caches.
- Found and fixed release-clone issues: setup did not create provider-backed `.env`, tests were affected by `.env`, and bootstrap-started backend/frontend processes died after the setup command returned.
- Final clone verification passed: fresh setup installed deps, `.env` was created with `SERVICE_MANAGER_MODE=docker` and `PIPELINE_MODE=riva`, `./setup.sh --verify` passed frontend 4/4 and backend/setup 41/41, and `./setup.sh --bootstrap` kept backend/frontend alive on `8120/6410`.
- Clone RAG proof passed: Docling ingested `clone-rag-evidence.pdf`, embedding/rerank returned a cited answer, Riva produced RIFF WAV audio, and the avatar animation artifact contained 1,636 frames.
- Clone browser proof passed with screenshots in `.cache/facespeed/evidence/release-clone-validation-2026-05-23/app/` and zero console/page/network errors in `browser-report.json`.
