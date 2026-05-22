# Plan: Smooth Mouth Animation

- Created: 2026-05-22 13:09
- Updated: 2026-05-22 13:18
- Status: closed
- Related log: logs/fixes/smooth-mouth-animation.md

## Goal
Make the 3D face mouth movement less stiff and less coarse while keeping the model static and still driven by the generated audio timeline.

## Scope
- In: browser viseme timeline generation, frontend timeline sampling, mouth and morph smoothing, test evidence and screenshot proof.
- Out: full NVIDIA Audio2Face NIM integration and new 3D assets.

## Skills
- fixcode-skill
- plan-skill
- frontend-skill
- testing-skill
- logging-skill

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Triage and root cause | done | Sawtooth backend fallback timeline plus nearest-frame frontend sampling causes hard pose jumps |
| 2 | Smooth timeline and renderer | done | Backend audio envelope timeline, frontend interpolation and damping added |
| 3 | Verify by tests and browser proof | done | 33 backend tests, 3 frontend tests, frontend build, Playwright proof image/report |
| 4 | Close log and report | done | `logs/fixes/smooth-mouth-animation.md` updated |

## Verification
- Backend pytest for timeline/client behavior.
- Frontend unit test and production build.
- Playwright browser run with Riva-backed job, captured screenshot and runtime dataset.

## Close criteria
- Mouth no longer jumps frame-to-frame in fallback timeline.
- Model remains non-rotating.
- Browser proof image shows visible 3D face and open mouth from generated audio.
- Tests pass or any blocker is documented.
