# Plan: Frame Accurate Mouth Sync

- Created: 2026-05-22 13:26
- Updated: 2026-05-22 13:36
- Status: closed
- Related log: logs/fixes/frame-accurate-mouth-sync.md

## Goal
Make the 3D face mouth motion visibly smoother, better aligned with Riva audio, and more presentable, with frame-level browser evidence and image/video proof.

## Scope
- In: browser frame capture, timeline/lipsync generation, frontend morph application, visual polish for the existing James GLB preview, test evidence package.
- Out: full A2F-3D NIM production inference, Unreal/MetaHuman runtime, or paid/external avatar services.

## Skills
- fixcode-skill
- frontend-skill
- testing-skill
- logging-skill

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Capture current frame behavior | done | Baseline video, screenshots, and `baseline/frame-report.json` |
| 2 | Root cause and fix | done | Text+audio viseme timeline, 60 FPS output, frontend morph scaling, warmer material/light |
| 3 | Verify smoothness with browser frame metrics | done | After video, open-mouth screenshot, `after/frame-report.json` |
| 4 | Package evidence and close | done | Evidence README, log update, secret scan and image hash check |

## Verification
- Playwright video of the app running a Riva-backed job.
- Frame-level JSON/summary comparing audio time, jaw, mouth width/smile and step/jerk metrics.
- Browser screenshot with model visible and speaking.
- Backend/frontend tests and frontend build.

## Close criteria
- Evidence includes pass screenshot/video and frame metrics.
- Motion uses real audio timing rather than a disconnected visual oscillator.
- Model remains visible, non-rotating, and visually cleaner.
- Test suite passes or blockers are documented.
