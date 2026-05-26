# RAG Chatbot Benchmark

> Latest current report: `docs/benchmarks/2026-05-25-rag-voice-benchmark-current.md`

- Updated: 2026-05-25 09:38
- Status: in_progress
- Plan: ../../plans/running/plan-benchmark-rag-chatbot.md

## Mục Tiêu
Benchmark lại agent RAG voice bằng luồng thật: 100 PDF upload/index thật, 10 câu và 30 câu hỏi thực tế, mỗi bộ chạy với 1 user và 10 user đồng thời. Báo cáo phải gồm tốc độ, độ chính xác, grounding, đúng source, audio input/output, screenshot frontend và resource guard.

## Port Riêng
Runtime project dùng dải `6000-6500`:

| Service | Port |
| --- | --- |
| Postgres | `6001` |
| Qdrant HTTP/gRPC | `6002/6003` |
| Audio2Face-3D gRPC/HTTP | `6040/6041` |
| Riva TTS/ASR | `6051/6052` |
| Docling | `8005` |
| Embedding/rerank | `8006` |
| LLM judge/teacher | `8007` |
| Frontend | `6310` |
| Backend | `6320` |

Port `6000` đang có service khác nên không dùng cho project này.
Riva TTS chạy với `RIVA_TTS_MAX_CONCURRENCY=1` để queue synthesize thật thay vì bắn song song làm Riva postprocessor crash.
`RIVA_SAMPLE_RATE_HZ=44100` khớp model rate của Riva TTS để tránh resample trong postprocessor khi benchmark.

## Gate Chất Lượng
- Không hardcode câu trả lời và không fallback để né fail.
- Correctness, grounding, no-hallucination, đúng document/page/chunk đều phải >95%.
- Câu xã giao/không liên quan phải phản hồi tự nhiên nhưng không bịa nguồn.
- Không tìm đúng file/page/chunk là fail.
- Sau mỗi đổi prompt/tool/pipeline phải chạy lại từ đầu batch bị ảnh hưởng.
- Batch chỉ accepted khi complete đủ case; checkpoint thiếu case không được tính pass.

## Resource Guard
Runner và ingester dừng khi một trong các ngưỡng bị vi phạm:

- RAM free < `10%`.
- VRAM free < `10%`.
- Disk free < `10%`.

Mỗi report benchmark lưu `resourceSamples` trong `summary.json` và tóm tắt RAM/VRAM/disk trong `REPORT.md`.

## Commands

```bash
python tests/benchmarks/arxiv_corpus.py download --limit 100
python tests/benchmarks/arxiv_corpus.py ingest --api-base http://127.0.0.1:6320 --limit 100
python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:8007/v1 --file-count 100 --count 10 --concurrency 1 --record-best
python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:8007/v1 --file-count 100 --count 10 --concurrency 10 --record-best
python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:8007/v1 --file-count 100 --count 30 --concurrency 1 --record-best
python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:8007/v1 --file-count 100 --count 30 --concurrency 10 --record-best
node scripts/capture-benchmark-evidence.mjs
```

## Evidence
Evidence mới lưu ở:

```text
tests/benchmarks/evidence/rag-voice-YYYY-MM-DD/
```

Nội dung tối thiểu:

- `frontend-answer.png`: thấy câu hỏi, câu trả lời, citation/source trên UI.
- `audio-input.wav`: file audio input dùng để test voice path.
- `audio-output.wav`: audio answer backend trả về.
- `browser-report.json`: console/network status và đường dẫn artifact.

## Hiện Trạng
- Backend cũ `8020` đang offline.
- Project ports `6310/6320/6040/6041/6051/6052` thuộc runtime này; provider services dùng sẵn `8005/8006/8007` trên máy benchmark.
- Corpus hiện có 102 PDF thật trong `tests/benchmarks/corpus/arxiv/`; benchmark chọn top 100.
- Top-100 corpus đã ingest OK `100/100`; backend status `100 documents / 11022 chunks`.
- Pipeline upload đã đổi sang embedding batch nhỏ: `RAG_EMBEDDING_BATCH_SIZE=2`, `RAG_EMBEDDING_BATCH_DELAY_SECONDS=1.0`; Docling timeout tăng `180s`; backend không reindex toàn bộ corpus lúc load (`RAG_REINDEX_ON_LOAD=false`).
- Benchmark `10 câu x 1 user` đã thử và dừng sau case đầu: fail, score `0.000`, latency `407.70s`, nguyên nhân Riva TTS `127.0.0.1:6051` connection refused.
- Chưa chạy các batch còn lại và chưa capture frontend/audio evidence vì real Riva TTS/ASR `6051/6052` offline; không dùng mock để báo pass.
- Run cũ `file-10/_latest-300` dừng ở `293/300`, `accepted=false`, không đủ điều kiện pass.
