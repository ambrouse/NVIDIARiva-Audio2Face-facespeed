# RAG Voice Benchmark Blocker Evidence

- Created: 2026-05-25 16:12 +07
- Accepted: `false`
- Status: `blocked`
- Related plan: `plans/running/plan-rag-voice-retest-100pdf.md`

## Summary

Đã bắt đầu test thật nhưng chưa được phép chạy benchmark `10/30 câu x 1/10 user` vì provider chính chưa online. Backend/frontend đã chạy trên port riêng `6320/6310`, corpus hiện có `100` document indexed và `11022` chunks. Luồng RAG/voice fail trước khi tạo answer/audio do embedding API và Riva ASR offline.

## Evidence

| File | Nội dung |
| --- | --- |
| `01-frontend-loaded.png` | Frontend chạy trên `6310`, thấy `100` source và avatar. |
| `02-runtime-modal.png` | Runtime modal từ frontend. |
| `03-voice-chat-provider-error.png` | Câu hỏi thật trên UI và lỗi `Request failed with status 503`. |
| `audio-input-smoke-synthetic.wav` | Audio input smoke để chứng minh đường upload ASR; file này là synthetic, không được tính là pass voice input thật. |
| `audio-output-unavailable.txt` | Ghi rõ chưa có audio output vì `/api/voice/chat` fail trước TTS. |
| `rag-search-response.json` | `/api/rag/search` fail do embedding API `6106` connection refused. |
| `voice-chat-response.json` | `/api/voice/chat` fail do embedding API `6106` connection refused. |
| `asr-response.json` | `/api/voice/transcribe` fail do Riva ASR `6052` connection refused. |
| `rag-status.json` | Backend status: `100` documents, `11022` chunks, Qdrant/Postgres OK, LLM unavailable. |
| `services.json` | Riva stopped; Audio2Face service not registered under expected container name. |
| `resource-snapshot.json` | RAM/VRAM/disk snapshot lúc test. |
| `browser-report.json` | Browser console/network report. |

## Resource Snapshot

- RAM available trước test: khoảng `90-91Gi/125Gi`.
- VRAM free: khoảng `12578MiB/48935MiB`, sát ngưỡng guard `25%`.
- GPU đang có process ngoài project dùng VRAM; không kill hoặc chỉnh các process này.
- Disk `/home`: khoảng `89G` free.

## Blockers

- Embedding/rerank API `http://127.0.0.1:6106` chưa listen, làm RAG search và voice chat trả `503`.
- Riva ASR `127.0.0.1:6052` chưa listen, làm audio input/transcribe trả `503`.
- Riva TTS `127.0.0.1:6051` chưa listen theo setup check trước đó.
- LLM judge/teacher `http://127.0.0.1:6107/v1` unavailable trong `/api/rag/status`.
- Audio2Face expected container `facespeed-audio2face-3d` chưa registered; container cũ `facespeed-audio2face` đang exited.

## Result

Không chạy full benchmark vì sẽ fail hàng loạt và có rủi ro VRAM. Batch này được ghi là blocker evidence, không phải pass report.
