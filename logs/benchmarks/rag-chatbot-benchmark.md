# Log: rag-chatbot-benchmark

> Latest session log: `logs/benchmarks/2026-05-25-rag-voice-benchmark-session.md`

- Started: 2026-05-23 20:11
- Status: in_progress
- Plan: plans/running/plan-benchmark-rag-chatbot.md
- Doc: docs/benchmarks/rag-chatbot-benchmark.md

## Ghi Nhận
- 2026-05-23 20:11: Runtime đang có 1 PDF / 10 chunks; Postgres/Qdrant/LLM online. Không đủ dữ liệu để kết luận benchmark 10/100/1000 file.
- 2026-05-23 20:18: Thêm downloader/ingester arXiv open-access tại `tests/benchmarks/arxiv_corpus.py`; mọi corpus/evidence benchmark sẽ nằm dưới `tests/benchmarks/`.
- 2026-05-23 20:35: Ingest được 13/14 PDF arXiv; 1 PDF còn fail do embedding CUDA OOM. Runtime đạt 14 documents / 1677 chunks tính cả PDF ban đầu.
- 2026-05-23 20:42: Smoke benchmark 5 câu fail do search vector trượt exact phrase và context teacher bị cắt ngắn.
- 2026-05-23 20:47: Tối ưu pipeline chung: chunker chia đoạn >2200 ký tự, teacher/review đọc full chunk context, search thêm lexical candidate layer. Smoke benchmark 5/5 pass 100%.
- 2026-05-23 20:58: Dừng benchmark chỉ dựa API/check kỹ thuật theo nhắc nhở của user. Thêm LLM judge strict để chấm correctness, grounding và hallucination từ answer + cited context; API 200/audio/dashboard không còn đủ để pass.
- 2026-05-23 22:10: Đọc lại README/docs/plans/logs/source benchmark. Runtime online với 14 documents / 1677 chunks; corpus arXiv tải 14 PDF, ingest 13/14, 1 PDF fail do embedding CUDA OOM. `best-100` cũ đạt 98% nhưng trước strict document/page checks; `_latest-100` strict mới checkpoint 4/100 nên cần chạy lại 100 case đầy đủ.
- 2026-05-23 22:15: Chạy strict `_latest-100` mới và dừng ở 30 case vì đã có 6 fail, không thể đạt ngưỡng 95%. Pattern: retrieval/citation đúng document/page/chunk, nhưng teacher kéo chi tiết từ citation phụ trang xa.
- 2026-05-23 22:20: Sửa backend để câu hỏi có quoted phrase trả lời extractive từ primary citation trước, tránh drift sang context phụ; thêm regression test. Verify 6/6 fail cũ pass strict LLM judge khi chạy không qua TTS.
- 2026-05-23 22:21: Verify source pass: `backend/.venv-linux/bin/python -m pytest tests -q` = 43 passed; `npm --prefix frontend test -- --run` = 4 passed; `npm --prefix frontend run build` pass. Full voice benchmark đang blocked vì Riva TTS `127.0.0.1:50051` offline, `/api/voice/chat` trả 503 ở bước audio.
- 2026-05-23 22:29: Cập nhật plan theo yêu cầu mới: ma trận `10/100/1000` file x `100/300/500` câu, bắt đúng answer/file/page/chunk/hallucination, không hardcode/fallback, sau mỗi đổi pipeline phải chạy lại batch từ đầu. Đóng plan cũ `real-db-llm-graph-rag`.
- 2026-05-23 22:31: Sửa benchmark runner: thêm `--file-count`, thư mục `tests/benchmarks/runs/matrix/file-{N}/`, gate `complete=false => accepted=false`, và tách check `expected_chunk_cited` + `expected_page_cited`.
- 2026-05-23 23:10: Chạy 10-file x100 ở `PIPELINE_MODE=mock` vì Riva TTS offline. Khi gặp fail, dừng batch, sửa tổng quát và chạy lại từ đầu: extractor lấy surrounding context dài hơn, xử lý phrase qua ranh giới câu, runner lọc math/formula/reference noise.
- 2026-05-23 23:33: 10-file x100 complete/pass: `100/100`, correctness/grounding/no-hallucination/document/page/chunk/dashboard/audio-url/animation-url đều `100%`. Lưu best-run tại `tests/benchmarks/runs/matrix/file-10/best-100/`. Artifact audio/animation là mock pipeline, không tính là real Riva voice evidence.
- 2026-05-25 09:38: Khôi phục task theo yêu cầu mới. Backend cũ `8020` offline; run cũ `file-10/_latest-300` dừng `293/300`, `accepted=false`. RAM available khoảng `99GiB/125GiB`, VRAM free khoảng `19.5GiB/47.8GiB`. Port `6000` đang bị service khác dùng; các port `6040/6041/6051/6052/6105/6106/6107/6310/6320` đang trống.
- 2026-05-25 09:50: Chuyển default runtime project sang dải `6000-6500`: backend `6320`, frontend `6310`, Postgres/Qdrant `6001-6003`, A2F `6040/6041`, Riva `6051/6052`, Docling/Embedding/LLM `6105-6107`. Cập nhật `.env.example`, README/docs, frontend config/test và backend config/test.
- 2026-05-25 10:05: Thêm `tests/benchmarks/resource_guard.py`, tích hợp guard vào `arxiv_corpus.py` khi ingest và `rag_chatbot_benchmark.py` khi chạy benchmark. Runner hỗ trợ `--count 30`, `--concurrency 1|10`, resource samples trong report, và evidence capture script `scripts/capture-benchmark-evidence.mjs`.
- 2026-05-25 10:18: arXiv API query bị `429 Too Many Requests`; thêm retry/backoff và fallback `download-direct`. Tải đủ `100` PDF thật trong `tests/benchmarks/corpus/arxiv/`, `metadata.json` có `100` entry. Chưa ingest vì backend `127.0.0.1:6320` chưa online và GPU utilization đang `99%`; theo guard không chạy upload/ingest GPU-heavy lúc này.
- 2026-05-25 10:54: Start backend/frontend trên port mới `6320/6310`; cập nhật `.env` thật để runtime đọc `6105/6106/6107` và `6051/6052`. Mở port-forward project-owned `6105->8005`, `6106->8006`, `6107->8007`; backend status thấy LLM available.
- 2026-05-25 10:58: Bắt đầu ingest 100 PDF với guard. Runtime tăng tới khoảng `18 documents / 2077 chunks`, nhưng VRAM tụt còn `882 MiB free / 48935 MiB` (<10%). Dừng ingest ngay và stop backend project để cắt request. Sau khi dừng, VRAM hồi lên khoảng `16804 MiB free`. Thêm checkpoint incremental cho `arxiv_corpus.py` để không mất tiến độ nếu phải dừng khẩn cấp.
- 2026-05-25 10:59: Verify nhanh: `python -m py_compile tests/benchmarks/arxiv_corpus.py tests/benchmarks/rag_chatbot_benchmark.py tests/benchmarks/resource_guard.py` pass; `backend/.venv-linux/bin/python -m pytest tests/backend/test_config.py -q` = 2 passed; `npm --prefix frontend test -- --run tests/frontend/App.test.tsx` = 4 passed.
- 2026-05-25 11:17: Sửa pipeline ingest nhẹ hơn: backend embed chunks theo batch `RAG_EMBEDDING_BATCH_SIZE=4`, delay `0.5s` giữa batch; ingester thêm `--max-new` để chạy từng nhóm nhỏ. Verify `test_config.py` + `testIngestEmbedsChunksInSmallBatches` = 3 passed. Chạy lại ingest từng lượt `--max-new 3`, guard VRAM 25%, delay 3s. Kết quả runtime đạt `26 documents / 2900 chunks`, report checkpoint `25/25`, VRAM giữ khoảng `16798 MiB free`; backend/port-forward đã stop sau lượt này.
- 2026-05-25 14:20: Hoàn tất ingest top-100 corpus: `100/100` OK, backend status `100 documents / 11022 chunks`. Sửa pipeline test: `--only-ids`, `--request-timeout`, Docling timeout `180s`, `RAG_REINDEX_ON_LOAD=false` để backend không reindex toàn bộ corpus khi khởi tạo. Thử benchmark `10x1`; case đầu fail sau `407.70s` vì Riva TTS `127.0.0.1:6051` connection refused. Dừng batch, chưa chạy `10x10/30x1/30x10`, chưa tạo frontend/audio evidence vì real voice dependency offline.
