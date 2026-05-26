# Voice RAG Chatbot Handoff

- Time: 2026-05-26 09:14 +07
- Status: provider-backed local runtime pass
- Main plan: `plans/plan-voice-rag-chatbot.md`
- Session log: `logs/plans/voice-rag-chatbot.md`

## Current State

The repository now has the provider-backed Voice RAG path: backend contracts, Docling PDF parsing, local document/embedding storage, PDF validation, chunk/citation models, embedding search, rerank, agent trace contracts, real Riva ASR, Riva TTS output, avatar timeline output, and a Voice RAG UI shell.

Current phase state:

| Phase | Status | Note |
| --- | --- | --- |
| 1. Runtime discovery | done | Riva ASR, Docling, embedding, rerank, and existing chatbot services checked. |
| 2. Backend contracts | done | Models/endpoints/config are implemented and covered by backend tests. |
| 3. Riva ASR | done | `facespeed-riva-asr` runs on `127.0.0.1:6052`; `/api/voice/transcribe` returns `source: riva-asr`. |
| 4-9. RAG/UI implementation | done | Docling ingestion, embedding search, rerank, voice answer, and production UI are wired. |
| 10-12. Docs/security/full QA | done | Provider-backed API/browser/audio/video/mobile evidence exists in `.cache/facespeed/evidence/release-readiness-2026-05-23/`. |

## Verified Runtime Facts

Riva:

- Container: `riva-speech`
- Image: `nvcr.io/nvidia/riva/riva-speech:2.19.0`
- TTS container remains reachable at `127.0.0.1:6051`.
- ASR runtime is a separate `facespeed-riva-asr` container on `127.0.0.1:6052`.
- ASR was provisioned with Riva 2.19.0 Conformer English offline ASR plus punctuation.
- Combined ASR+TTS model loading exceeded available VRAM, so the working ASR runtime loads only offline ASR plus punctuation with single-request batch tuning.
- Recreate ASR locally with `scripts/provision-riva-asr-local.sh`.

Docling parse service:

- Base URL: `http://127.0.0.1:8005`
- Health: `GET /health`
- Parse endpoint from OpenAPI: `POST /api/v1/parse`
- Purpose: PDF to Markdown by Docling with GPU acceleration.

Embedding/rerank service:

- Base URL: `http://127.0.0.1:8006`
- Health: `GET /health`
- Embedding: `POST /api/v1/embed`
- Rerank: `POST /api/v1/rerank`
- Provider verification result: embeddings returned 2048-dimensional vectors; rerank placed the relevant voice RAG document above unrelated text.

Existing chatbot backend:

- Base URL: `http://127.0.0.1:9000`
- OpenAPI title: `Chatbot Multi-Agent Bách Việt`
- Treat it as a reference or integration candidate only. This project still needs its own focused voice RAG contracts.

## Resume Checklist

Continue from final verification/close:

1. Keep Docling parsing and embedding/rerank providers as the only main retrieval path.
2. Keep `RIVA_ASR_HOST/RIVA_ASR_PORT` separate from `RIVA_HOST/RIVA_PORT`.
3. Open the app through nginx proxy `http://127.0.0.1:6300/` unless directly debugging frontend/backend.
4. Re-run backend, frontend, browser, audio, retrieval, and security evidence after any change.
5. Close the plan only after final hygiene is complete.

Provider-backed evidence:

- `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-rag-evidence.pdf`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-report.json`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-output-answer.wav`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-output-animation.json`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-output-audio-asr.json`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-avatar-3d-moving.webm`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/app/02-chat-answer-avatar.png`
- `.cache/facespeed/evidence/release-readiness-2026-05-23/app/11-mobile-chat.png`
- `docs/assets/voice-rag-avatar-demo.gif`

Implemented endpoints:

- `POST /api/voice/transcribe`
- `POST /api/voice/chat`
- `POST /api/documents`
- `GET /api/documents`
- `GET /api/documents/{id}`
- `GET /api/documents/{id}/chunks`
- `POST /api/rag/search`
- `GET /api/chat/turns/{id}`

## Files To Open Tomorrow

- `plans/plan-voice-rag-chatbot.md`
- `logs/plans/voice-rag-chatbot.md`
- `README.md`
- `.env.example`
- `backend/src`
- `frontend/src`
