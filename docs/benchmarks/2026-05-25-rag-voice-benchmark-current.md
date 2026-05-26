# RAG Voice Benchmark Current Report

- Updated: 2026-05-25 14:20 +07
- Status: blocked by Riva TTS/ASR dependency
- Related plan: `plans/running/plan-2026-05-25-rag-voice-benchmark-current.md`
- Related log: `logs/benchmarks/2026-05-25-rag-voice-benchmark-session.md`

## Current State

Đã tải corpus arXiv thật và ingest thật qua backend `6320`.

- Metadata corpus: 102 PDF thật trong `tests/benchmarks/corpus/arxiv/`; benchmark chọn top 100.
- Backend/API: 100 document / 11022 chunks.
- Ingest report: 100 OK / 100 trong `tests/benchmarks/corpus/arxiv/ingest-results.json`.
- Đã xóa 2 document ngoài tập top-100 (`2605_22687v1.pdf`, `2605_22686v1.pdf`) khỏi backend/DB/vector store để benchmark không bị nhiễu.

`2605.22730v1` được reconcile vì client timeout nhưng backend đã persist. `2605.22743v1` và `2605.22742v1` retry thành công sau khi tăng Docling timeout, thêm retry theo ID, và giữ port-forward `6105/6106/6107` sống bằng session riêng.

## Resource Guard

Ngưỡng guard đang dùng:

- VRAM free tối thiểu: 25% của 48935 MiB, tương đương khoảng 12234 MiB.
- RAM available tối thiểu: 15%.

Tại retry `2605.22743v1`, VRAM free tụt xuống 11950 MiB, dưới ngưỡng 12234 MiB; monitor dừng retry ngay. Sau khi chờ, VRAM hồi về baseline khoảng 12578 MiB. Không kill các GPU process ngoài dự án.

## Benchmark Status

Đã thử mốc nhẹ nhất:

- Command: `python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:6107/v1 --file-count 100 --count 10 --concurrency 1 --record-best --keep-failures --artifact-samples 2 ...`
- Kết quả: dừng thủ công sau case đầu vì `0001/10 fail`, score `0.000`, latency `407.70s`.
- Job logs chỉ ra Riva TTS `127.0.0.1:6051` connection refused.
- ASR/TTS ports `6051/6052` không có service thật đang listen.

Chưa chạy `10x10`, `30x1`, `30x10` vì voice dependency offline khiến mọi batch voice chắc chắn fail. Chưa có screenshot/audio evidence mới từ frontend cho batch này. Artifact cũ trong `tests/benchmarks/runs/` không được xem là pass cho batch hiện tại.

## Next Safe Step

1. Start Riva TTS thật ở `127.0.0.1:6051` và ASR thật ở `127.0.0.1:6052`, trong dải port project.
2. Xác nhận `/api/voice/transcribe` và `/api/voice/chat` trả audio thật, không mock.
3. Chạy lại benchmark theo thứ tự nhẹ: `10x1`, `10x10`, `30x1`, `30x10`.
4. Chỉ capture screenshot/audio sau khi benchmark API pass.
