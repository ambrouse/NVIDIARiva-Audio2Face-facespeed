# Test: nginx-proxy

- Created: 2026-05-26 09:14
- Status: pass
- Related plan: ../../plans/plan-nginx-proxy-docs-20260526-v1.md
- Related doc: ../../docs/task/task-nginx-proxy-docs-20260526-v1.md
- Evidence: evidence-2026-05-26/nginx-proxy-home.png

## Goal
Kiểm tra nginx proxy `6300` sau khi thêm service vào Docker Compose và đưa vào `./setup.sh`.

## Environment
| Item | Value |
| --- | --- |
| App URL | `http://127.0.0.1:6300/` |
| Frontend upstream | `http://127.0.0.1:6310` |
| Backend upstream | `http://127.0.0.1:6320` |
| Docling provider | `http://127.0.0.1:8005` |
| Embedding/rerank provider | `http://127.0.0.1:8006` |
| vLLM provider | `http://127.0.0.1:8007/v1` |
| Nginx container | `facespeed-nginx` |

## Commands And Results
| Command | Result |
| --- | --- |
| `bash -n scripts/setup.sh` | Pass |
| `docker compose config --quiet` | Pass |
| `curl -fsS --max-time 10 http://127.0.0.1:6300/` | Pass, trả HTML frontend |
| `curl -fsS --max-time 20 http://127.0.0.1:6300/api/rag/status` | Pass, `documentCount=100`, `chunkCount=11022`, Postgres/Qdrant available |
| Playwright open `http://127.0.0.1:6300/` and screenshot | Pass, title `FaceSpeed Studio`, console errors `[]` |
| `POST /api/jobs` short TTS smoke | Pass, Riva TTS created audio/animation through nginx |
| `POST /api/voice/chat` RAG voice smoke | Pass, answer cites `2605_22719v1.pdf p.3`, returns `audioUrl` and `animationUrl` |

## Screenshot Review
Ảnh `evidence-2026-05-26/nginx-proxy-home.png` đã được đọc lại: UI chính hiển thị qua proxy, sidebar và Voice RAG panel render, badge tài liệu là `100`, ASR đang `on`, avatar ở trạng thái `idle`. Ảnh không chứng minh benchmark RAG trả lời câu hỏi; phần đó nằm trong `tests/benchmarks/`.

## Notes
- Lần chụp đầu phát hiện Vite HMR WebSocket lỗi qua nginx. Đã sửa nginx template bằng header `Upgrade` và `Connection`, sau đó chụp lại không còn console error.
- Playwright trên host cần `LD_LIBRARY_PATH=$PWD/.local-libs/playwright` do Chromium thiếu `libasound.so.2` nếu không dùng local libs.
- Voice chat cần provider trực tiếp `8005/8006/8007`; bridge benchmark `6105/6106/6107` không phải runtime chính.
- Spoken preview dùng `VOICE_CHAT_TTS_MAX_CHARS=150` để tránh Riva/Triton timeout với câu trả lời dài.

## Voice Chat Smoke
Payload:

```json
{
  "message": "What does the indexed PDF say about benchmark evaluation?",
  "language": "en-US",
  "voice": "English-US.Female-1",
  "outputMode": "preview",
  "sessionId": "debug-nginx-voice-20260526-final"
}
```

Result:

| Field | Value |
| --- | --- |
| HTTP status | `200 OK` |
| Top citation | `2605_22719v1.pdf`, page `3` |
| Review status | `pass` |
| Audio | `/api/artifacts/audio/c9dc775a-a51e-4857-8f00-8d1c927be7b3.wav` |
| Animation | `/api/artifacts/animation/c9dc775a-a51e-4857-8f00-8d1c927be7b3.json` |
