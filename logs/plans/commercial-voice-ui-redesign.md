# Commercial Voice UI Redesign Log

## 2026-05-23 00:39

Started the commercial UI/animation redesign after user review.

Reference scan:

- Tavus positions conversational video agents around a face-to-face experience and low-latency conversation.
- ElevenLabs voice agent examples emphasize a simple voice entry point, agent state, and chat/voice continuity.
- HeyGen avatar docs emphasize avatar selection and video/avatar creation rather than exposing system internals first.

Design decision:

- Replace the large hero and dashboard-like status blocks with a compact product workspace.
- Make the first screen a conversation surface: icon rail, chat history, hold-to-talk voice button, avatar panel.
- Move runtime/source/trace details into popups.
- Add face model selection and face size/expression controls.
- Improve facial motion with idle/head/blink/expression dynamics on top of timeline-driven mouth shapes.

## 2026-05-23 00:58

Implemented the first commercial redesign pass.

Changes:

- Replaced the top navbar/landing hero with a left icon rail and compact product workspace.
- Rebuilt the Voice RAG home around chat history, hold-to-talk, typed message submit, source/runtime/trace popups, and a right-side avatar panel.
- Added avatar profile picker, face size slider, and expression slider.
- Updated `FaceViewer` to accept model/profile controls and added blink, brow, cheek, smile, breathing, and subtle head movement over timeline mouth animation.
- Removed the visually poor `a2f-james-v3.glb` option from the production picker after browser review showed blank eyes and bust-like rendering.
- Added `lucide-react` for production-grade icon navigation and controls.

Validation:

- `npm --prefix frontend test -- --run` -> 3 passed.
- `npm --prefix frontend run build` -> passed with the existing large bundle warning.
- Browser QA evidence saved in `test/release-readiness-2026-05-23/`.
- Browser report: 0 console errors, 0 page errors, 0 failed HTTP responses, `mouthRig=model-morphs`, jaw delta `0.404`, blink max `0.702`, mobile horizontal overflow false.

## 2026-05-23 01:12

Asset cleanup pass:

- Deleted unused browser model assets from `frontend/public/models/`: `a2f-james-v3.glb` and `head.fbx`.
- Kept only the production-safe `readyplayer-talk-arkit.glb` asset in the app bundle.
- Updated the phase report to mark the James v3 GLB as a removed proof asset, not a production frontend dependency.

## 2026-05-23 01:18

Final product polish pass:

- Moved avatar profile, face size, and expression controls out of the home surface and into the Avatar popup.
- Kept the home view focused on chat history, hold-to-talk, compact source/runtime/trace actions, and the live 3D face/audio panel.
- Replaced the old Operations service-manager view with provider-backed RAG runtime cards so the UI no longer reports mock/container fallback state.
- Re-captured full browser evidence after waiting for the first stable WebGL frame.
- Final browser report: 0 console errors, 0 page errors, 0 failed HTTP responses, `meshCount=4`, jaw delta `0.425`, blink max `0.698`, mobile overflow false.

## 2026-05-23 01:28

Audio playback polish:

- Removed the visible browser audio control bar from the avatar panel.
- Added autoplay for the latest RAG voice answer and a single replay icon for the newest answer only.
- Added frontend cleanup for replaced audio URLs, including pausing/resetting the previous audio element and revoking old blob URLs when applicable.
- Added a regression test proving the audio element has no `controls` attribute while replay remains available.
- Browser evidence: 1 hidden audio element, 0 visible audio controls, 1 replay button, audio playing with `paused=false`.
