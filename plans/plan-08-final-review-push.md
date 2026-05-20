# Plan 08: Final Review and Push

## Mục tiêu

Review toàn bộ thay đổi, chạy test/release gates, security review, rồi commit/push chỉ khi user xác nhận.

## Skill phải đọc trước khi làm

- `testing-skill`
- `security-skill`
- `push-code-skill`
- `documentation-skill`
- `logging-skill`
- `readme-style` nếu README thay đổi

## Phạm vi

Làm:

1. Review git diff/status.
2. Run tests/build.
3. Security review.
4. Docs/log completion.
5. Commit after user request.
6. Push after user request.

Không làm:

- Không commit nếu user chưa yêu cầu.
- Không push nếu user chưa xác nhận.
- Không skip hooks/tests.
- Không amend existing commit trừ khi user yêu cầu.

## Pre-final checklist

### Repo hygiene

```bash
git status --short
git diff --stat
git diff
```

PASS if:

- No secret/token.
- No logs/outputs/cache/model assets tracked.
- Changes match plan scope.

### Tests

Run appropriate:

```bash
python -m pytest tests
backend/.venv-linux/bin/python -m pytest backend tests
npm --prefix frontend test
npm --prefix frontend run build
```

PASS if all required non-GPU tests pass.

If NVIDIA smoke blocked, docs must say blocked and not claim pass.

### Security review

Check:

1. Secret/key leak.
2. CORS localhost.
3. No command injection.
4. No path traversal.
5. Docker commands scoped.
6. No public bind.
7. Dependency changes justified.
8. CI safe.

PASS if no critical/high unresolved.

ASK if risk acceptance needed.

### Docs/logs

- Phase close comments updated.
- `logs/sessions/facespeed-safe-completion.md` has final summary.
- README/docs match behavior.

## Commit protocol

Only if user says commit.

1. Run git status/diff/log.
2. Stage specific files only.
3. Commit with clear message and timestamp/context.
4. Include required co-author trailer per Claude Code git protocol.

Do not use `git add -A` blindly.

## Push protocol

Only if user says push.

1. Check remote/branch.
2. Push normal, no force.
3. If remote conflict, ask user.

## PASS/ASK/REDO/BLOCKED

PASS when:

1. Tests/build pass or blocked documented.
2. Security review pass.
3. Docs/readme/logs updated.
4. Commit/push done only with explicit user approval.

ASK when:

- Commit/push requested but tests fail.
- Remote branch conflict.
- Need include/exclude specific files.
- Need risk acceptance.

REDO when:

- Secret in diff.
- Tests fail due code.
- Docs claim unsupported behavior.
- CI unsafe.

BLOCKED when:

- Missing credentials/remote access.
- Environment cannot run tests and install not approved.

## Final log format

```text
[time] Final Review
Status: PASS/BLOCKED
Tests:
- backend: pass/fail/blocked
- frontend: pass/fail/blocked
- setup: pass/fail/blocked
Security: pass/fail
Docs: updated/not updated
Commit: <hash or not requested>
Push: <remote result or not requested>
Next:
- ...
```

## Close Comment

Status: PASS for review/test/security gates; commit/push not requested
Closed at: 2026-05-20 17:09
Evidence:
- `backend/.venv-linux/bin/python -m pytest backend tests`: 25 passed.
- `npm --prefix frontend test`: 3 passed.
- `npm --prefix frontend run build`: PASS with existing FaceViewer chunk-size warning.
- `bash -n scripts/setup.sh`: PASS.
- Tracked NVIDIA key grep: PASS.
- Tracked runtime/cache artifact check: PASS.
- Working diff secret scan: PASS.
- README/docs do not claim real NVIDIA pass.
- Docker/NVIDIA real pull/start remains blocked and was not run.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 08 - Final Review`
Next plan: N/A
Notes:
- Commit and push were not performed because user has not explicitly requested them.
- If user requests commit, stage specific files only and follow push-code/git safety protocol.
