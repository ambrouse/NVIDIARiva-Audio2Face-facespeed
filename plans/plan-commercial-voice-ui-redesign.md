# Plan: Commercial Voice UI Redesign

- Created: 2026-05-23 00:39
- Updated: 2026-05-23 01:18
- Status: completed
- Related log: logs/plans/commercial-voice-ui-redesign.md

## Goal

Rebuild the Voice RAG frontend into a commercial product workspace: compact voice-first home, left icon navigation, clean chat history, hold-to-talk control, polished avatar panel, model selection, model sizing, and more natural facial expression.

## Scope

- In:
  - Replace oversized landing hero with product app layout.
  - Add left icon rail navigation.
  - Make Voice RAG home show only the essential voice button and chat history as the primary workflow.
  - Move knowledge/runtime/trace/settings into popups or compact side controls.
  - Add multiple selectable face model entries and size control.
  - Improve avatar facial motion with natural idle, blink, micro head movement, eye expression, and expression intensity.
  - Capture desktop, mobile, model picker, popup, and avatar evidence screenshots/videos.
- Out:
  - New backend RAG architecture changes unless needed for UI contract.
  - Downloading unverified third-party avatar assets without license review.

## Skills

- plan-skill
- frontend-skill
- testing-skill

## Phases

| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Benchmark current voice/avatar product UI patterns | done | Tavus, ElevenLabs, HeyGen docs/search reviewed |
| 2 | Rebuild navigation and home layout | done | `test/release-readiness-2026-05-23/app/01-home-voice-chat.png` |
| 3 | Add model picker, size controls, and expression controls | done | `app/03-avatar-picker-popup.png`, `app/07-atlas-calm-model-selected.png` |
| 4 | Improve facial animation naturalness | done | `browser-report.json`: jaw delta 0.404, blink max 0.702 |
| 5 | Full browser QA and polish pass | done | `test/release-readiness-2026-05-23/` |

## Verification

- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- Browser QA at desktop and mobile viewports.
- Evidence screenshots:
  - home voice/chat
  - model picker/settings popup
  - knowledge popup
  - trace popup
  - mobile voice/chat
  - avatar animation with jaw/face metrics

## Close Criteria

- Home no longer looks like a landing page or dashboard.
- Main screen focuses on voice action and chat history.
- Left nav is icon-based and compact.
- User can select a model and adjust face size.
- Avatar motion reads more expressive and natural.
- Screenshots are reviewed visually and do not show overlap, awkward crop, loading, or broken state.
