# Plan: nginx-proxy-docs

- Created: 2026-05-26 09:05
- Updated: 2026-05-26 09:20
- Status: closed
- Related log: logs/documentation/nginx-proxy-docs-20260526-v1.md
- Related doc: docs/task/task-nginx-proxy-docs-20260526-v1.md

## Goal
Cập nhật README, docs, logs, tests và plans để phản ánh thay đổi nginx proxy trong Docker Compose và workflow chạy qua `./setup.sh`.

## Scope
- In: Root README, docs vận hành/cài đặt, log task, test evidence dạng markdown, plan đóng/mở.
- Out: Không đổi logic backend/frontend ngoài phần đã thêm nginx; không chạy lại benchmark RAG Voice đầy đủ.

## Skills
- plan-skill
- documentation-skill
- logging-skill
- testing-skill
- readme-style

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Rà tài liệu hiện có và xác định chỗ thiếu sau khi thêm nginx. | done | `README.md`, `docs/operations.md`, `tests/README.md`, `plans/README.md`. |
| 2 | Cập nhật README/docs/logs/tests/plans theo format skill. | done | `docs/task/task-nginx-proxy-docs-20260526-v1.md`, `logs/documentation/nginx-proxy-docs-20260526-v1.md`, `tests/nginx-proxy/`. |
| 3 | Verify cú pháp shell, Docker Compose và nginx proxy endpoint. | done | `bash -n`, `docker compose config --quiet`, `curl` proxy, Playwright screenshot, voice chat smoke. |

## Verification
- `bash -n scripts/setup.sh`
- `docker compose config --quiet`
- `curl -fsS --max-time 10 http://127.0.0.1:6300/`
- `curl -fsS --max-time 20 http://127.0.0.1:6300/api/rag/status`
- `POST http://127.0.0.1:6300/api/voice/chat`

## Close Criteria
- README/docs ghi đúng URL chính `http://127.0.0.1:6300/`.
- Logs và docs task có liên kết ngược tới plan.
- Tests có báo cáo proxy rõ command, kết quả và rủi ro còn lại.
- Plan được chuyển khỏi `plans/running/` khi hoàn tất.

## Close Notes
- Provider runtime dùng service sẵn trên máy: Docling `8005`, embedding/rerank `8006`, vLLM `8007`.
- Nginx proxy `6300` hoạt động cho frontend, API, HMR WebSocket và voice chat.
- Spoken preview giới hạn `VOICE_CHAT_TTS_MAX_CHARS=150` để tránh Riva/Triton timeout với câu trả lời dài.
