# Plan: pdf-crud-agent-canvas

- Created: 2026-05-23 19:00
- Updated: 2026-05-23 19:11
- Status: closed
- Related log: logs/plans/pdf-crud-agent-canvas.md
- Related doc: docs/plan/pdf-crud-agent-canvas.md

## Goal
Xoa PDF vua upload, them CRUD cho PDF context dong bo giua runtime memory va local JSON storage, trinh bay lai pipeline RAG hien tai, va thay modal trace bang so do canvas co animation de user nhin duong di agent/database.

## Scope
- In: API list/detail/update/delete PDF context, xoa embeddings/turns lien quan khi delete, UI sources co rename/delete/refresh, trace canvas animated, test API va UI that bang browser.
- Out: Thay provider RAG/embedding/docling, them database server moi, cai thien chat luong semantic retrieval vuot ngoai CRUD/visualization.

## Skills
- plan-skill: lap phase va cap nhat trang thai.
- backend-skill: API/service/storage contract.
- frontend-skill: UI CRUD va canvas animation.
- testing-skill: regression test va evidence bang frontend that.
- documentation-skill: doc pipeline va ket qua.
- logging-skill: log phase/verify.

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Khao sat storage/UI va ghi pipeline hien tai | done | docs/plan/pdf-crud-agent-canvas.md |
| 2 | Backend CRUD PDF dong bo memory + JSON storage | done | pytest tests/backend/test_rag_api.py |
| 3 | Frontend sources CRUD va trace canvas animated | done | npm test/build + screenshot |
| 4 | Xoa PDF vua upload `0987c3de69f08a20` bang API moi | done | GET /api/documents khong con record |
| 5 | Verify app that tren desktop/mobile | done | .cache/facespeed/evidence/pdf-crud-agent-canvas-evidence-2026-05-23/ |

## Verification
- `backend/.venv-linux/bin/python -m pytest tests/backend/test_rag_api.py`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- API smoke: delete PDF vua upload, list/status/search sau delete.
- Browser screenshots desktop/mobile cho Sources CRUD va Trace canvas animated.

## Close Criteria
- PDF vua upload da bi xoa khoi UI, memory, `storage/rag/documents`, `storage/rag/embeddings`, va turn lien quan.
- Backend CRUD co test regression.
- Frontend co controls CRUD va trace canvas animation render ro rang.
- Doc/log/evidence cap nhat, plan chuyen sang completed roi closed.

## Result
- Closed. Plan da duoc chuyen khoi `plans/running`, log/doc/evidence da cap nhat.
