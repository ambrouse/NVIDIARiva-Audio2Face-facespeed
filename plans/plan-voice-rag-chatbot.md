# Plan: Voice RAG Chatbot

- Created: 2026-05-22 16:53
- Updated: 2026-05-23 00:30
- Status: provider-backed runtime pass
- Related log: logs/plans/voice-rag-chatbot.md

## Goal

Upgrade FaceSpeed Studio from a text-to-speech avatar studio into a local voice RAG chatbot:

- User speaks into the browser.
- Riva ASR converts speech to text.
- The text goes through a structured RAG pipeline over uploaded PDF knowledge.
- A multi-agent loop produces a grounded answer.
- Riva TTS converts the answer to voice.
- The existing 3D avatar speaks the answer with mouth animation synchronized to the generated voice.

The first production target is English. Vietnamese must be represented in the language architecture and ingestion model, but Vietnamese chat/voice quality can ship in a later phase after English is stable.

## Scope

- In:
  - Add language selector with `English` and `Vietnamese`, with English enabled first and Vietnamese available for document metadata/indexing.
  - Add Riva ASR/STT client and backend voice-chat endpoint.
  - Add audio capture/upload path from frontend to backend.
  - Add PDF ingestion through the local Docling API running on this machine.
  - Support English and Vietnamese PDF parsing metadata from day one.
  - Build a wiki-style RAG index: document sections as linked nodes, semantic chunks, references, adjacent links, entity links, page citations, embeddings, and rerank.
  - Add multi-agent orchestration:
    - Lead agent.
    - Search agent.
    - Teacher agent.
    - Review agent.
  - Keep agents concise at runtime: large internal context, short structured messages, bounded retry loops.
  - Redesign frontend as a production voice RAG assistant, not a simple TTS form.
  - Preserve existing Riva TTS + 3D avatar mouth animation as the final answer output path.
  - Add backend/frontend tests, browser evidence, audio evidence, retrieval evidence, and source-citation evidence.
  - Update setup, `.env.example`, README, and CI where needed.
- Out:
  - Full Vietnamese voice chatbot quality in the first implementation milestone.
  - Cloud deployment, auth, billing, multi-tenant storage, or public hosting.
  - Training custom ASR/TTS/embedding/reranker models.
  - Replacing Riva if the local Riva ASR model is not installed.
  - Real-time full-duplex interruption/barge-in until base turn-based voice chat is stable.

## Skills

- plan-skill: phase tracking, evidence, logs, close criteria.
- frontend-skill: redesign production voice RAG UI, responsive states, accessibility, no decorative dead controls.
- backend-skill: API contracts, service boundaries, config, cleanup, Riva/Docling/RAG services.
- testing-skill: backend integration tests, browser tests, evidence screenshots/audio/retrieval reports.
- security-skill: file upload safety, prompt injection, citation handling, secrets, local service boundaries.
- documentation-skill: setup/API/RAG docs and operator notes.
- logging-skill: concise implementation logs.
- readme-style: update README/banner/evidence after implementation.
- push-code-skill: only if user explicitly asks to push after completion.

## Architecture

### Target User Flow

```text
Mic audio
  -> Riva ASR
  -> transcript
  -> Lead agent
  -> query analysis / decomposition
  -> Search agent
  -> embedding search + wiki graph expansion + rerank
  -> evidence context
  -> Review agent
  -> retry search/analysis if weak
  -> Teacher agent
  -> final grounded answer
  -> Riva TTS
  -> WAV + viseme/blendshape timeline
  -> 3D avatar speaks answer
```

### Backend Services

| Service | Responsibility |
| --- | --- |
| `RivaAsrClient` | Speech audio to transcript. |
| `RivaTtsClient` | Existing text to voice answer. |
| `DoclingClient` | Call local Docling API for PDF parse/OCR/layout extraction. |
| `DocumentIngestionService` | Validate PDF, parse, normalize language metadata, build chunks/nodes. |
| `WikiChunkGraphService` | Build chunk graph: parent/child, prev/next, citation, entity, term, semantic links. |
| `EmbeddingService` | Create/query embeddings; provider configurable. |
| `RerankService` | Rerank candidate chunks; provider configurable. |
| `RagSearchService` | Hybrid retrieval, graph expansion, rerank, context packing. |
| `AgentOrchestrator` | Lead/search/review/teacher loop, retries, concise messages. |
| `VoiceChatService` | End-to-end turn orchestration and artifact serving. |

### Frontend Product Shape

The main page becomes a voice RAG conversation surface:

- Left/primary area:
  - Conversation transcript.
  - Push-to-talk / recording state.
  - Language selector: English active, Vietnamese available for document metadata/indexing.
  - Current answer audio playback.
  - Citations attached to each answer.
- Right/secondary area:
  - 3D avatar preview speaking the answer.
  - Knowledge source panel: uploaded PDFs, ingestion status, chunk/index stats.
  - Retrieval trace drawer: only for advanced/debug mode, not first-viewport clutter.
- Support pages:
  - Knowledge library.
  - Runtime/Services.
  - Logs/Activity.
  - Setup/Readiness.

## RAG Design

### Wiki-Style Chunking

PDF ingestion must produce a graph, not just a flat list:

- `Document`: file metadata, language, title, checksum, ingestion status.
- `SectionNode`: title path, heading level, page range, parent/children.
- `ChunkNode`: text chunk with page, bbox if available, title path, language, token count.
- `LinkEdge`:
  - `parent_section`
  - `child_section`
  - `previous_chunk`
  - `next_chunk`
  - `same_page`
  - `citation_reference`
  - `shared_entity`
  - `glossary_term`
  - `semantic_neighbor`
- `Citation`: page, title path, excerpt, source file, confidence.

Chunking rules:

- Prefer Docling structural blocks: title, heading, paragraph, list, table, figure caption.
- Preserve heading hierarchy as title path.
- Target chunk size starts around 300-700 tokens, with overlap only when boundaries are weak.
- Tables should become standalone chunks with a compact text rendering and table metadata.
- Vietnamese and English chunks store language metadata separately.
- Every retrieved answer must cite chunk ids and page/source metadata.

### Retrieval And Rerank

Minimum retrieval path:

1. Normalize transcript/query.
2. Lead agent decomposes or rewrites into concise search intents.
3. Hybrid retrieval:
   - vector top-k over chunk embeddings.
   - keyword scoring when provider search is not configured.
   - graph expansion from high-score nodes to parent/neighbor/reference chunks.
4. Rerank with query + candidate chunk pairs.
5. Context packing:
   - group by source/section.
   - remove duplicates.
   - keep short source excerpts.
   - include citations and missing-info markers.
6. Review agent checks grounding, relevance, and answerability.

## Agent Contracts

### Lead Agent

Purpose: own the turn, decompose the request, coordinate other agents, decide retries, and produce the final orchestration decision.

Runtime style:

- Internal context can be rich.
- External message to other agents must be short JSON.
- No long prose between agents.

Output shape:

```json
{
  "turn_id": "...",
  "language": "en",
  "user_transcript": "...",
  "search_intents": ["..."],
  "constraints": ["answer with citations", "say when not found"],
  "next_agent": "search"
}
```

### Search Agent

Purpose: retrieve and summarize evidence from the RAG index.

Output shape:

```json
{
  "found": true,
  "confidence": 0.0,
  "queries_used": ["..."],
  "evidence": [
    {
      "chunk_id": "...",
      "source": "...",
      "page": 1,
      "title_path": ["..."],
      "excerpt": "...",
      "score": 0.0
    }
  ],
  "compact_context": "..."
}
```

### Review Agent

Purpose: decide if evidence is enough, if the answer is grounded, and what to retry when weak.

Review states:

- `pass`
- `retry_search`
- `retry_analysis`
- `not_found`
- `unsafe_or_unanswerable`

Output shape:

```json
{
  "status": "pass",
  "reason": "...",
  "missing": [],
  "retry_instruction": null
}
```

### Teacher Agent

Purpose: write the final user-facing answer from approved evidence.

Requirements:

- Answer naturally and clearly.
- Cite sources/pages.
- Explain if information was not found.
- Keep answer short enough for TTS unless user asks for depth.
- For voice output, prefer concise paragraphs and avoid huge lists.

## Phases

| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Audit current runtime and discover Riva ASR + Docling API availability | done | Initial TTS-only runtime identified; Docling/embedding/rerank discovered |
| 2 | Define backend contracts and data models for voice turns, documents, chunks, citations, agents | done | `backend/src/models/rag.py`, `backend/tests/test_rag_api.py` |
| 3 | Add Riva ASR/STT service and voice input endpoint | done | `facespeed-riva-asr` runs on `50151`; `/api/voice/transcribe` returns `source: riva-asr` |
| 4 | Add Docling PDF ingestion path | done | `DoclingClient` parses PDFs through `POST /api/v1/parse`; provider failure returns HTTP error |
| 5 | Implement wiki-style chunk graph and storage | done | Docling Markdown becomes section/chunk graph with prev/next links and persisted embeddings |
| 6 | Implement embedding search, graph expansion, and rerank | done | `EmbeddingRerankClient` drives vector search and rerank; no keyword fallback |
| 7 | Implement four-agent orchestration loop | done | Lead/Search/Review/Teacher trace contracts and pass/not-found tests |
| 8 | Connect answer TTS and 3D avatar output | done | Runtime chain returns WAV and animation artifacts |
| 9 | Redesign frontend into production voice RAG UI | done | Landing-style UI with popup Knowledge/Runtime/Trace evidence captured |
| 10 | Add setup/config/CI/docs | done | `.env.example`, README, handoff, evidence docs updated |
| 11 | Security and robustness hardening | done | PDF validation and provider-error no-fallback regression tests pass |
| 12 | Full QA evidence and close | done | `.cache/facespeed/evidence/release-readiness-2026-05-23/` includes PDF/audio/video/UI/mobile/browser reports |

## Phase Details

### Phase 1: Runtime Discovery

- Confirm current Riva server exposes ASR models, not only TTS.
- Add or verify a `check_riva_asr` setup command.
- Discover local Docling API port and API contract:
  - health endpoint.
  - PDF upload endpoint.
  - response schema.
- Decide initial providers:
  - embedding provider.
  - reranker provider.
  - vector store/local storage.
- Blocker rule:
  - If Riva ASR or Docling API is unavailable, report the blocking error and do not substitute another product path.

### Phase 2: Backend Contracts

- Add models:
  - `VoiceTurn`
  - `Transcript`
  - `ChatAnswer`
  - `Document`
  - `SectionNode`
  - `ChunkNode`
  - `Citation`
  - `AgentTrace`
- Add endpoints:
  - `POST /api/voice/transcribe`
  - `POST /api/voice/chat`
  - `POST /api/documents`
  - `GET /api/documents`
  - `GET /api/documents/{id}`
  - `GET /api/documents/{id}/chunks`
  - `POST /api/rag/search`
  - `GET /api/chat/turns/{id}`

### Phase 3: Riva ASR

- Add `RivaAsrClient`.
- Accept browser-recorded audio format, normalize to Riva-supported PCM/WAV as needed.
- Return transcript with confidence/alternatives if available.
- Test:
  - valid WAV fixture.
  - empty audio.
  - unsupported format.
  - Riva unavailable.
  - timeout.

### Phase 4: Docling PDF Ingestion

- Add `DoclingClient`.
- Add upload validation:
  - extension/content-type.
  - max size.
  - page count where available.
  - path traversal safety.
  - checksum dedupe.
- Parse English and Vietnamese PDFs.
- Preserve:
  - title hierarchy.
  - page number.
  - block type.
  - table text.
  - language metadata.

### Phase 5: Wiki Chunk Graph

- Convert Docling output into linked nodes.
- Build stable chunk ids.
- Store graph in local project storage first.
- Add cleanup/retention settings.
- Test graph invariants:
  - every chunk belongs to a document.
  - every chunk has citation metadata.
  - prev/next edges are symmetric enough to traverse.
  - parent/child section links survive serialization.

### Phase 6: Search, Embedding, Rerank

- Implement embedding index.
- Implement retrieval:
  - query rewrite/decomposition.
  - vector top-k.
  - keyword scoring when provider search is not configured.
  - graph expansion.
  - rerank.
  - context packing.
- Add benchmark fixtures:
  - answer exists in one paragraph.
  - answer needs multiple linked chunks.
  - answer exists in table.
  - answer is not found.
  - English question over English PDF.
  - Vietnamese PDF indexed but Vietnamese chat marked limited until enabled.

### Phase 7: Multi-Agent Loop

- Implement agent prompt files/config:
  - `lead.md`
  - `search.md`
  - `review.md`
  - `teacher.md`
- Use strict structured messages between agents.
- Add bounded loop:
  - max analysis/search retries.
  - review pass threshold.
  - explicit not-found response.
- Add trace:
  - compact, no raw secrets.
  - enough to debug why answer passed/failed.

### Phase 8: Voice Answer + Avatar

- Feed Teacher answer into existing Riva TTS.
- Feed answer WAV into existing animation timeline path.
- Return:
  - transcript text.
  - answer text.
  - citations.
  - audio URL.
  - animation URL.
  - agent trace summary.
- Test end-to-end through backend test client.

### Phase 9: Frontend Voice RAG UI

- Replace "Create a speaking 3D avatar" with a voice-first assistant surface.
- Required states:
  - no document uploaded.
  - uploading/indexing PDF.
  - ready to ask.
  - recording.
  - transcribing.
  - searching.
  - reviewing.
  - speaking answer.
  - no answer found.
  - service unavailable.
  - mobile microphone permission denied.
- UI must show:
  - language selector: English enabled, Vietnamese available for document metadata/indexing.
  - push-to-talk button.
  - transcript bubble.
  - answer bubble with citations.
  - source chips/pages.
  - 3D avatar preview.
  - document library/status.
- Advanced trace should be collapsible and not dominate the end-user screen.

### Phase 10: Setup, CI, Docs

- `.env.example` additions:
  - `RIVA_ASR_*`
  - `DOCLING_API_BASE_URL`
  - `RAG_STORAGE_DIR`
  - `EMBEDDING_PROVIDER`
  - `RERANK_PROVIDER`
  - `VOICE_CHAT_MAX_AUDIO_SECONDS`
  - `PDF_MAX_UPLOAD_MB`
- `setup.sh` additions:
  - check Riva ASR.
  - check Docling.
  - check embedding/rerank provider.
  - initialize local RAG storage.
- CI:
  - backend tests for ingestion/retrieval/orchestration.
  - frontend tests for voice UI states.
  - syntax/secret/runtime artifact checks.
- README:
  - Voice RAG architecture.
  - setup/run.
  - evidence.
  - limitations.

### Phase 11: Security And Robustness

- Prompt injection protection:
  - retrieved docs are evidence, not instructions.
  - system prompts dominate source text.
  - citations required for factual claims.
- Upload security:
  - PDF-only validation.
  - size limits.
  - safe storage paths.
  - no executable extraction.
- Logging:
  - no raw API keys.
  - avoid logging full PDFs or long private user speech by default.
- Rate/timeout:
  - ASR timeout.
  - Docling timeout.
  - embedding/rerank timeout.
  - agent max retries.

### Phase 12: QA Evidence

- Real browser tests:
  - English voice question -> transcript -> RAG answer -> voice answer -> avatar speaking.
  - PDF upload/indexing.
  - citations open/visible.
  - not-found case.
  - mobile voice UI.
- Reports:
  - ASR audio report.
  - TTS audio report.
  - retrieval/rerank report.
  - agent trace report.
  - screenshot set, one per function/state.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Riva server may not have ASR model loaded | Real voice input blocked | Phase 1 discovery; product reports the blocking error until ASR is provisioned |
| Docling API port/schema unknown | PDF ingestion blocked | Make endpoint configurable and document exact discovered contract |
| Embedding/rerank provider unspecified | RAG quality blocked | Start with pluggable provider interface and fixture tests |
| Vietnamese ASR/TTS/retrieval quality may lag | Scope creep | English-first milestone; Vietnamese selector and PDF metadata ready |
| Multi-agent loop can become slow | Bad UX | Short JSON inter-agent messages, max retries, trace summaries |
| Prompt injection from PDFs | Unsafe answers | Treat docs as data, review agent checks grounding, citations required |
| Large PDFs can bloat storage | Disk/RAM pressure | size/page limits, cleanup, chunk reports, storage quotas |

## Phase 1 Discovery Results

- Current Riva container: `riva-speech`, image `nvcr.io/nvidia/riva/riva-speech:2.19.0`.
- Riva command includes `--asr_service=false --tts_service=true --nlp_service=false`.
- Riva TTS is reachable on `127.0.0.1:50051`.
- Initial Riva ASR call against the TTS-only container returned gRPC `UNIMPLEMENTED`; this was resolved by provisioning `facespeed-riva-asr` on `127.0.0.1:50151`.
- Docling parse API is reachable:
  - Base: `http://127.0.0.1:8005`
  - Health: `GET /health`
  - Parse: `POST /api/v1/parse`
  - OpenAPI title: `Parse-Data Service`
  - Description: PDF to Markdown by Docling with GPU acceleration.
- Embedding/rerank API is reachable:
  - Base: `http://127.0.0.1:8006`
  - Health: `GET /health`
  - Embedding: `POST /api/v1/embed`
  - Rerank: `POST /api/v1/rerank`
  - Embedding verification: 2 vectors, 2048 dimensions.
  - Rerank verification: relevant voice RAG document scored above unrelated document.
- Existing external chatbot backend is reachable on `http://127.0.0.1:9000`; it exposes existing RAG/session endpoints but is treated as a reference/runtime dependency candidate, not copied blindly into this project.

Phase 1 decision:

- Proceed with backend architecture for ASR using a separate ASR endpoint from the TTS endpoint.
- Proceed with real Docling, embedding, and rerank integration using configurable base URLs.

## Current Handoff

- Updated: 2026-05-23 00:30 +07.
- Current state:
  - Phase 1 is done.
  - Phase 2 is done.
  - Phases 4-11 are done with provider-backed Docling + embedding/rerank wiring.
  - Riva ASR is provisioned as a tuned offline runtime on `127.0.0.1:50151`.
  - Riva TTS remains on `127.0.0.1:50051`.
  - Current product shell is the Voice RAG assistant UI with PDF upload, ASR-ready status, editable transcript, cited answer, Riva TTS audio, and avatar timeline output.
- Resume from:
  - `docs/voice-rag-chatbot-handoff.md`
  - `logs/plans/voice-rag-chatbot.md`
- Next safe work item:
  - Finish final hygiene/close after any additional user-requested QA artifacts.
- Runtime note:
  - `scripts/provision-riva-asr-local.sh` rebuilds the ASR runtime locally, copies the offline ASR + punctuation models into a slim runtime repo, tunes batch sizes for this GPU, and starts `facespeed-riva-asr`.
- Ready services:
  - Docling parse API at `http://127.0.0.1:8005`.
  - embedding/rerank API at `http://127.0.0.1:8006`.
- Provider-backed evidence:
  - `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-rag-evidence.pdf`
  - `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-report.json`
  - `.cache/facespeed/evidence/release-readiness-2026-05-23/app/02-chat-answer-avatar.png`
  - `.cache/facespeed/evidence/release-readiness-2026-05-23/pipeline/docling-avatar-3d-moving.webm`

## Verification

- Backend:
  - `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests`
  - ASR fixture test.
  - Docling ingestion fixture tests for English and Vietnamese PDFs.
  - Chunk graph invariant tests.
  - Retrieval/rerank benchmark tests.
  - Agent loop retry/pass/not-found tests.
  - End-to-end `POST /api/voice/chat` test client case.
- Frontend:
  - `npm --prefix frontend test -- --run`
  - `npm --prefix frontend run build`
  - Playwright browser tests for desktop/mobile.
  - Microphone permission/error-state tests where browser automation allows.
- Runtime:
  - `./setup.sh --check`
  - `scripts/provision-riva-asr-local.sh`
  - new `./setup.sh --check-docling`
  - end-to-end browser evidence with screenshots/audio/retrieval reports.
- Security:
  - upload validation tests.
  - prompt injection fixture tests.
  - secret scan.
  - runtime artifact ignore check.

## Close criteria

- English voice chatbot works end to end:
  - mic/audio input -> transcript -> RAG answer -> answer voice -> 3D avatar speaking.
- User can upload/index PDFs through Docling and ask questions over indexed content.
- RAG returns cited answers with page/source evidence.
- Agent loop follows Lead/Search/Review/Teacher contracts and bounded retry behavior.
- If no evidence is found, the chatbot says so clearly instead of hallucinating.
- Frontend is a polished production voice RAG interface on desktop and mobile.
- Vietnamese is visible in the language selector and document metadata model.
- Tests and evidence prove backend, frontend, audio, retrieval, and avatar output.
- README/setup/docs are updated.
- Remaining provider gaps, especially full Docling/embedding wiring, are documented with exact commands and observed output.
