# Nginx Proxy Tests

Thư mục này lưu smoke test cho nginx proxy của môi trường dev. Mục tiêu là chứng minh browser chỉ cần mở `http://127.0.0.1:6300/`, trong khi nginx tự chuyển app request tới frontend `6310` và API request tới backend `6320`.

## Nội Dung

| File | Nội dung |
| --- | --- |
| `test-nginx-proxy-20260526-v1.md` | Báo cáo smoke test nginx proxy sau khi thêm Docker Compose service. |
| `evidence-2026-05-26/` | Ảnh Playwright và README evidence cho lần test ngày 2026-05-26. |

## Khi Nào Dùng

Dùng test này sau khi chỉnh `docker-compose.yml`, `docker/nginx/`, `scripts/setup.sh`, port frontend/backend hoặc cấu hình `VITE_API_BASE_URL`.
