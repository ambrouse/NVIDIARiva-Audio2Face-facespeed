# Production End-User Rebuild Log

## 2026-05-22 14:40

Created the implementation plan for rebuilding FaceSpeed into a production-style end-user avatar studio.

Inputs and skills:

- `plan-skill`: required persisted plan with phases, verification, evidence, close criteria.
- `frontend-skill`: product UI must be polished, responsive, accessible, and end-user focused.
- `testing-skill`: every visible frontend function needs real browser validation and one strong screenshot.
- `readme-style`: README should act like a GitHub product landing page plus operational brief.

Research summary:

- HeyGen uses a creator-first flow: avatar selection/upload, script typing, language/voice, generation, and visible output.
- Synthesia uses a broader production model: create, localize, manage, publish, engage, with avatar and video output controls.
- Tavus emphasizes face-to-face real-time AI with a large human preview and developer/enterprise paths.

Decision:

- Plan targets an end-user "Speaking Avatar Studio" rather than the current dashboard-first app.
- Technical service/container/status pages should become secondary support surfaces.
- Evidence must avoid screenshot spam: one reviewed image per meaningful function/state.

Created:

- `plans/plan-production-enduser-rebuild.md`

## 2026-05-22 14:45

Started execution.

Audit snapshot:

- Frontend currently has a dashboard shell with `Pipeline`, `Services`, `Logs`, and `System` pages.
- Backend routes include jobs, artifacts, services, and system checks.
- Runtime/generated folders present: `.cache/`, `.local-libs/`, `.local-rpms/`, `.pytest_cache/`, `backend/.venv-linux/`, `frontend/node_modules/`, `frontend/dist/`, `outputs/`, `logs/`, and previous `.cache/facespeed/evidence/*`.
- Required skill folders exist in both `.codex/skills/` and `skills/`; user explicitly asked to keep skill folders.
- Current live ports after previous fix: frontend `6310`, backend `8020`, Riva `50051`.

Initial cleanup rule:

- Do not delete runtime folders yet; first update `.gitignore` and create cleanup manifest so generated/runtime assets are not confused with source.

## 2026-05-22 14:53

Execution updates:

- Reworked the frontend shell from dashboard-first navigation to an end-user studio layout:
  - Main tab: `Studio` with script, voice, language, avatar rig, output mode, generate button, output playback, and 3D face preview.
  - Secondary tabs: `Operations`, `Activity`, and `Setup`.
- Moved frontend runtime to `127.0.0.1:6310` across config, tests, and docs.
- Added root `setup.sh` as the one-command entrypoint. With no args it runs `--setup-run`.
- Extended `scripts/setup.sh` with:
  - `--setup`, `--run`, `--setup-run`, `--status`, `--stop`, and `--help`.
  - PID files under `logs/runtime/`.
  - Backend/frontend startup with warnings allowed for resource gates.
  - Project-scoped stop/status behavior for local app processes and labeled containers.
- Verified:
  - `bash -n setup.sh && bash -n scripts/setup.sh`
  - `bash setup.sh --status`
  - `bash setup.sh --run`
- Current runtime:
  - Backend health is reachable at `http://127.0.0.1:8020/health`.
  - Frontend is reachable at `http://127.0.0.1:6310/`.
  - Riva TCP is reachable at `127.0.0.1:50051`.
  - Audio2Face-3D is not currently reachable at `127.0.0.1:8040` or `127.0.0.1:8041/health`.

Cleanup performed:

- Removed generated build/runtime folders:
  - `frontend/dist/`
  - `.cache/model-search/`
  - `.pytest_cache/`
  - `backend/.pytest_cache/`
  - Python `__pycache__/` folders under project source/tests/scripts.
  - Old `outputs/`, `backend/outputs/`, `backend/logs/`, and `logs/jobs/`.
  - Previous ad-hoc evidence folders under `.cache/facespeed/evidence/`.
  - Duplicate/root FBX uploads and the unused frontend `head.fbx` model copy.
- Kept intentionally:
  - `.cache/nvidia/` for downloaded NVIDIA assets and NGC CLI material.
  - `.local-libs/` and `.local-rpms/` for local browser/Playwright audio-library support.
  - `frontend/node_modules/` and `backend/.venv-linux/` so the project remains runnable during QA.
  - `.codex/skills/` and `skills/` as requested.

Verification after cleanup/setup edits:

- `npm --prefix frontend test -- --run`: passed, 3 tests. jsdom still prints expected canvas/WebGL stubs.
- `npm --prefix frontend run build`: passed. Vite reports a non-fatal large chunk warning for the Three.js bundle.
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests`: passed, 33 tests.

## 2026-05-22 15:06

Final implementation pass completed.

Frontend/product:

- Changed the product from dashboard-first to `FaceSpeed Studio`.
- Main screen is now an end-user avatar creation studio with:
  - Script editor.
  - Riva English voice selection.
  - Language, avatar rig, and output mode controls.
  - Generate button.
  - Output job state, audio playback, animation artifact link.
  - Three.js ReadyPlayer ARKit speaking avatar preview.
- Secondary pages are now:
  - `Operations`: status-only service/container view with real refresh.
  - `Activity`: service log load/filter.
  - `Setup`: machine readiness checks.
- Removed visible Start/Restart/Stop service buttons from Operations because they were too operational for the end-user UI and better handled through `setup.sh`.
- Added favicon and updated browser title to `FaceSpeed Studio`.
- Fixed mobile badge stretching found during visual evidence review.

Setup/source:

- Added root `setup.sh` one-command entrypoint.
- `scripts/setup.sh` now supports `--setup`, `--run`, `--setup-run`, `--status`, `--stop`, and `--help`.
- `--status` now reports backend/frontend port owner PIDs even when the service was started before PID files existed.
- `--stop` can stop project-owned backend/frontend port listeners after verifying the process command line belongs to this repo.
- Runtime cleanup removed generated caches/builds/old evidence while keeping `.cache/nvidia`, local browser libs, node modules, venv, and both skill folders.
- Renamed frontend package from `text-speech-face-dashboard` to `facespeed-studio`.

README/evidence:

- Rebuilt `README.md` using the project README style.
- Added real browser GIF banner at `docs/assets/voice-rag-avatar-demo.gif`.
- Created evidence folder: `.cache/facespeed/evidence/release-readiness-2026-05-23/`.
- Evidence includes:
  - 6 screenshots, one per function/state.
  - `browser-report.json`.
  - `audio-report.json`.
  - `generated-audio.wav`.
  - `voice-rag-avatar-demo.gif`.

Evidence results:

- Browser console errors: 0.
- Page errors: 0.
- HTTP 4xx/5xx responses: 0.
- Job id: `17309abe-6bd3-4d77-b91d-a6d21a46ca12`.
- Animation engine: `browser-viseme-v2`.
- Animation frames: 451.
- Avatar model: ReadyPlayer ARKit GLB with 208 morph targets.
- Audio: mono PCM WAV, 22050 Hz, 7.512 seconds, RMS 1949.23, peak 17342, non-silent true.

Final verification:

- `bash -n setup.sh && bash -n scripts/setup.sh && bash setup.sh --status`: passed; status reports existing backend/frontend port owner PIDs.
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests/test_setup_script.py`: passed, 9 tests after the port-owner status/stop enhancement.
- `npm --prefix frontend test -- --run`: passed, 3 tests. jsdom canvas warnings are expected.
- `npm --prefix frontend run build`: passed with a non-fatal Three.js bundle size warning.
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests`: passed, 33 tests.
- Duplicate screenshot hash scan: no duplicates.
- Secret scan: only placeholder NGC examples were matched; no concrete key material found.

Remaining known limitation:

- Audio2Face-3D NIM is still optional and not running in this final QA pass. The delivered working path is Riva TTS plus browser `browser-viseme-v2` animation on a morph-target 3D avatar.
