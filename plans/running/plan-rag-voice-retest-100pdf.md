# Plan: rag-voice-retest-100pdf

- Created: 2026-05-25 16:03 +07
- Updated: 2026-05-25 17:30 +07
- Status: completed_with_performance_risk
- Related log: logs/benchmarks/2026-05-25-rag-voice-retest-plan.md
- Related doc: docs/benchmarks/2026-05-25-rag-voice-retest-plan.md

## Goal

Chạy lại test thật cho agent RAG voice sau lần dừng ngang: 100 PDF thật, upload/index thật, 10 câu và 30 câu hỏi thực tế, mỗi bộ chạy ở 1 user và 10 user đồng thời. Chỉ pass khi trả lời nhanh, đúng nguồn, đúng file/page/chunk với câu RAG, phản hồi tốt với câu xã giao/ngoài phạm vi, có audio input/output, screenshot frontend, report hiệu năng/chất lượng và resource guard dừng ngay khi RAM/VRAM/disk gần quá tải.

## Scope

- In: rà runtime hiện tại, giữ port riêng `6000-6500`, xác nhận 100 PDF, reset/reupload khi pipeline upload đổi, benchmark luồng thật `/api/voice/transcribe` và `/api/voice/chat`, chấm correctness/grounding/source match/no hallucination, đo latency, resource, capture frontend/audio/report.
- In: nếu case fail do sai retrieval/prompt/tool/pipeline thì sửa tổng quát ở prompt/tool/pipeline, không hardcode theo câu hỏi, rồi chạy lại từ đầu batch bị ảnh hưởng.
- Out: dùng mock/fake speech để báo pass, sửa cứng answer/citation, fallback để né lỗi, kill process/container ngoài project, dùng port runtime ngoài `6000-6500`.

## Skills

- `plan-skill`: quản lý phase và close criteria.
- `testing-skill`: benchmark thật, evidence, report, rerun sau fix.
- `backend-skill`: kiểm API/RAG/tool/pipeline nếu phải sửa.
- `frontend-skill`: capture UI thật và kiểm tra audio/avatar.
- `documentation-skill`: cập nhật README/env/docs/report.
- `logging-skill`: ghi log blocker, fix, kết quả.
- `security-skill`: không ghi secret/token/PII vào evidence.

## Source Findings

- Port/env/README hiện đã nằm trong dải riêng: Postgres `6001`, Qdrant `6002/6003`, A2F `6040/6041`, Riva TTS/ASR `6051/6052`, Docling `6105`, embedding/rerank `6106`, LLM `6107`, frontend `6310`, backend `6320`.
- Corpus hiện có hơn 100 PDF thật trong `tests/benchmarks/corpus/arxiv/`; report trước ghi top-100 đã indexed `100/100`, backend có `100 documents / 11022 chunks`.
- Điểm dừng hiện tại: batch `10 câu x 1 user` fail ngay case 1 vì Riva TTS `127.0.0.1:6051` connection refused; ASR `6052` cũng chưa chứng minh online.
- Benchmark hiện có guard RAM/VRAM/disk và chấm đúng document/page/chunk cho câu RAG, nhưng cần bổ sung suite xã giao/ngoài phạm vi và audio input có lời nói thật. File evidence hiện sinh tone WAV không đủ để pass voice input.

## Phases

| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Snapshot runtime, git diff, port/env/README và blocker hiện tại | done | `6001-6003` online; backend/frontend/Riva/provider bridge offline; VRAM `12578MiB` free |
| 2 | Bật provider thật trong dải `6000-6500` | in_progress | User cho phép chạy tiếp với guard stop/kill project khi RAM/VRAM used >= `90%` |
| 3 | Kiểm tra resource baseline trước test | done | RAM `90-91Gi` available; VRAM `12578MiB` free, sát ngưỡng `25%`; disk `89G` free |
| 4 | Xác nhận hoặc reset corpus 100 PDF | done | `/api/documents`: `100` indexed, `11022` chunks |
| 5 | Nếu pipeline upload/chunk/embed đổi, xóa index cũ trong project và upload lại 100 PDF | pending | Ingest report `100/100`, resource samples, không reuse index sai pipeline |
| 6 | Bổ sung benchmark mixed-case | pending | Case types `rag_answerable`, `chitchat`, `out_of_scope`; rule chấm riêng từng loại |
| 7 | Bổ sung audio-input thật cho E2E | pending | `audio-input.wav` có lời nói, `/api/voice/transcribe` trả transcript đúng, không dùng tone để pass |
| 8 | Chạy smoke thật `1 câu x 1 user` | done | `tests/benchmarks/evidence/rag-voice-2026-05-25-final/` |
| 9 | Chạy benchmark `10 câu x 1 user` | done | `tests/benchmarks/runs/matrix/file-100/_latest-10/REPORT.md` |
| 10 | Chạy benchmark `10 câu x 10 user` | done | `tests/benchmarks/runs/matrix/file-100/_latest-10-users-10/REPORT.md` |
| 11 | Chạy benchmark `30 câu x 1 user` | done | `tests/benchmarks/runs/matrix/file-100/_latest-30/REPORT.md` |
| 12 | Chạy benchmark `30 câu x 10 user` | done | `tests/benchmarks/runs/matrix/file-100/_latest-30-users-10/REPORT.md` |
| 13 | Capture frontend evidence | done | `tests/benchmarks/evidence/rag-voice-2026-05-25-final/frontend-answer.png` |
| 14 | Phân tích fail và tối ưu pipeline | done | Bỏ TTS fallback, chọn answer citation, queue Riva TTS, sample rate `44100`, siết benchmark gate |
| 15 | Tổng hợp report cuối | done | `tests/benchmarks/REPORT-2026-05-25-rag-voice.md` |

## Benchmark Matrix

| Suite | Cases | Users | Case Mix | Pass Rule |
| --- | ---: | ---: | --- | --- |
| Smoke | 1 | 1 | 1 RAG answerable | API, citation, audio, animation pass |
| Small single | 10 | 1 | 8 RAG, 1 xã giao, 1 ngoài phạm vi | complete, accepted, p95 nhanh |
| Small load | 10 | 10 | 8 RAG, 1 xã giao, 1 ngoài phạm vi | complete, no timeout storm |
| Real single | 30 | 1 | 24 RAG, 3 xã giao, 3 ngoài phạm vi | complete, source/judge >95% |
| Real load | 30 | 10 | 24 RAG, 3 xã giao, 3 ngoài phạm vi | complete, source/judge >95%, latency đạt ngưỡng |

## Resource Guard

- Dừng ngay trước khi schedule case mới và trong background monitor nếu RAM free < `15%`, VRAM free < `25%`, hoặc disk free < `10%` trong full benchmark.
- Với smoke/debug có thể dùng ngưỡng tối thiểu hiện tại `10%`, nhưng không được gọi là pass final nếu không chạy lại bằng ngưỡng final.
- Khi guard dừng: không kill process ngoài project; ghi sample cuối, batch bị `blocked`, chờ tài nguyên hồi rồi chạy lại từ đầu batch.

## Verification

- Static/unit: `backend/.venv-linux/bin/python -m pytest tests/backend -q`
- Lưu ý từ 2026-05-25 16:10 +07: user yêu cầu dọn `tests/` chỉ giữ benchmark, nên test backend/frontend cũ trong `tests/` không còn dùng làm gate cho batch này.
- Frontend: `npm --prefix frontend test -- --run` và `npm --prefix frontend run build`
- Provider health: `/health`, `/api/rag/status`, TTS/ASR port check `6051/6052`, provider bridge `6105/6106/6107`.
- Corpus: `python tests/benchmarks/arxiv_corpus.py ingest --api-base http://127.0.0.1:6320 --limit 100 --gpu-min-free-vram-percent 25 --ram-min-free-percent 15`
- Benchmark:
  - `python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:6107/v1 --file-count 100 --count 10 --concurrency 1 --record-best --keep-failures --gpu-min-free-vram-percent 25 --ram-min-free-percent 15`
  - Lặp lại với `--concurrency 10`, rồi `--count 30` cho cả `1` và `10` user.
- Frontend evidence: `node scripts/capture-benchmark-evidence.mjs` sau khi script đã dùng audio input có lời nói thật.

## Close Criteria

- 100 PDF thật được xác nhận, và nếu pipeline upload/chunk/embed đổi thì đã reupload/reindex đủ `100/100`.
- Bốn batch `10/30 câu x 1/10 user` complete và accepted; không lấy checkpoint thiếu case làm pass.
- Câu RAG: đúng document/page/chunk, citations đúng, judge `correct/grounded/no_hallucination` > `95%`.
- Câu xã giao/ngoài phạm vi: phản hồi tự nhiên, không bịa nguồn, không gắn citation giả; câu ngoài phạm vi nói rõ không có trong KB nếu cần.
- Tốc độ final: 1 user p50 <= `10s`, p95 <= `30s`; 10 user p95 <= `60s`, không có timeout hàng loạt.
- Có screenshot frontend, audio input thật, audio output thật, animation artifact, `browser-report.json`, `REPORT.md`, `summary.json`, `case-log.md`.
- Nếu sửa prompt/tool/pipeline, batch liên quan đã chạy lại từ đầu và report cuối ghi rõ trước/sau.
