# Real DB, LLM và Graph RAG

- Created: 2026-05-23 19:23
- Status: completed
- Plan: ../../plans/plan-real-db-llm-graph-rag.md

## Kiến Trúc Mục Tiêu Trong Phase Này
- Postgres lưu document metadata, chunks, chunk links, prompts, sessions, agent tasks/history/context.
- Qdrant lưu vectors của chunk để query rộng và mở rộng theo graph links.
- vLLM local ở `127.0.0.1:8007` xử lý metadata cleanup, teacher answer và review.
- Backend vẫn giữ fallback local JSON để không mất khả năng chạy khi DB chưa bật.
- Frontend có prompt manager và dashboard phiên agent đang chạy.

## Pipeline Upload
1. PDF -> Docling markdown.
2. LLM metadata cleaner tạo title/summary/keywords sạch hơn.
3. Backend chunking và tạo wiki links: prev/next, same section, keyword/title overlap.
4. Embedding provider tạo vectors.
5. Postgres lưu document/chunk/link; Qdrant lưu vector payload.

## Pipeline Response
1. Leader tạo session task và yêu cầu search.
2. Search agent phân tích query, chọn filter, embedding, Qdrant search, mở rộng chunk graph, rerank, tự đánh giá search lại nếu cần.
3. Teacher agent đọc context đã chọn và prompt để trả lời.
4. Review agent dùng LLM kiểm hallucination/thiếu/trôi; nếu fail thì báo leader để retry search hoặc trả gap.
5. Riva TTS và browser avatar tạo output.
6. Mỗi agent ghi task/history/context riêng và session ledger chung trong Postgres.

## Lưu Ý
- Phase này chưa thay thế hoàn toàn bằng graph database chuyên dụng. Postgres + Qdrant là lựa chọn tốt nhất hiện tại vì nhẹ, dễ quản lý bằng compose, hỗ trợ metadata/query/vector, và phù hợp máy local.

## Kết Quả Đã Verify
- Postgres: `127.0.0.1:6001`, lưu document/chunk/link/prompt/session/task/history/context/event.
- Qdrant: `127.0.0.1:6002`, collection `facespeed_chunks`, vector size `2048`, `10` points từ PDF hiện có.
- LLM thật: OpenAI-compatible vLLM `http://127.0.0.1:8007/v1`, model `google/gemma-4-E4B-it`.
- Runtime API: `/api/rag/status` trả `postgresAvailable=true`, `qdrantAvailable=true`, `llmAvailable=true`, `graphRagEnabled=true`.
- Evidence UI: `.cache/facespeed/evidence/real-db-llm-graph-rag-evidence-2026-05-23/app/`.
