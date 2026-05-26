# Log: real-db-llm-graph-rag

- Started: 2026-05-23 19:23
- Status: closed
- Plan: plans/plan-real-db-llm-graph-rag.md
- Doc: docs/plan/real-db-llm-graph-rag.md

## Ghi Nhận Ban Đầu
- `vllm_gemma4` đang expose OpenAI-compatible API ở `127.0.0.1:8007`, model `google/gemma-4-E4B-it`.
- Port `6000` đang bị `face-recognition` dùng; chọn Postgres `6001`, Qdrant HTTP `6002`, Qdrant gRPC `6003`.
- Riva TTS/ASR, Docling và embedding provider đang chạy sẵn.

## Phase Log
- 2026-05-23 19:23: Tạo plan/log/doc và bắt đầu triển khai.
- 2026-05-23 19:34: Thêm `docker-compose.yml` cho Postgres `6001` và Qdrant `6002/6003`, bind data vào `.cache/facespeed`.
- 2026-05-23 19:47: Thêm Postgres store, Qdrant store, OpenAI-compatible LLM client, prompt/session/task/history/context/event tables.
- 2026-05-23 19:52: Backend tests pass `31 passed`; frontend tests pass `4 passed`; frontend build pass.
- 2026-05-23 19:58: Sửa Qdrant collection mismatch 4 -> 2048 dims và thêm lock tránh race khi app boot nhiều request song song.
- 2026-05-23 20:02: API smoke pass: `/api/rag/status` báo Postgres/Qdrant/LLM true, Qdrant `facespeed_chunks` có 10 points.
- 2026-05-23 20:04: Chat thật pass với session `evidence-session-001`, 5 agent events: user -> lead -> search -> qdrant -> teacher/llm -> review/lead.
- 2026-05-23 20:05: Playwright screenshots lưu tại `.cache/facespeed/evidence/real-db-llm-graph-rag-evidence-2026-05-23/app/`, canvas pixel check `1032x440`, colored pixels > 65k.
- 2026-05-23 22:28: Đóng plan cũ theo yêu cầu tiếp tục benchmark; chuyển khỏi `plans/running/` sang `plans/`.
