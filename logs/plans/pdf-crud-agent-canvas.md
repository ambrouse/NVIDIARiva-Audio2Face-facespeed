# Log: pdf-crud-agent-canvas

- Started: 2026-05-23 19:00
- Status: completed
- Plan: plans/running/plan-pdf-crud-agent-canvas.md
- Doc: docs/plan/pdf-crud-agent-canvas.md

## Muc Tieu
Xoa PDF vua upload, them CRUD PDF context dong bo storage, va thay trace dang list bang canvas animated de mo ta duong di agent/database.

## Ghi Nhan Ban Dau
- Backend dang chay tren `127.0.0.1:8020`, frontend tren `127.0.0.1:6310`.
- PDF vua upload co id `0987c3de69f08a20`, file `docling-rag-evidence.pdf`.
- Storage hien tai la JSON local trong `storage/rag/documents`, `storage/rag/embeddings`, `storage/rag/turns`; runtime backend giu ban copy trong memory.
- RAG hien tai: Docling parse PDF -> chunk -> embedding provider -> cosine threshold -> expand neighbor chunks -> rerank provider -> review confidence -> tao answer -> Riva TTS -> browser avatar timeline.

## Phase Log
- 2026-05-23 19:00: Tao plan/log/doc va bat dau khao sat.
- 2026-05-23 19:04: Them backend CRUD cho PDF context va regression test.
- 2026-05-23 19:07: Them UI Sources CRUD va Trace canvas animated.
- 2026-05-23 19:08: Restart backend/frontend, xoa PDF `0987c3de69f08a20`; API tra `deleted=true`, removed 1 chunk va 2 turns.
- 2026-05-23 19:10: Verify backend, frontend build/test, Playwright desktop/mobile screenshots.

## Files Chinh
- `backend/src/models/rag.py`
- `backend/src/services/rag_service.py`
- `backend/src/routes/rag.py`
- `backend/src/main.py`
- `tests/backend/test_rag_api.py`
- `frontend/src/services/api.ts`
- `frontend/src/pages/PipelinePage.tsx`
- `frontend/src/components/AgentTraceCanvas.tsx`
- `frontend/src/styles/app.css`

## Verify
- Backend: `7 passed`.
- Frontend unit: `4 passed`.
- Frontend build: pass.
- API status sau xoa: `documentCount=1`, `chunkCount=10`.
- Browser: desktop/mobile screenshots pass, no console/page errors.

## Risk Con Lai
- Chat answer van la extractive template, chua phai LLM reasoning nen chat luong RAG co the van kem voi PDF scan/OCR xau.
- Page mapping chunk hien van uoc luong tu section/chunk index.
