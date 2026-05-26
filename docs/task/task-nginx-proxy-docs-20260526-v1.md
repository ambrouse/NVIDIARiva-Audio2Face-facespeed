# Task: nginx-proxy-docs

- Created: 2026-05-26 09:05
- Updated: 2026-05-26 09:20
- Status: completed
- Related plan: plans/plan-nginx-proxy-docs-20260526-v1.md
- Related log: logs/documentation/nginx-proxy-docs-20260526-v1.md
- Related test: tests/nginx-proxy/test-nginx-proxy-20260526-v1.md

## Goal
Cập nhật tài liệu và evidence sau khi thêm nginx vào Docker Compose để browser chỉ cần mở `http://127.0.0.1:6300/`.

## Scope
- Root README ghi URL chính, test evidence và task doc.
- `docs/operations.md` ghi port proxy, tmux runtime và cách forward.
- `tests/nginx-proxy/` ghi smoke test proxy qua frontend, backend API và ảnh Playwright.
- `plans/` và `logs/documentation/` ghi lại phase và verify.

## Result
- Nginx container `facespeed-nginx` chạy trong Docker Compose.
- `./setup.sh` / `./setup.sh --run` start nginx cùng Docker services.
- Nginx proxy `/api/*` tới backend `127.0.0.1:6320`.
- Nginx proxy app path còn lại tới frontend `127.0.0.1:6310`.
- Vite HMR qua nginx đã được chỉnh thêm WebSocket upgrade header, không còn console error trong smoke screenshot.
- Provider backend dùng service sẵn trên máy: Docling `8005`, embedding/rerank `8006`, vLLM `8007`.
- Voice chat qua nginx đã pass sau khi backend dùng đúng provider `8005/8006/8007` và spoken preview giới hạn `VOICE_CHAT_TTS_MAX_CHARS=150`.

## Verification
| Check | Result |
| --- | --- |
| `bash -n scripts/setup.sh` | Pass |
| `docker compose config --quiet` | Pass |
| `curl -fsS --max-time 10 http://127.0.0.1:6300/` | Pass, trả HTML frontend |
| `curl -fsS --max-time 20 http://127.0.0.1:6300/api/rag/status` | Pass, trả JSON status |
| `POST http://127.0.0.1:6300/api/voice/chat` | Pass, trả answer/citation/audioUrl/animationUrl |
| `POST http://127.0.0.1:6300/api/jobs` với câu TTS ngắn | Pass, Riva TTS tạo audio/animation |
| Playwright screenshot `tests/nginx-proxy/evidence-2026-05-26/nginx-proxy-home.png` | Pass, app shell hiện qua proxy và không có console error |

## Notes
- Test này không thay thế benchmark RAG Voice đầy đủ trong `tests/benchmarks/`.
- A2F-3D vẫn là provider tùy chọn; nginx proxy không thay đổi pipeline Riva + browser ARKit hiện tại.
