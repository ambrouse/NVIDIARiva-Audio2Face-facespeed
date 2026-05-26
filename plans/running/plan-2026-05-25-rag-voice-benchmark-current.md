# Plan: 2026-05-25-rag-voice-benchmark-current

- Created: 2026-05-25 12:13 +07
- Updated: 2026-05-25 14:20 +07
- Status: blocked by Riva voice dependency
- Related log: `logs/benchmarks/2026-05-25-rag-voice-benchmark-session.md`
- Related doc: `docs/benchmarks/2026-05-25-rag-voice-benchmark-current.md`

## Goal

Test thật agent RAG voice với tối thiểu 100 PDF thật, 10 câu và 30 câu hỏi thực tế, mỗi bộ ở 1 user và 10 user đồng thời. Chỉ pass khi nhanh, đúng nguồn, đúng file/page/chunk, có audio input/output, screenshot frontend và report hiệu năng/chất lượng.

## Scope

- In: port riêng `6000-6500`, corpus PDF thật, ingest thật, benchmark API thật, resource guard RAM/VRAM/disk, report và evidence.
- Out: kill hoặc chỉnh service ngoài dự án khi chưa có lệnh rõ.

## Skills

- `plan-skill`
- `testing-skill`
- `backend-skill`
- `frontend-skill`
- `documentation-skill`
- `logging-skill`

## Phases

| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Đọc lại source/plan/runtime | done | backend, benchmark scripts, docs cũ |
| 2 | Chuẩn hóa port `6000-6500` | done | `.env`, `.env.example`, config, docs |
| 3 | Thêm guard và batch ingest | done | `resource_guard.py`, `ragEmbeddingBatchSize=2` |
| 4 | Tải và ingest PDF thật | done | top-100 benchmark corpus indexed 100/100 |
| 5 | Retry/fix pipeline upload | done | reconcile timeout, `--only-ids`, request timeout, Docling timeout, load no reindex |
| 6 | Benchmark `10/30 x 1/10 user` | blocked | `10x1` case 1 failed: Riva TTS `6051` offline |
| 7 | Frontend screenshot/audio evidence | pending | chờ real voice API pass |
| 8 | Final report | pending | chờ benchmark pass |

## Verification

- Compile benchmark tools: pass.
- Backend config tests: pass.
- Ingest report: 100 OK / 100 results, 0 fail.
- Resource guard stop: triggered when VRAM free dropped below 12234 MiB.
- Benchmark `10x1`: attempted; case 1 failed with Riva TTS connection refused.

## Close Criteria

- Riva TTS `6051` và ASR `6052` online trước khi chạy voice benchmark tiếp.
- VRAM free ổn định trên 12234 MiB trước khi chạy tiếp.
- Có đúng 100 document sạch được chọn cho benchmark.
- Bốn batch benchmark pass với report và evidence.
- Docs/log/plan final được cập nhật.
