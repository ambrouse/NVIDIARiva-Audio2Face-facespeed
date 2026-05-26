# Plan: Release Repo Hardening

- Created: 2026-05-23 01:22
- Updated: 2026-05-23 03:02
- Status: completed
- Related log: logs/plans/release-repo-hardening.md

## Goal

Bring the repository to a release-ready GitHub product state: clean source/evidence/logs/docs, production README with GIF banner, complete setup and operations docs, license/contribution/release metadata, and full test proof that the RAG voice avatar pipeline still runs.

## Scope

- In:
  - Consolidate duplicated evidence/test folders into one current release evidence package.
  - Capture a smooth GIF demo under `.cache/facespeed/evidence/` and publish the same GIF into `docs/assets/` for the README banner.
  - Clean logs and add durable log retention/cleanup scripts and docs.
  - Add GitHub-ready `LICENSE`, `CONTRIBUTING.md`, release notes, version metadata, and docs index.
  - Harden `setup.sh` so a terminal-only machine can check/install prerequisites, create venv/node deps, validate Docker/GPU/Riva/RAG requirements, and fail with clear unsupported-machine messages.
  - Update README to Readme Style with banner, quick start, machine support matrix, repo map, docs index, test evidence, and accuracy notes.
  - Run backend/frontend/build/browser QA and read screenshots/GIF before marking pass.
- Out:
  - Pushing tags/releases to GitHub unless explicitly requested.
  - Claiming unsupported NVIDIA services can run on machines without compatible GPU/Docker/network.

## Skills

- plan-skill
- frontend-skill
- backend-skill
- testing-skill
- documentation-skill
- logging-skill
- readme-style
- security-skill

## Phases

| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Audit current docs/logs/tests/setup and benchmark product UI references | done | Web reference notes, repo inventory |
| 2 | Clean and consolidate test/evidence/log/doc structure | done | `.cache/facespeed/evidence/release-readiness-2026-05-23/`, `logs/README.md` |
| 3 | Add license/contributing/version/release metadata | done | `LICENSE`, `CONTRIBUTING.md`, `CONTRIBUTORS.md`, `VERSION`, `CHANGELOG.md`, `RELEASE.md` |
| 4 | Harden setup/log management scripts and docs | done | `setup.sh`, `scripts/setup.sh`, `scripts/manage-logs.sh`, `docs/installation.md`, `docs/operations.md` |
| 5 | Regenerate demo video/GIF banner and README | done | `docs/assets/voice-rag-avatar-demo.gif`, `README.md` |
| 6 | Full verification: tests, build, browser, screenshots, GIF review, hygiene scan | done | Tests/build passed; GIF and hygiene scan verified |

## Verification

- `bash setup.sh --check`
- `bash scripts/manage-logs.sh --dry-run`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests`
- Browser QA through the running app with screenshot/GIF evidence.
- Evidence hygiene: no duplicate stale evidence folders, no pycache/test temp files, no visible audio bar, GIF under 100 MB.

Latest results:

- `npm --prefix frontend test -- --run`: 4 passed.
- `npm --prefix frontend run build`: passed with a non-blocking Vite chunk-size warning for the Three.js bundle.
- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests`: 41 passed.
- `./setup.sh --check`: completed with environment warnings for the current host while Riva/Docling/embedding/backend/frontend checks were reachable.
- Browser QA captured desktop/mobile screenshots plus `facespeed-release-demo.gif` under 100 MB.
- Fresh release clone validation passed from `/tmp/facespeed-release-clone-validation-2026-05-23`; evidence is in `.cache/facespeed/evidence/release-clone-validation-2026-05-23/`.

## Close Criteria

- README looks like a credible GitHub product page with GIF banner and accurate run instructions.
- Important folders have README files.
- Only current, useful evidence remains in `.cache/facespeed/evidence/`.
- Logs are summarized and operational logs have cleanup/retention workflow.
- Setup script can bootstrap or clearly report missing OS/GPU/Docker/key prerequisites.
- All automated and browser checks pass with evidence.
