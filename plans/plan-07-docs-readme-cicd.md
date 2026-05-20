# Plan 07: Docs, README, CI/CD, Versioning

## Mục tiêu

Hoàn thiện tài liệu, README, CI/CD, versioning và release gates để repo dễ clone, dễ chạy mock/local, và setup NVIDIA container an toàn.

## Skill phải đọc trước khi làm

- `documentation-skill`
- `readme-style`
- `testing-skill`
- `security-skill`
- `push-code-skill`
- `logging-skill`

## Phạm vi

Làm:

1. README chuẩn.
2. Docs NVIDIA/setup/troubleshooting.
3. Phase reports.
4. CI/CD review/update.
5. Version consistency.
6. Gitignore/env hygiene.

Không làm:

- Không push nếu chưa đến final plan và user confirm.
- Không claim NVIDIA real pass nếu blocked.

## README requirements

README phải có:

1. Title/banner/badges.
2. Overview.
3. Mermaid flow.
4. Quick Start local mock:
   - backend `127.0.0.1:8020`
   - frontend `127.0.0.1:6210`
5. VS Code port forwarding note.
6. NVIDIA container setup safe summary.
7. Resource safety checklist:
   - port
   - process
   - RAM
   - memory commit
   - disk
   - GPU/VRAM
   - Docker
8. Repository map.
9. Test commands.
10. Docs index.
11. Accuracy notes:
   - mock pass vs real NVIDIA pass
   - blocked conditions
   - A2F API uncertainty until verified
12. Secret warning:
   - no NVIDIA/NGC key in repo/log/docs
   - rotate key if exposed.

PASS if README commands match actual scripts/env.

## Docs structure

Target docs:

```text
docs/nvidia-host-setup.md
docs/troubleshooting/resource-and-ports.md
docs/troubleshooting/audio2face-api.md
docs/phase-reports/phase-0-baseline.md
docs/phase-reports/phase-1-resource-guardrails.md
...
```

Rules from `documentation-skill`:

- Docs in `docs/`.
- Timestamp rõ.
- Tóm tắt trọng tâm.
- Clean/update old docs after task.

## CI/CD requirements

Review `.github/workflows/ci.yml`.

CI should run non-GPU safe checks:

1. Backend tests.
2. Setup script static tests.
3. Frontend tests.
4. Frontend build.
5. Optional secret/gitignore checks.

CI must not:

- Pull NVIDIA containers.
- Run GPU smoke.
- Require NGC key.
- Bind public ports.

PASS if CI yaml aligns with commands and no heavy jobs.

## Versioning requirements

Check/update consistency:

- `VERSION`
- `frontend/package.json` version if present.
- README version mention if any.

ASK if:

- Version bump type unclear.

## Gitignore/env hygiene

Must ignore:

```text
.env
logs/
outputs/
.cache/
.cache/nvidia/
frontend/.ms-playwright/
.local-libs/
.local-rpms/
riva-model-repo/
*.wav
*.mp3
```

`.env.example` may include keys names but not secret values.

PASS if no secret/cache/output/log is tracked.

## Test commands

```bash
python -m pytest tests
backend/.venv-linux/bin/python -m pytest backend tests
npm --prefix frontend test
npm --prefix frontend run build
```

Plus CI syntax review via reading yaml; only run extra validators if available without install.

## PASS/ASK/REDO/BLOCKED

PASS when:

1. README accurate.
2. Docs updated and concise.
3. CI safe and relevant.
4. Version consistent.
5. Gitignore/env safe.
6. Tests/build pass or blocked documented.

ASK when:

- Need version bump decision.
- Need README screenshot/banner.
- Need accept docs wording for real NVIDIA blocked.

REDO when:

- README commands wrong.
- Docs claim real NVIDIA pass without evidence.
- CI runs heavy/GPU job.
- Secret appears in tracked file.

BLOCKED when:

- Tests cannot run due missing deps and install not approved.

## Logs

Log docs/CI updates in `logs/sessions/facespeed-safe-completion.md`.

## Close Comment

Status: PASS
Closed at: 2026-05-20 16:59
Evidence:
- `README.md` updated with safe local mock quick start, NVIDIA container dry-run workflow, resource gates, VS Code forwarding, tests, repo map, docs index and accuracy notes.
- Added `docs/troubleshooting/resource-and-ports.md`.
- Added `docs/troubleshooting/audio2face-api.md`.
- `.github/workflows/ci.yml` now includes setup syntax, tracked runtime artifact and NVIDIA key checks.
- `.gitignore` now broadly ignores `logs/`, `outputs/` and `.cache/`.
- Version consistent: `VERSION` and `frontend/package.json` are both `0.1.0`.
- `backend/.venv-linux/bin/python -m pytest backend tests`: 25 passed.
- `npm --prefix frontend test`: 3 passed.
- `npm --prefix frontend run build`: PASS with existing FaceViewer chunk-size warning.
- `bash -n scripts/setup.sh`: PASS.
- Tracked NVIDIA key grep: PASS.
- Tracked runtime/cache artifact check: PASS.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 07 - Docs, README, CI/CD, Versioning`
Next plan: `plans/plan-08-final-review-push.md`
Notes:
- CI remains non-GPU safe and does not pull NVIDIA containers or require NGC key.
- Real NVIDIA pass is not claimed in docs.
