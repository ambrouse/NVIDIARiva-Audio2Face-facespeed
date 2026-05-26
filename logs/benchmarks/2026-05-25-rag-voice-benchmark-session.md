# Session Log: RAG Voice Benchmark

- Started: 2026-05-25 12:13 +07
- Updated: 2026-05-25 14:20 +07
- Status: blocked by Riva voice dependency
- Related plan: `plans/running/plan-2026-05-25-rag-voice-benchmark-current.md`
- Related doc: `docs/benchmarks/2026-05-25-rag-voice-benchmark-current.md`

## Timeline

- Moved project ports into `6000-6500`: backend `6320`, frontend `6310`, provider bridges `6105/6106/6107`.
- Added guarded ingest and benchmark tooling with RAM/VRAM/disk samples.
- Downloaded 100 real arXiv PDFs, then metadata later reached 102 after replacement attempts.
- Optimized ingest embedding pipeline to batch chunk embeddings with delay.
- Ingested PDF corpus slowly with VRAM guard. Main loop reached 97 OK from first 100.
- Reconciled `2605.22730v1` after client timeout; backend had already persisted it.
- Added `--only-ids` and `--request-timeout` to the ingest tool for targeted retry.
- Raised Docling timeout to 180s and set `RAG_REINDEX_ON_LOAD=false` so backend startup does not reindex the full corpus.
- Retried `2605.22743v1`; monitor stopped immediately when VRAM free fell below 12234 MiB, but the PDF had already persisted OK.
- Retried `2605.22742v1`; ingest report reached 100 OK / 100 results.
- Cleaned 2 extra replacement documents from backend/DB/vector store after the first 100 corpus files were fully indexed.
- Started benchmark `10 câu x 1 user`; stopped after case 1 failed with latency 407.70s.
- Latest job logs show Riva TTS `127.0.0.1:6051` connection refused.

## Verification

- `python -m py_compile tests/benchmarks/arxiv_corpus.py tests/benchmarks/rag_chatbot_benchmark.py tests/benchmarks/resource_guard.py`: pass earlier in session.
- `backend/.venv-linux/bin/python -m pytest tests/backend/test_config.py tests/backend/test_rag_api.py::testIngestEmbedsChunksInSmallBatches -q`: pass earlier in session.
- `python -m py_compile tests/benchmarks/arxiv_corpus.py`: pass after `--only-ids` and `--request-timeout` changes.
- `backend/.venv-linux/bin/python -m pytest tests/backend/test_config.py -q`: pass after Docling timeout config change.
- Ingest report: 100 OK / 100 results, 0 fail.
- Benchmark `10x1`: attempted, case 1 failed because voice output pipeline cannot reach Riva TTS.

## Resource Notes

- Lowest safe ingest baseline before stop: about 12578 MiB VRAM free.
- Stop event during retry: VRAM free dropped to 11950 MiB; monitor stopped the retry process.
- RAM available stayed above 82 GB during guarded ingest/retry.
- Backend RSS stayed near 1.06 GB during replacement ingest.

## Blocker

Cannot pass real voice benchmark until Riva TTS is online at `6051` and ASR is online at `6052`. The current failure is not accepted as pass because audio output is missing.
