# Plan: real-db-llm-graph-rag

- Created: 2026-05-23 19:23
- Updated: 2026-05-23 22:28
- Status: closed
- Related log: logs/plans/real-db-llm-graph-rag.md
- Related doc: docs/plan/real-db-llm-graph-rag.md

## Goal
Chuyển dự án từ RAG local JSON đơn giản sang lát cắt production hơn: Postgres/Qdrant container quản lý bằng Docker Compose, LLM thật local qua vLLM, graph/wiki RAG có liên kết chunk, session/agent ledger, prompt manager trên frontend, và dashboard agent canvas cập nhật đúng theo phiên chat thật.

## Scope
- In: `docker-compose.yml` cho Postgres/Qdrant ports 6001-6003, bind data vào `.cache/facespeed`, backend store/migration, Qdrant vector sync, OpenAI-compatible vLLM client, prompt CRUD, agent session/task/history/context tables, graph-neighbor expansion, streaming/polling status cho frontend, UI prompt manager và dashboard canvas/status.
- Out: fine-tune model, auth/multi-user permission đầy đủ, thay embedding provider hiện có, triển khai cloud, graph database chuyên dụng như Neo4j.

## Skills
- plan-skill: quản lý phase và close criteria.
- backend-skill: API/service/database boundaries.
- frontend-skill: prompt manager, status dashboard, canvas realtime.
- testing-skill: backend/frontend/e2e evidence bằng ảnh.
- security-skill: DB secret/config, không lộ `.env`, không hardcode cloud key.
- documentation-skill: ghi kiến trúc và vận hành.
- logging-skill: ghi log phase/verify.

## Risks
- Port 6000 đang bị face-recognition dùng; dùng 6001-6003 để tránh xung đột.
- Host GPU đang tải cao; dùng vLLM đang chạy sẵn ở 8007, không start thêm GPU model.
- Đây là refactor lớn; lát cắt trong phase này phải chạy được thật, còn tối ưu sâu agent reasoning sẽ tiếp tục sau.

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Tạo plan/log/doc và xác nhận runtime/ports | done | vLLM `/v1/models`, ports 6001-6003 |
| 2 | Infra DB container Postgres/Qdrant | done | `docker compose ps` healthy/green |
| 3 | Backend store, LLM, prompt/session schemas | done | `backend/.venv-linux/bin/python -m pytest tests` |
| 4 | Graph RAG upload/search/chat với agent events | done | `/api/voice/chat`, `/api/agent-sessions/evidence-session-001` |
| 5 | Frontend prompt manager + dashboard realtime | done | `npm test -- --run`, `npm run build`, screenshots |
| 6 | Evidence, docs, close plan | done | `.cache/facespeed/evidence/real-db-llm-graph-rag-evidence-2026-05-23/app/` |

## Verification
- `docker compose up -d facespeed-postgres facespeed-qdrant`
- `curl http://127.0.0.1:6002/collections/facespeed_chunks`
- `backend/.venv-linux/bin/python -m pytest tests`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- API smoke upload/search/chat/session-status/prompt CRUD.
- Playwright desktop/mobile screenshots showing prompt manager, dashboard status, and canvas paths.

## Close Criteria
- DB services chạy bằng compose ở ports 6001-6003, data nằm dưới `.cache/facespeed`.
- Upload ghi Postgres + Qdrant và vẫn có fallback JSON nếu DB chưa sẵn sàng.
- Chat dùng LLM thật local, có session/agent task/history/context, agent status hiển thị theo phiên.
- Frontend có prompt manager và dashboard agent canvas cập nhật đúng event, không lag/không overlap.
- Evidence ảnh và docs/log đầy đủ.

## Result
- Postgres chạy ở `127.0.0.1:6001`, Qdrant HTTP/gRPC ở `127.0.0.1:6002/6003`, data bind-mounted dưới `.cache/facespeed`.
- vLLM thật `google/gemma-4-E4B-it` ở `127.0.0.1:8007/v1` đã được dùng cho metadata/teacher/review.
- Qdrant collection `facespeed_chunks` đã sync 10 vectors, size 2048, từ PDF hiện có.
- Frontend có prompt manager, runtime cards, chat status và trace canvas event thật.
