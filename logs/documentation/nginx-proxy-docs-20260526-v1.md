# Log: nginx-proxy-docs

- Started: 2026-05-26 09:05
- Finished: 2026-05-26 09:20
- Status: completed
- Related plan: plans/plan-nginx-proxy-docs-20260526-v1.md
- Related doc: docs/task/task-nginx-proxy-docs-20260526-v1.md

## Goal
Ghi lại việc cập nhật tài liệu và evidence sau khi thêm nginx proxy vào Docker Compose và setup workflow.

## Scope
- Cập nhật README/docs/tests/plans/logs để người dùng mở một port `6300`.
- Không ghi runtime log dài, secret hoặc output benchmark lớn.

## Phases
| Phase | Result |
| --- | --- |
| Rà tài liệu | Đã phát hiện docs còn thiếu nginx proxy và provider URL đúng. |
| Cập nhật file | Đã cập nhật README, docs, tests, plan/log và `.env.example`. |
| Verify | Đã chạy shell/compose/API/browser smoke; voice chat pass qua nginx. |

## Files
- `README.md`
- `docs/operations.md`
- `docs/task/task-nginx-proxy-docs-20260526-v1.md`
- `tests/nginx-proxy/test-nginx-proxy-20260526-v1.md`
- `plans/plan-nginx-proxy-docs-20260526-v1.md`
- `.env`
- `.env.example`
- `backend/src/config.py`
- `backend/src/services/rag_service.py`

## Verification
- `bash -n scripts/setup.sh`: pass.
- `docker compose config --quiet`: pass.
- `curl http://127.0.0.1:6300/api/rag/status`: pass, provider URL là `8005/8006`, `llmAvailable=true`.
- `POST http://127.0.0.1:6300/api/jobs`: pass với TTS ngắn.
- `POST http://127.0.0.1:6300/api/voice/chat`: pass, trả answer/citation/audioUrl/animationUrl.
- Playwright screenshot qua `6300`: pass, title `FaceSpeed Studio`, console errors rỗng sau khi sửa WebSocket upgrade.

## Risks
- A2F gRPC/HTTP vẫn là provider tùy chọn; nginx proxy chỉ xử lý frontend/backend dev app.
- Riva TTS local có thể timeout với đoạn đọc dài, nên spoken preview đang giới hạn bằng `VOICE_CHAT_TTS_MAX_CHARS=150`.
