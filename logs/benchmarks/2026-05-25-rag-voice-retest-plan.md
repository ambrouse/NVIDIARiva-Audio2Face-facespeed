# Session Log: RAG Voice Retest Plan

- Created: 2026-05-25 16:03 +07
- Status: blocked
- Related plan: `plans/running/plan-rag-voice-retest-100pdf.md`
- Related doc: `docs/benchmarks/2026-05-25-rag-voice-retest-plan.md`

## Notes

- Đã đọc lại plan hiện tại, benchmark docs, backend RAG service, routes, config, frontend pipeline page, benchmark runner, corpus ingester, resource guard và evidence capture script.
- Port/env/README đã ghi runtime project trong `6000-6500`.
- Corpus hiện có hơn 100 PDF trong `tests/benchmarks/corpus/arxiv/`; report trước ghi top-100 indexed `100/100`.
- Blocker gần nhất là real voice dependency: Riva TTS `127.0.0.1:6051` connection refused trong case đầu của batch `10x1`.
- Plan mới yêu cầu bổ sung mixed-case benchmark và audio input có lời nói thật trước khi claim pass.

## Snapshot 2026-05-25 16:03 +07

- Listening trong dải project: `6001`, `6002`, `6003`.
- Chưa thấy listen: backend `6320`, frontend `6310`, Riva TTS/ASR `6051/6052`, A2F `6040/6041`, Docling/embedding/LLM bridge `6105/6106/6107`.
- RAM: `91Gi` available trên `125Gi`.
- VRAM: `12578MiB` free trên `48935MiB`, GPU util `31%`.
- Disk `/home`: `89G` free, dùng `77%`.

## Run 2026-05-25 16:07 +07

- Bắt đầu thực thi plan test theo yêu cầu.
- Quy tắc chạy: kiểm resource trước mỗi bước nặng, không dùng mock để báo pass, không kill hoặc chỉnh process ngoài project, không ghi secret vào evidence/report.
- Snapshot phase 1: project containers đang chạy chỉ có `facespeed-postgres` trên `6001` và `facespeed-qdrant` trên `6002/6003`.
- Backend `6320`, frontend `6310`, Riva TTS/ASR `6051/6052`, A2F `6040/6041`, Docling/embedding/LLM bridge `6105/6106/6107` chưa listen.
- Resource baseline: RAM available `91Gi/125Gi`, disk free `89G`, VRAM free `12578MiB/48935MiB` với GPU util `42%`.
- Kết luận phase 1: chưa được chạy benchmark voice/RAG vì provider và backend/frontend chưa online; chuyển sang kiểm tra nền nhẹ và start service project nếu an toàn.
- Theo yêu cầu mới, đã dọn `tests/` để chỉ giữ `tests/benchmarks/`.
- Đã xoá test cũ ngoài benchmark: `tests/backend/`, `tests/frontend/`, `tests/README.md`, `tests/test_setup_script.py`.
- Đã xoá cache và run output cũ trong benchmark: `tests/benchmarks/__pycache__`, `tests/benchmarks/runs`, `tests/benchmarks/evidence`; giữ lại benchmark scripts và corpus PDF thật.
- `python -m py_compile tests/benchmarks/arxiv_corpus.py tests/benchmarks/rag_chatbot_benchmark.py tests/benchmarks/resource_guard.py`: pass.
- `bash setup.sh --run`: backend `6320` và frontend `6310` start thành công; setup cảnh báo Riva TTS và Audio2Face không reachable.
- `/api/rag/status`: `100` documents, `11022` chunks, Postgres/Qdrant OK, `llmAvailable=false`.
- `/api/rag/search`: fail `503`, detail embedding request failed, connection refused.
- `/api/voice/chat`: fail `503`, detail embedding request failed, connection refused.
- `/api/voice/transcribe`: fail `503`, detail Riva ASR `6052` connection refused.
- Đã capture frontend screenshots và artifact blocker tại `tests/benchmarks/evidence/rag-voice-2026-05-25-blocked/`.
- Không chạy benchmark `10/30 x 1/10 user` vì provider offline sẽ fail hàng loạt và VRAM đang sát guard `25%`.

## Update 2026-05-25 16:22 +07

- User yêu cầu tiếp tục chạy và chỉ bắt đầu stop/kill project khi RAM/VRAM vượt `90%` used.
- Guard mới cho bước tiếp theo: RAM used >= `90%` hoặc VRAM used >= `90%` thì stop/kill các process/container thuộc project này; không kill process ngoài project nếu chưa có lệnh rõ theo PID/tên.
- GPU hiện đang bị chiếm bởi process ngoài project: `VLLM::EngineCore`, `face-reconizer/face-recognition`, `RAG_Chatbot/RAG_Chat/parse-data` và một process `./venv/bin/python main.py`.

## Completed 2026-05-25 17:30 +07

- Đã chạy lại luồng thật với 100 PDF indexed (`100` documents, `11022` chunks), backend `6320`, frontend `6310`, Riva TTS `6051`, Riva ASR `6052`, provider bridge `6105/6106/6107`.
- Pipeline fixes chính: chọn answer citation theo phrase/keyword/context quality; bỏ TTS fallback; thêm queue Riva TTS `RIVA_TTS_MAX_CONCURRENCY=1`; đổi `RIVA_SAMPLE_RATE_HZ=44100`; rút spoken voice text còn 220 ký tự; siết benchmark gate `answer_source_cited` và `answer_source_expected_document`.
- Benchmark cuối:
  - `10 câu / 1 user`: `10/10`, pass rate `100%`, p50/p95/max `6.31s/13.90s/13.90s`.
  - `10 câu / 10 user`: `10/10`, pass rate `100%`, p50/p95/max `56.76s/58.21s/58.21s`.
  - `30 câu / 1 user`: `30/30`, pass rate `100%`, p50/p95/max `6.32s/6.59s/6.64s`.
  - `30 câu / 10 user`: `30/30`, pass rate `100%`, p50/p95/max `56.01s/57.82s/57.91s`.
- Evidence cuối: `tests/benchmarks/evidence/rag-voice-2026-05-25-final/` gồm screenshot frontend, audio input, ASR input, audio output, ASR output, voice chat JSON, animation JSON và browser report.
- Report tổng quan tiếng Việt đã tạo tại `tests/benchmarks/REPORT-2026-05-25-rag-voice.md`; README benchmark tại `tests/benchmarks/README.md`.
- Resource không vượt ngưỡng user yêu cầu: RAM used khoảng `31%`, VRAM used khoảng `81%`, dưới mức stop/kill `90%`.
- Rủi ro còn lại: 10-user latency `56-58s` chưa thật sự nhanh nếu SLA mong muốn dưới `15s`; cold-start Riva TTS sau restart vẫn có thể timeout lần đầu; ASR confidence thấp nên không dùng ASR làm judge correctness RAG.
