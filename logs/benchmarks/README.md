# Benchmark Logs

Thư mục này lưu log ngắn và báo cáo phiên benchmark. Log ở đây dùng để hiểu một lần chạy benchmark đã làm gì, kết quả chính ra sao, blocker nào còn lại.

Nên giữ:

- File `.md` tổng kết benchmark.
- `LATEST.md` trỏ tới phiên mới nhất.
- Ghi chú bridge/provider chỉ khi cần tái hiện benchmark.

Không nên commit log runtime dài, PID file, hoặc output provider quá lớn. Các artifact kiểm chứng chính nằm trong `tests/benchmarks/`.
