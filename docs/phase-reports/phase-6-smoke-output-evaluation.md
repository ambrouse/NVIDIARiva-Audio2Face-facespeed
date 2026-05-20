# Phase 6 Smoke Output Evaluation

Time: 2026-05-20

## Scope

This phase verified the mock/non-GPU pipeline output contract. Real NVIDIA Riva and Audio2Face smoke tests were not run because the project containers are not started yet and the resource preflight reported memory commit headroom below the 10% reserve gate.

## Preflight

- Target ports `8020`, `6210`, `50100`, and `8040` appeared available.
- RAM and disk were above reserve thresholds.
- Memory commit headroom was below the 10% reserve gate during preflight, so heavy GPU/container smoke tests remain blocked.

## Mock smoke input

```text
hello from facespeed smoke
```

## Mock smoke output

- Job state: `completed`.
- Audio artifact: `outputs/smoke/audio/<job-id>.wav`.
- A2F result artifact: `outputs/smoke/a2f/<job-id>.json`.
- Result JSON: `{"status":"mock_completed"}`.
- Job log existed and captured state transitions.

## Algorithm evaluation

Expected state order:

```text
validating_text -> generating_speech -> speech_ready -> sending_to_a2f -> animating_face -> completed
```

Observed state order matched the expected order.

## Tests

```text
backend/.venv-linux/bin/python -m pytest backend tests
25 passed

npm --prefix frontend test
3 passed

npm --prefix frontend run build
PASS
```

Frontend build still reports a non-fatal FaceViewer chunk-size warning.

## Real NVIDIA status

Blocked until:

1. Official Riva container image/tag is verified.
2. Official Audio2Face container image/tag/API contract is verified.
3. User explicitly confirms image pull/container start.
4. Resource preflight passes all 10% reserve gates.

## Result

Status: PASS for mock/non-GPU smoke. BLOCKED for real NVIDIA smoke.
