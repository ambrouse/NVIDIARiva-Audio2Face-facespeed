# Evidence: nginx-proxy 2026-05-26

Evidence này chứng minh app mở được qua nginx proxy `http://127.0.0.1:6300/`.

| File | Nội dung |
| --- | --- |
| `nginx-proxy-home.png` | Ảnh Playwright desktop 1440x900 sau khi mở app qua `6300`; app shell hiển thị, badge tài liệu `100`, ASR on, trạng thái avatar idle. |

## Đọc Ảnh

Ảnh không phải benchmark RAG trả lời câu hỏi. Nó chỉ chứng minh proxy frontend hoạt động và UI chính render qua nginx. Kết quả API được ghi riêng trong `../test-nginx-proxy-20260526-v1.md`.
