# Tests

Thư mục `tests/` hiện tập trung vào benchmark RAG Voice có artifact thật. Test unit/backend cũ đã được dọn khỏi root test tree trong worktree hiện tại; nếu cần khôi phục test tự động, đặt lại theo convention pytest ở root hoặc `backend/tests/`.

## Kết Quả Đáng Đọc

| Tài liệu | Nội dung |
| --- | --- |
| [`benchmarks/README.md`](benchmarks/README.md) | Bản đọc nhanh: accuracy, latency, VRAM, câu hỏi - câu trả lời mẫu. |
| [`benchmarks/REPORT-2026-05-25-rag-voice.md`](benchmarks/REPORT-2026-05-25-rag-voice.md) | Báo cáo đầy đủ cho benchmark ngày 2026-05-25. |
| [`benchmarks/LATEST.md`](benchmarks/LATEST.md) | Snapshot mới nhất. |
| [`nginx-proxy/README.md`](nginx-proxy/README.md) | Smoke evidence cho nginx proxy `6300` và backend API qua `/api/*`. |

## Kết Quả Hiện Tại

| Metric | Value |
| --- | ---: |
| PDF dùng trong benchmark | 100 |
| Chunk đã index | 11,022 |
| Tổng case | 80 |
| Pass | 80/80 |
| Đúng file/page/chunk | 100% |
| Single-user p50 | khoảng 6.3s |
| 10-user p95 | khoảng 58s |

Các artifact lớn trong `benchmarks/runs/` và `benchmarks/evidence/` là dữ liệu kiểm chứng. Không cần đọc hết để review nhanh; bắt đầu từ `benchmarks/README.md`.

## Smoke Vận Hành

| Area | Evidence |
| --- | --- |
| Nginx proxy `6300` | [`nginx-proxy/test-nginx-proxy-20260526-v1.md`](nginx-proxy/test-nginx-proxy-20260526-v1.md) |
