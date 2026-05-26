# Voice RAG Chatbot Plan Log

## 2026-05-22 16:53

Created the plan for upgrading FaceSpeed Studio into a voice RAG chatbot.

Skills applied:

- `plan-skill`: required persisted plan with phases, verification, risks, and close criteria.
- `frontend-skill`: required because the main UI must become a production voice RAG interface, not a dashboard or TTS form.

Current repo snapshot:

- Existing working path is Riva TTS plus browser avatar animation.
- Backend has `RivaTtsClient`, `JobService`, artifact routes, service/system routes, and A2F/browser viseme animation.
- Frontend currently has Studio, Operations, Activity, and Setup pages.
- There is no current ASR/STT client, Docling client, document ingestion service, embedding/rerank service, or multi-agent RAG orchestration.
- `.env.example` currently has Riva TTS/A2F settings but no Docling/RAG/ASR settings.

Key planning decisions:

- English is the first production implementation target.
- Vietnamese must appear in the language model and document metadata design, but full Vietnamese voice chat can be a later milestone.
- The "analysis agent" mentioned in the example is folded into the Lead agent's query-analysis responsibility so the first product loop still has exactly four agents: Lead, Search, Review, Teacher.
- RAG must use wiki-style linked chunks: section hierarchy, prev/next, citation, shared entity/term, and semantic neighbor links.
- Docling API port/schema is treated as a discovery requirement before implementation.
- Riva ASR availability is treated as a discovery requirement because the current app only proves Riva TTS.

Created:

- `plans/plan-voice-rag-chatbot.md`

## 2026-05-22 16:58

Started Phase 1: runtime discovery.

Discovery goals:

- Verify whether current Riva endpoint exposes ASR/STT, not only TTS.
- Locate the local Docling API process/port and identify its health/upload contract.
- Record current repo/runtime state before implementation.

## 2026-05-22 17:06

Phase 1 discovery completed.

Repo/runtime:

- Branch is `master`, tracking `origin/master`.
- Only new plan file is untracked in source view; logs remain under ignored `logs/` per repo policy.
- Existing app is still running:
  - Backend: `127.0.0.1:8020`.
  - Frontend: `127.0.0.1:6310`.

Riva:

- Running container: `riva-speech`.
- Image: `nvcr.io/nvidia/riva/riva-speech:2.19.0`.
- Docker command: `start-riva --riva-uri=0.0.0.0:50051 --asr_service=false --tts_service=true --nlp_service=false`.
- Python package exposes `riva.client.ASRService`, `RecognitionConfig`, and ASR methods.
- Direct ASR verification against `127.0.0.1:50051` returned gRPC `UNIMPLEMENTED`.
- Conclusion: current runtime supports TTS only. Voice chatbot implementation must report ASR as blocked until Riva is restarted/provisioned with ASR models.

Docling / RAG support services:

- `parse-data` service found at `http://127.0.0.1:8005`.
  - `GET /health` returns ok.
  - `POST /api/v1/parse` is documented in OpenAPI.
  - OpenAPI description says PDF to Markdown by Docling with GPU acceleration.
- `embedding` service found at `http://127.0.0.1:8006`.
  - `GET /health` returns ok.
  - `POST /api/v1/embed` works.
  - Embedding verification returned 2 vectors with dimension 2048.
  - `POST /api/v1/rerank` works.
  - Rerank verification ranked the voice RAG document above unrelated text.
- Existing chatbot backend found at `http://127.0.0.1:9000`.
  - Exposes RAG/session endpoints including `/api/v1/rags/rag-contract-fast`, `/api/v1/rags/rag-upload`, and `/api/v1/rags/history`.
  - Treat as reference/integration candidate only; this FaceSpeed project still needs its own focused voice RAG contracts.

Phase 1 outcome:

- Marked Phase 1 as `done`.
- Next phase should define backend contracts and config around:
  - `RIVA_ASR_*`.
  - `DOCLING_API_BASE_URL=http://127.0.0.1:8005`.
  - `EMBEDDING_API_BASE_URL=http://127.0.0.1:8006`.
  - RAG storage/index settings.

## 2026-05-22 17:08

Started Phase 2: backend contracts and data models.

Immediate design constraints from Phase 1:

- ASR must be modeled as a real service path but can return `unavailable` until Riva is restarted with ASR enabled.
- Docling and embedding/rerank should be configurable HTTP clients, not hardcoded ports.
- Voice chat turn response must be able to include partial outputs: transcript-only, RAG answer, citations, TTS audio, animation URL, and agent trace summary.

## 2026-05-22 17:25

Paused work by user request and wrote handoff notes for the next session.

Updated:

- `plans/plan-voice-rag-chatbot.md`
- `docs/voice-rag-chatbot-handoff.md`
- `README.md`

Current state to remember tomorrow:

- Phase 1 is complete.
- Phase 2 is in progress but no backend contract/code implementation has started yet.
- Current shipped app remains the English Riva TTS + browser 3D avatar Studio.
- Riva ASR is not currently available because the running container has `--asr_service=false`; direct ASR verification returned gRPC `UNIMPLEMENTED`.
- Docling is reachable at `http://127.0.0.1:8005`.
- Embedding/rerank is reachable at `http://127.0.0.1:8006`.
- Existing chatbot backend at `http://127.0.0.1:9000` can be studied, but should not be copied blindly.

Next safe task:

- Continue Phase 2 by writing backend contracts, config keys, and tests for voice turns, transcripts, documents, wiki chunks, citations, retrieval output, and agent traces.

## 2026-05-22 22:20

Resumed the Voice RAG plan and applied the updated rule from the user: no substitute path for the main runtime. If ASR is unavailable, the product must report the error instead of pretending voice input works.

Implemented:

- Backend RAG contracts in `backend/src/models/rag.py`.
- RAG service and endpoints for status, PDF ingestion, document listing/detail/chunks, search, voice chat turns, and turn lookup.
- Strict `/api/voice/transcribe` unavailable response while current Riva ASR is disabled.
- Voice RAG frontend shell with PDF upload, mic recording action, ASR blocked state, citations, agent trace output, and avatar output surface.
- Config keys in `.env.example`.
- README and handoff status updates.

Validation:

- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests` -> 38 passed.
- `npm --prefix frontend test -- --run` -> 3 passed. jsdom reports canvas `getContext` as not implemented, so browser evidence remains required for 3D.
- `npm --prefix frontend run build` -> passed. Vite reports the existing large Three.js chunk warning.
- Source scan for `fallback`, `planned/limited`, and `seed` across active backend/frontend/plan/docs returned no matches.
- Live QA servers started on backend `127.0.0.1:8120` and frontend `127.0.0.1:6410`; API status returned ASR blocked and frontend root returned HTTP 200.
- Evidence folder created at `.cache/facespeed/evidence/release-readiness-2026-05-23/` with blocker reports. No pass screenshot is claimed.

Blocker:

- Full close criteria cannot pass yet because real microphone transcription is blocked by the running Riva container command `--asr_service=false`.
- Browser screenshot capture is also blocked by missing host library `libasound.so.2` for Playwright Chromium.

## 2026-05-22 22:50

Follow-up from user request: make the UI feel like a landing/product surface, not a dense dashboard, and use popups to keep system thinking compact.

Implemented:

- Rebuilt the Voice RAG screen as a landing-style hero with primary actions, compact status rail, large avatar preview, and a focused current-turn workspace.
- Moved Knowledge, Runtime, and Agent Trace details into modal popups.
- Added `scripts/install-playwright-local-libs.sh` to install Playwright's missing `libasound.so.2` project-locally without sudo.
- Implemented a real `NvidiaRivaAsrClient`; `/api/voice/transcribe` now calls Riva when `RIVA_ASR_ENABLED=true` and reports actual Riva errors.
- Browser evidence refreshed after waiting for the 3D avatar model to load.

Validation:

- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests` -> 38 passed.
- `npm --prefix frontend test -- --run` -> 3 passed.
- `npm --prefix frontend run build` -> passed.
- `RIVA_ASR_ENABLED=true` direct ASR verification reached Riva and returned `UNIMPLEMENTED`, confirming runtime ASR is still not provisioned.
- Evidence image hygiene: four unique PNG hashes, no temporary/log/json/pdf artifacts in evidence.

Remaining blocker:

- Riva model repo contains TTS models only. Current running container command still has `--asr_service=false`, and direct ASR verification returns `UNIMPLEMENTED`.

## 2026-05-22 23:30

Resolved the Riva ASR runtime blocker for the local product pipeline.

Runtime work:

- Provisioned Riva ASR model repo from NGC with `rmir_asr_conformer_en_us_str`, `rmir_asr_conformer_en_us_ofl`, and punctuation.
- Initial combined ASR+TTS runtime failed with GPU OOM while loading all models.
- Created an ASR-only offline runtime repo and tuned Riva batch sizes down for a single local product turn:
  - `max_batch_size: 1`
  - `acoustic_model_max_execution_batch_size: 1`
  - `feature_extractor.max_execution_batch_size: 1`
- Started `facespeed-riva-asr` on `127.0.0.1:50151`.
- Kept existing Riva TTS service on `127.0.0.1:50051`.
- Added `scripts/provision-riva-asr-local.sh` so the local ASR runtime can be recreated inside project cache without sudo.

Code updates:

- Added `RIVA_ASR_HOST` and `RIVA_ASR_PORT`.
- Fixed ASR client to call the ASR endpoint while TTS continues to call the TTS endpoint.
- Added an editable transcript field in the Voice RAG product surface so users can review or correct ASR output before running the cited answer.

Validation:

- Direct Riva ASR call on `50151` returned transcript from a real WAV fixture.
- Direct Riva TTS call on `50051` returned audio while ASR runtime was online.
- Backend runtime chain passed:
  - PDF upload/index.
  - `/api/voice/transcribe` -> `source: riva-asr`.
  - `/api/voice/chat` -> `reviewStatus: pass`.
  - audio artifact -> RIFF WAV.
  - animation artifact -> 1015 frames.
- Browser evidence captured:
  - `.cache/facespeed/evidence/release-readiness-2026-05-23/app/05-desktop-asr-online-cited-answer.png`
  - `.cache/facespeed/evidence/release-readiness-2026-05-23/app/06-desktop-record-button-riva-asr-cited-answer.png`
- Test suite:
  - `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests` -> 38 passed.
  - `npm --prefix frontend test -- --run` -> 3 passed.
  - `npm --prefix frontend run build` -> passed.

Remaining product work at that point:

- The current RAG slice was still local keyword/graph retrieval. This was superseded by the 2026-05-23 provider-backed integration below.

## 2026-05-23 00:30

Completed the provider-backed RAG integration gate.

Implemented:

- Added `DoclingClient` for `POST /api/v1/parse` and made provider errors fail the request instead of using an in-process parser fallback.
- Added `EmbeddingRerankClient` for `POST /api/v1/embed` and `POST /api/v1/rerank`.
- Reworked `RagService` so PDF ingestion uses Docling Markdown, persists section/chunk graph plus embeddings, and search uses vector similarity, graph neighbor expansion, and rerank.
- Added config for Docling/embedding/rerank timeouts and RAG thresholds.
- Tightened voice chat so missing TTS/audio/avatar artifacts return an error instead of a partial success.
- Removed the old procedural canvas face rig from `FaceViewer`; initial canvas now shows only a loading bar until the GLB model is loaded.

Validation:

- `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest tests -q` -> 39 passed.
- `npm --prefix frontend test -- --run` -> 3 passed. jsdom still warns that canvas `getContext` is not implemented, so browser evidence was used for 3D.
- `npm --prefix frontend run build` -> passed with the existing large bundle warning.
- Runtime provider-backed chain passed on backend `127.0.0.1:8020`:
  - uploaded valid `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-rag-evidence.pdf`;
  - Docling parsed the PDF;
  - embedding/rerank returned a cited answer with confidence `0.762`;
  - Riva ASR transcribed `input-question.wav`;
  - Riva TTS generated `docling-output-answer.wav`;
  - avatar animation produced `docling-output-animation.json` with 1,655 frames.
- Browser evidence passed:
  - desktop UI with cited answer: `.cache/facespeed/evidence/release-readiness-2026-05-23/app/02-chat-answer-avatar.png`;
  - mobile UI answer view with no horizontal overflow: `.cache/facespeed/evidence/release-readiness-2026-05-23/app/11-mobile-chat.png`;
  - avatar movement recording: `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-avatar-3d-moving.webm`, jaw delta `0.369`, `mouthRig=model-morphs`;
  - README GIF banner regenerated from the real browser canvas: `docs/assets/voice-rag-avatar-demo.gif`.
- Riva ASR back-transcribed `docling-output-answer.wav`; meaning passes, with minor ASR wording errors such as `docking` for `Docling`.

Remaining:

- Final hygiene and plan close can be done after any additional user-requested QA artifact.
