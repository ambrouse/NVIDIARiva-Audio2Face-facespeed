# Plan 06: Smoke Tests and Output Evaluation

## Mục tiêu

Kiểm chứng pipeline mock và NVIDIA thật bằng test có kiểm soát tài nguyên, đánh giá output/thuật toán rõ ràng trước khi claim pass.

## Skill phải đọc trước khi làm

- `testing-skill`
- `security-skill`
- `logging-skill`
- `documentation-skill`
- `backend-skill`
- `frontend-skill` nếu test UI

## Phạm vi

Làm:

1. Mock smoke test local.
2. Riva real smoke after approval.
3. A2F real smoke after approval.
4. End-to-end one-job smoke after approval.
5. Output artifact evaluation.

Không làm:

- No benchmark/load/concurrency.
- No repeated retry loop.
- No GPU smoke if resource gate fails.

## Test levels

### Level 1: Mock pipeline smoke

Input:

```text
hello from facespeed smoke
```

Expected:

- Job completed.
- State transitions in order.
- Audio path exists.
- Result JSON exists.
- Job logs exist.

PASS if backend API/service returns completed mock job and artifacts are safe paths.

### Level 2: Riva real smoke

Input:

- Very short text.
- Known language/voice.
- One request only.

Expected:

- WAV file exists.
- WAV metadata valid.
- Duration > 0.
- Sample rate matches config.
- File size reasonable.

PASS if WAV can be opened and metadata verified.

ASK before running because GPU/container.

### Level 3: A2F real smoke

Input:

- Small WAV from Riva or fixture.

Expected depends on A2F API after verification:

- HTTP success or accepted job.
- Result metadata/artifact path.
- Error format safe if unsupported.

PASS if A2F endpoint contract verified and artifact/result captured.

ASK if API/image/tag unclear.

### Level 4: End-to-end real smoke

Input:

- One short text job.

Expected:

- Riva WAV.
- A2F result.
- Backend job completed.
- Frontend can display result in localhost UI.

PASS only with resource before/after snapshot and artifacts.

## Algorithm evaluation checklist

1. Input normalized.
2. State order correct.
3. Audio is valid WAV.
4. A2F payload/result matches verified contract.
5. Errors safe and user-visible.
6. No secret in logs.
7. No path outside `outputs/`.
8. Resource stays above thresholds.
9. No active external process/container harmed.

## Resource snapshot required

Before and after each real smoke:

```bash
free -h
cat /proc/meminfo | grep -E 'MemAvailable|CommitLimit|Committed_AS|SwapFree'
df -h . /home
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
nvidia-smi pmon -c 1
docker ps --filter label=com.facespeed.project=NVIDIARiva-Audio2Face-facespeed
```

## Test output log format

Write to `logs/sessions/facespeed-safe-completion.md`:

```text
[time] Phase 5 Smoke
Status: PASS/BLOCKED/REDO
Input: <redacted safe sample>
Artifacts:
- outputs/smoke/...
Resource before:
- ...
Resource after:
- ...
Evaluation:
- WAV valid: yes/no
- A2F result valid: yes/no
- UI verified: yes/no
Next:
- ...
```

## PASS/ASK/REDO/BLOCKED

PASS when:

- Required smoke level artifacts exist and pass evaluation.
- Resource remains above thresholds.
- No secret/log leak.
- UI/manual check done if claiming frontend complete.

ASK when:

- Need to run GPU/container.
- Need choose A2F API/image.
- Need accept non-ideal output.

REDO when:

- WAV invalid.
- State order wrong.
- Result missing despite claimed success.
- Error hidden or unsafe.

BLOCKED when:

- Resource threshold fail.
- Riva/A2F unavailable.
- NGC/license/image missing.
- User has not approved GPU smoke.

## Docs/logs

- Summarize smoke result in docs accuracy notes.
- Keep raw logs local and gitignored.

## Close Comment

Status: PASS for mock/non-GPU smoke; BLOCKED for real NVIDIA smoke
Closed at: 2026-05-20 16:53
Evidence:
- Preflight showed target ports available, but memory commit headroom below 10% reserve gate, blocking heavy GPU/container smoke.
- Mock smoke job completed with artifacts under `outputs/smoke`.
- State transition order matched expected pipeline algorithm.
- Result JSON contained `{"status":"mock_completed"}`.
- `backend/.venv-linux/bin/python -m pytest backend tests`: 25 passed.
- `npm --prefix frontend test`: 3 passed.
- `npm --prefix frontend run build`: PASS with existing FaceViewer chunk-size warning.
- Added `docs/phase-reports/phase-6-smoke-output-evaluation.md`.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 06 - Smoke Output Evaluation`
Next plan: `plans/plan-07-docs-readme-cicd.md`
Notes:
- Real NVIDIA smoke remains blocked until official Riva/A2F image tags/API are verified, containers are started after user confirmation, and resource preflight passes.
- No GPU/container work was executed in this phase.
