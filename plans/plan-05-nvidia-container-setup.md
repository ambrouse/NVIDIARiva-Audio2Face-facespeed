# Plan 05: NVIDIA Container Setup

## Mục tiêu

Thiết kế và triển khai workflow setup Riva và Audio2Face bằng container mới riêng cho FaceSpeed, an toàn cho server nhiều project.

## Skill phải đọc trước khi làm

- `security-skill`
- `testing-skill`
- `documentation-skill`
- `logging-skill`
- `backend-skill`
- `push-code-skill` nếu chạm CI/config release

## Phạm vi

Làm:

1. Container plan cho Riva.
2. Container plan cho Audio2Face sau khi xác minh image/tag/API.
3. Cache/assets layout trong `.cache/nvidia/`.
4. Safe scripts/dry-run.
5. Rollback commands scoped by project label/name.

Không làm nếu chưa hỏi user:

- Pull image/model lớn.
- Start GPU container.
- Docker cleanup thêm.
- Use sudo/system install.
- Bind public network.

## Container naming/labels

All project containers:

```text
name prefix: facespeed-
label: com.facespeed.project=NVIDIARiva-Audio2Face-facespeed
bind: 127.0.0.1 only
```

Suggested names:

```text
facespeed-riva
facespeed-audio2face
```

## Cache/assets layout

```text
.cache/nvidia/ngc/
.cache/nvidia/riva/
.cache/nvidia/audio2face/
outputs/smoke/
logs/setup/
```

Rules:

- Gitignored.
- No secret stored in tracked files.
- NVIDIA key only via interactive `ngc config set` or local ignored secret if user explicitly approves.
- Remind user to rotate key after setup because key was pasted in chat.

## Preflight hard gates

Before pull/start:

1. `ss -ltnp` target ports free.
2. `df -h` project/home free >= 10%.
3. `MemAvailable` >= 10%.
4. Commit headroom >= 10%.
5. VRAM free >= 10%.
6. `docker info` OK.
7. NVIDIA container runtime OK.
8. Existing GPU processes listed and not touched.
9. User confirms action.

If any gate fails: BLOCKED.

## Riva container workflow

### Step 1: Identify official image/setup path

Need current NVIDIA/Riva container docs or existing known image from NGC.

ASK if:

- Image/tag unclear.
- NGC license/EULA requires manual acceptance.

### Step 2: Dry-run command generation

Generate command without executing:

- Pull image.
- Mount `.cache/nvidia/riva`.
- Expose `127.0.0.1:50100`.
- Add label/name.
- Add resource limits if compatible.
- GPU device minimal.

PASS if command is reviewed and scoped.

### Step 3: Start only after confirmation

Start container only after user confirms.

PASS if:

- Container is `facespeed-riva`.
- Port `50100` listening on `127.0.0.1`.
- Riva health/smoke light check passes or blocked with reason.

## Audio2Face container workflow

### Step 1: Verify image/tag/API

Audio2Face container/API may vary. Do not assume `/api/process-audio` is real.

Need determine:

- Official image/tag.
- Required GPU/display/headless mode.
- HTTP/gRPC/streaming endpoint.
- How to submit WAV.
- Output artifact format.

ASK if image/API unclear.

### Step 2: Dry-run command generation

Generate command:

- Name `facespeed-audio2face`.
- Label project.
- Mount `.cache/nvidia/audio2face`.
- Bind `127.0.0.1:8040`.
- Resource limits.
- No public bind.

### Step 3: Start only after confirmation

PASS if:

- Container starts without restart loop.
- API/health endpoint verified.
- Resource usage acceptable.

## Rollback procedure

Default rollback:

```bash
docker stop facespeed-riva facespeed-audio2face
```

Rules:

- Only exact project names/labels.
- Do not remove volumes/cache unless user confirms.
- Do not prune globally during rollback.

Optional cleanup after confirmation:

```bash
docker rm facespeed-riva facespeed-audio2face
docker volume rm <project-specific-volume>
```

## Tests/evaluation

Non-GPU tests:

- Setup script static tests.
- Dry-run output assertions.
- No unsafe Docker command patterns.

GPU/manual tests after confirmation:

- Riva health.
- A2F health.
- Port bound localhost.
- `docker inspect` labels/name/resource limits.
- Resource before/after snapshot.

## PASS/ASK/REDO/BLOCKED

PASS when:

1. Dry-run commands safe.
2. User-approved container start succeeds.
3. Containers named/labeled/bound correctly.
4. Resource snapshot within thresholds.
5. Rollback command documented.

ASK when:

- Pull/start/download needed.
- Image/tag/license/API unclear.
- Port conflict.
- Resource limits may need tuning.

REDO when:

- Command binds `0.0.0.0`.
- Missing label/name.
- Restart loop.
- Secret printed/logged.

BLOCKED when:

- No NGC access.
- Image/license unavailable.
- Resource threshold fails.
- Docker/NVIDIA runtime fails.

## Docs/logs

- Update `docs/nvidia-host-setup.md`.
- Log resource snapshots and commands with secrets redacted.
- Do not commit local logs/cache.

## Close Comment

Status: PASS for dry-run workflow; BLOCKED for real container start
Closed at: 2026-05-20 16:46
Evidence:
- Added `--dry-run-containers` mode.
- Dry-run prints scoped Docker pull/run commands with `facespeed-` names, project label, localhost binds, cache mounts, resource limits and `--restart no`.
- Dry-run prints scoped rollback commands and keeps cache/assets by default.
- `.env.example` includes container image/name/resource-limit fields.
- `docs/nvidia-host-setup.md` documents dry-run container workflow and rollback rules.
- `bash -n scripts/setup.sh`: PASS.
- `backend/.venv-linux/bin/python -m pytest tests`: 9 passed.
- `backend/.venv-linux/bin/python -m pytest backend tests`: 25 passed.
- Placeholder dry-run command printed instructions only; no image pull/container start/cleanup was executed.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 05 - NVIDIA Container Setup Dry-run`
Next plan: `plans/plan-06-smoke-output-evaluation.md`
Notes:
- Real Riva/A2F container start is BLOCKED until official image/tag/API are verified and user explicitly confirms pull/start.
- NVIDIA key must not be written to repo/log/docs/env; remind user to rotate after setup.
- Re-run resource guardrails before any heavy pull/start because memory commit headroom is close to threshold.
