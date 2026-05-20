# Plan 03: Backend Hardening

## Mục tiêu

Hoàn thiện backend FastAPI để pipeline mock/NVIDIA an toàn, deterministic, có output contract rõ và không tạo rủi ro path/command/secret/resource.

## Skill phải đọc trước khi làm

- `backend-skill`
- `testing-skill`
- `security-skill`
- `documentation-skill`
- `logging-skill`

## Phạm vi

Làm:

1. Config/env validation.
2. Job algorithm/state machine hardening.
3. Riva/A2F adapters contract.
4. System/resource API read-only nếu cần frontend dashboard.
5. Tests backend.

Không làm:

- Không start Riva/A2F thật.
- Không tạo auth public nếu dashboard chỉ localhost.
- Không thêm dependency nếu không cần.

## Backend contract mục tiêu

### Config

- Đọc env uppercase và camelCase.
- Default localhost ports từ `.env.example`.
- Validate modes: `mock`, `nvidia`.
- Allowed origins chỉ localhost nếu chưa auth.
- Resource thresholds có default 10%.
- Không expose secret trong API/log.

### Job algorithm

State order:

```text
validating_text -> generating_speech -> speech_ready -> sending_to_a2f -> animating_face -> completed
```

Failure:

```text
failed + safe error message + job log
```

Rules:

- Normalize text.
- Reject empty text.
- Enforce text length limit.
- Validate language/voice/profile/output mode.
- One job at a time for NVIDIA mode unless later explicitly changed.
- Timeout external calls.
- No infinite retry.

### Artifact contract

- Audio files only under `outputs/audio` or `outputs/smoke`.
- Riva LINEAR_PCM must be written as valid WAV.
- A2F result JSON must be stored under `outputs/a2f` or `outputs/smoke`.
- No path from user controls output path.

### Service manager contract

- Service allowlist only.
- No raw command from frontend.
- Start/stop real containers only via project label/name and explicit confirm/manual path.
- Read logs by service key, not arbitrary path.

## Các bước chi tiết

### Step 1: Config hardening

Implement/verify:

- `BACKEND_PORT=8020`
- `FRONTEND_PORT=6210`
- `RIVA_PORT=50100`
- `A2F_PORT=8040`
- `RESOURCE_RESERVE_PERCENT=10`
- `GPU_MIN_FREE_VRAM_PERCENT=10`
- `RAM_MIN_FREE_PERCENT=10`
- `DISK_MIN_FREE_PERCENT=10`

PASS nếu tests chứng minh env được đọc đúng và defaults đúng.

### Step 2: Job request validation

Test cases:

1. Empty text -> validation error or failed job safe message.
2. Long text -> rejected.
3. Invalid output mode -> rejected by schema.
4. Valid mock job -> completed.
5. Riva failure -> failed with safe error.
6. A2F timeout/error -> failed with safe error.

PASS nếu API/service behavior deterministic.

### Step 3: Riva adapter tests

Test fake Riva returns PCM.

PASS nếu WAV output:

- 1 channel.
- 16-bit sample width.
- sample rate matches config.
- frames equal fake PCM.

### Step 4: A2F adapter tests

Test fake HTTP.

PASS nếu:

- URL uses configured localhost host/port/path.
- Payload has audioPath/profile/outputMode.
- Response JSON written safely.
- HTTP error/timeout handled without secret leak.

### Step 5: System/resource read-only API

If needed by frontend, add endpoint such as:

```text
GET /api/system
GET /api/system/resources
```

Rules:

- Read-only.
- No secrets.
- No shell command from request.
- Use safe fixed checks or cached script output.

ASK nếu:

- Endpoint would need extra dependency or sudo.

## Test commands

```bash
backend/.venv-linux/bin/python -m pytest backend tests
python -m pytest tests
```

## Đánh giá output

PASS khi:

1. Backend tests pass.
2. Job mock output có audio/result/log.
3. Error cases có safe error.
4. No secret in logs/diff.
5. No command/path traversal issue.

ASK khi:

- Cần chọn text length max, voice allowlist, language allowlist.
- Cần background worker/concurrency design lớn hơn scope.

REDO khi:

- State order sai.
- Artifact path unsafe.
- Test pass bằng mock quá mức làm mất contract external boundary.
- Error leak stack/secret/token.

## Docs/logs

- Update docs if API contract changes.
- Log phase result in `logs/sessions/facespeed-safe-completion.md`.

## Close Comment

Status: PASS
Closed at: 2026-05-20 16:20
Evidence:
- Backend settings now default to safe localhost ports and include resource threshold config.
- Job request validation rejects whitespace-only text, too-long text and unsafe voice names.
- Riva/A2F failure paths are covered and return failed jobs with safe errors.
- `backend/.venv-linux/bin/python -m pytest backend tests`: 23 passed.
- `npm --prefix frontend test`: 1 passed.
- `npm --prefix frontend run build`: PASS with existing FaceViewer chunk-size warning.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 03 - Backend Hardening`
Next plan: `plans/plan-04-frontend-dashboard.md`
Notes:
- No NVIDIA real service, Docker container, GPU smoke or browser manual test was run in this phase.
- UI/browser verification belongs to Phase 04.
