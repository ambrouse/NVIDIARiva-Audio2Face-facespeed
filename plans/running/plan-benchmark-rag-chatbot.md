# Plan: benchmark-rag-chatbot

> Latest clearer plan name: `plans/running/plan-2026-05-25-rag-voice-benchmark-current.md`

- Created: 2026-05-23 20:11
- Updated: 2026-05-25 09:38
- Status: in_progress
- Related log: logs/benchmarks/rag-chatbot-benchmark.md
- Related doc: docs/benchmarks/rag-chatbot-benchmark.md

## Goal
Khôi phục test đang dừng ngang và chạy lại benchmark thật cho agent RAG voice với 100 PDF thật, 10 câu và 30 câu hỏi thực tế, mỗi mốc chạy ở 1 user và 10 user đồng thời. Hệ thống chỉ pass khi trả lời nhanh, đúng nguồn, đúng file/page/chunk, có audio input/output, có screenshot frontend, report hiệu năng/chất lượng rõ ràng và resource guard dừng ngay nếu RAM/VRAM/disk xuống dưới ngưỡng an toàn.

## Scope
- In: rà source/plan hiện tại, cấu hình port riêng trong `6000-6500`, tải đủ tối thiểu 100 PDF open-access, upload/ingest thật, benchmark `/api/voice/chat` thật, chấm correctness/grounding/hallucination/source match, đo latency p50/p95/max, chạy concurrency `1` và `10`, lưu screenshot/audio/report, sửa lỗi bằng prompt/tool/pipeline tổng quát rồi chạy lại từ đầu batch bị ảnh hưởng.
- Out: sửa cứng theo câu hỏi, fallback để né fail, dùng mock artifact để báo pass real voice, đụng project/port ngoài repo, xóa thay đổi người dùng không liên quan.

## Skills
- plan-skill: quản lý phase và close criteria.
- testing-skill: benchmark, evidence, report, rerun sau fix.
- backend-skill: kiểm API/RAG/tool/pipeline.
- frontend-skill: screenshot UI thật.
- documentation-skill: README/env/docs/report.
- logging-skill: log phase, blocker, kết quả.
- security-skill: không ghi secret/PII/token vào evidence.

## Risks
- Backend hiện không chạy; cần restart bằng port mới `6320`.
- Corpus hiện có 14 PDF, cần tải thêm để đạt tối thiểu 100 PDF thật.
- Ingest trước đó từng fail CUDA OOM; ingest/benchmark phải chạy với resource guard.
- Provider hiện nghe ở một số port ngoài dải mới (`8005-8007`); để pass theo yêu cầu port riêng cần chạy hoặc proxy provider ở `6105-6107`, không dùng lẫn project khác.
- Riva real voice phải online ở `6051` và ASR ở `6052`; nếu offline thì batch voice chưa pass.

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Đọc lại plan/source/runtime và xác nhận điểm dừng | done | plan cũ, `_latest-300` incomplete 293/300, backend 8020 offline |
| 2 | Chuyển cấu hình project sang port riêng `6000-6500` | done | `.env`, `.env.example`, `README.md`, `docs/operations.md`, config/test cập nhật |
| 3 | Thêm resource guard cho ingest/benchmark | done | py_compile pass; runner/ingester có RAM/VRAM/disk guard |
| 4 | Tải đủ 100 PDF thật và ingest/upload lại nếu pipeline upload đổi | done | Top-100 corpus indexed `100/100`, backend `100 documents / 11022 chunks` |
| 5 | Chạy benchmark 10 câu: 1 user rồi 10 user | blocked | `10x1` case 1 fail vì Riva TTS `6051` offline |
| 6 | Chạy benchmark 30 câu: 1 user rồi 10 user | pending | `tests/benchmarks/runs/matrix/file-100/` |
| 7 | Chụp frontend và lưu audio input/output | pending | `tests/benchmarks/evidence/rag-voice-YYYY-MM-DD/` |
| 8 | Nếu case false thì sửa prompt/tool/pipeline tổng quát, reset batch liên quan và chạy lại từ đầu | pending | git diff + rerun report |
| 9 | Báo cáo cuối hiệu năng/chính xác/source/hallucination/resource | pending | `docs/benchmarks/rag-chatbot-benchmark.md` |

## Verification
- `backend/.venv-linux/bin/python -m pytest tests`
- `npm --prefix frontend test -- --run`
- `npm --prefix frontend run build`
- `python tests/benchmarks/arxiv_corpus.py download --limit 100`
- `python tests/benchmarks/arxiv_corpus.py ingest --limit 100 --api-base http://127.0.0.1:6320`
- `python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:6107/v1 --file-count 100 --count 10 --concurrency 1 --record-best`
- `python tests/benchmarks/rag_chatbot_benchmark.py --api-base http://127.0.0.1:6320 --llm-base http://127.0.0.1:6107/v1 --file-count 100 --count 10 --concurrency 10 --record-best`
- Lặp lại hai command trên với `--count 30`.
- `node scripts/capture-benchmark-evidence.mjs`

## Close Criteria
- Có tối thiểu 100 PDF thật tải về và 100 document indexed OK.
- Bốn batch `10/30 câu x 1/10 user` complete, accepted, source document/page/chunk đúng, judge correctness/grounding/no-hallucination đạt >95%.
- Latency nhanh: p50 <= 10s, p95 <= 30s cho 1 user; concurrency 10 không có timeout hàng loạt và p95 <= 60s.
- Có screenshot frontend thấy input/output, audio input, audio output, artifact/report và resource samples.
- Nếu sửa prompt/tool/pipeline, batch liên quan được chạy lại từ đầu; không hardcode/fallback né fail.
- Không stop/xóa process/container không thuộc project; không dùng port ngoài dải `6000-6500` cho runtime project.
