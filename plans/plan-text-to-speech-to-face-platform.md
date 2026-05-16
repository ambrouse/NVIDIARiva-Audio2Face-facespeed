# Plan tổng: Web Text → Speech → Face với NVIDIA Riva và Audio2Face

## 1. Mục tiêu dự án

Xây dựng một nền tảng web cho pipeline:

```text
User Text Input → Text Processing → NVIDIA Riva TTS → Audio Output → NVIDIA Audio2Face → Face Animation/Stream/Export
```

Dự án cần có đầy đủ:

- Backend API điều phối pipeline Text → Speech → Face.
- Frontend web dashboard để người dùng nhập text, chạy pipeline và quản trị service.
- Dashboard quản lý bật/tắt/khởi động lại NVIDIA Riva và NVIDIA Audio2Face.
- Giao diện xem logs realtime của tất cả service đang chạy.
- File `setup.sh` kiểm tra phần cứng, driver, Docker, NVIDIA Container Toolkit, Riva, Audio2Face, thư viện hệ thống và tự động cài/bật thành phần cần thiết nếu thiếu.
- Tài liệu vận hành, testing, logging và quy trình push code.

## 2. Phạm vi chính

### 2.1 Backend

Backend chịu trách nhiệm:

- Nhận text từ frontend.
- Validate input ở boundary.
- Gọi NVIDIA Riva TTS để sinh audio.
- Lưu hoặc stream audio output.
- Gửi audio sang NVIDIA Audio2Face.
- Điều phối trạng thái job pipeline.
- Quản lý service Riva/A2F: start, stop, restart, status, health check.
- Gom logs từ backend, Riva, A2F, setup, worker và hệ thống.
- Cung cấp WebSocket/SSE cho logs realtime và trạng thái job.
- Cung cấp REST API cho dashboard.

### 2.2 Frontend

Frontend dashboard cần có:

- Màn hình nhập text và chọn voice/config.
- Màn hình chạy pipeline Text → Speech → Face.
- Trạng thái realtime của job.
- Audio preview.
- Preview hoặc link stream/export từ Audio2Face.
- Trang service dashboard:
  - Riva status.
  - Audio2Face status.
  - GPU status.
  - Backend worker status.
  - Nút start/stop/restart từng service.
- Trang logs:
  - Logs realtime theo service.
  - Filter theo service, level, keyword, thời gian.
  - Download logs.
- Trang setup/system check:
  - Driver/GPU/CUDA/Docker status.
  - Riva installed/running.
  - Audio2Face installed/running.
  - Library status.
  - Gợi ý lệnh sửa lỗi nếu auto-fix không thể chạy.

### 2.3 DevOps / setup

Cần có:

- `setup.sh` cho Linux host.
- Docker Compose hoặc scripts quản lý service.
- `.env.example` cho config.
- Health check scripts.
- Log folder chuẩn.
- Tài liệu cài đặt và vận hành.

## 3. Kiến trúc đề xuất

```text
┌──────────────────────────────┐
│ Frontend Dashboard            │
│ - Text input                  │
│ - Service control             │
│ - Logs viewer                 │
│ - Job monitor                 │
└───────────────┬──────────────┘
                │ REST + WebSocket/SSE
┌───────────────▼──────────────┐
│ Backend API                   │
│ - Auth/config boundary        │
│ - Pipeline orchestration      │
│ - Service manager             │
│ - Log streaming               │
│ - Job state                   │
└───────┬──────────────┬───────┘
        │              │
        │ gRPC/HTTP    │ HTTP/gRPC/Local API
┌───────▼──────┐ ┌─────▼──────────────┐
│ NVIDIA Riva  │ │ NVIDIA Audio2Face   │
│ TTS Service  │ │ A2F App/Service     │
└───────┬──────┘ └─────┬──────────────┘
        │              │
        ▼              ▼
   Audio output   Face animation/stream/export

┌──────────────────────────────┐
│ Observability Layer           │
│ - Service logs                │
│ - Setup logs                  │
│ - Pipeline logs               │
│ - Health/status snapshots     │
└──────────────────────────────┘
```

## 4. Công nghệ đề xuất

### 4.1 Backend

Ưu tiên một trong hai hướng:

- Python FastAPI:
  - Phù hợp tích hợp NVIDIA SDK/gRPC/scripts.
  - Dễ viết orchestration, WebSocket, background jobs.
- Node.js/NestJS:
  - Phù hợp nếu team frontend mạnh TypeScript.

Khuyến nghị ban đầu: **Python FastAPI** vì pipeline AI/NVIDIA, script setup và xử lý audio thường thuận hơn.

Thành phần backend:

- FastAPI REST API.
- WebSocket hoặc SSE cho logs/job realtime.
- Background worker nội bộ hoặc Celery/RQ nếu job dài.
- SQLite/PostgreSQL cho job history/config.
- Filesystem hoặc object storage cho audio/export files.
- Service manager wrapper gọi Docker/systemd/process command an toàn.

### 4.2 Frontend

Khuyến nghị:

- React + TypeScript + Vite.
- Tailwind CSS hoặc shadcn/ui nếu cần UI nhanh, rõ và hiện đại.
- TanStack Query cho API state.
- WebSocket/SSE client cho logs realtime.
- Monaco/log viewer đơn giản cho logs.

### 4.3 NVIDIA Services

- NVIDIA Riva TTS chạy qua Docker/container theo hướng dẫn NVIDIA.
- NVIDIA Audio2Face chạy local app/service hoặc container nếu môi trường hỗ trợ.
- Backend không gọi command trực tiếp từ input người dùng; chỉ dùng allowlist action: `start`, `stop`, `restart`, `status`, `logs`.

### 4.4 Logs

Cấu trúc đề xuất:

```text
logs/
  backend/app.log
  backend/error.log
  riva/service.log
  audio2face/service.log
  setup/setup.log
  jobs/{job_id}.log
```

Backend expose logs qua API theo service name hợp lệ, không cho đọc path tùy ý từ client.

## 5. Các skill cần dùng

- `backend-skill`: dùng khi thiết kế API, service manager, job orchestration, validate input, tích hợp Riva/A2F.
- `frontend-skill`: dùng khi xây dashboard, trang pipeline, trang service control, trang logs.
- `frontend-design-skills`: dùng khi thiết kế UI/UX dashboard, bố cục, màu sắc, interaction, accessibility.
- `testing-skill`: dùng cho unit test, integration test, UI test, setup test, smoke test Riva/A2F.
- `documentation-skill`: dùng khi viết docs cài đặt, vận hành, API, troubleshooting.
- `logging-skill`: dùng để ghi log phiên làm việc và log triển khai từng phase.
- `security-skill`: dùng khi thiết kế endpoint điều khiển service, log viewer, command execution, config secrets.
- `push-code-skill`: dùng trước khi push code lên repository.

## 6. Roadmap tổng

## Phase 0: Khảo sát yêu cầu và môi trường

### Mục tiêu

Xác định chính xác môi trường chạy NVIDIA Riva và Audio2Face, phần cứng GPU, hệ điều hành, cách triển khai và ràng buộc vận hành.

### Việc cần làm

1. Xác định OS target: Ubuntu version, WSL hay bare metal.
2. Xác định GPU NVIDIA hỗ trợ CUDA.
3. Xác định driver/CUDA/NVIDIA Container Toolkit yêu cầu.
4. Xác định cách chạy Audio2Face: GUI app, headless mode, local service, streaming hoặc export.
5. Xác định output mong muốn:
   - Preview trong browser.
   - Export file animation.
   - Stream realtime.
6. Xác định có cần user auth hay chỉ dashboard nội bộ.

### Thời gian dự kiến

- 0.5 - 1 ngày.

### Tài nguyên cần thiết

- Máy NVIDIA GPU.
- Tài khoản NVIDIA NGC nếu cần tải Riva model/container.
- NVIDIA Riva documentation.
- NVIDIA Audio2Face documentation.

### Skill cần dùng

- `backend-skill`
- `security-skill`
- `documentation-skill`

### Điều kiện hoàn thành

- Có bảng yêu cầu môi trường.
- Có quyết định cách chạy Riva/A2F.
- Có checklist setup ban đầu.

---

## Phase 1: Khởi tạo cấu trúc dự án

### Mục tiêu

Tạo skeleton dự án gồm backend, frontend, scripts, logs, docs và config.

### Việc cần làm

1. Tạo cấu trúc thư mục:

```text
backend/
frontend/
scripts/
configs/
logs/
docs/
tests/
plans/
```

2. Tạo `.env.example` với các biến:

```text
BACKEND_HOST=
BACKEND_PORT=
RIVA_HOST=
RIVA_PORT=
A2F_HOST=
A2F_PORT=
LOG_DIR=
OUTPUT_DIR=
SERVICE_MANAGER_MODE=
```

3. Tạo file cấu hình service allowlist.
4. Tạo README hoặc docs setup nếu được yêu cầu.
5. Thiết lập formatter/linter/test runner.

### Thời gian dự kiến

- 0.5 - 1 ngày.

### Tài nguyên cần thiết

- Node.js nếu dùng React.
- Python nếu dùng FastAPI.
- Docker/Docker Compose nếu dùng container.

### Skill cần dùng

- `backend-skill`
- `frontend-skill`
- `documentation-skill`
- `testing-skill`

### Điều kiện hoàn thành

- Project có cấu trúc rõ.
- Backend/frontend chạy được ở chế độ dev.
- Có script test/lint cơ bản.

---

## Phase 2: Setup script `setup.sh`

### Mục tiêu

Tạo script kiểm tra và hỗ trợ cài đặt môi trường NVIDIA/Riva/A2F/thư viện cần thiết.

### Việc cần làm

1. Kiểm tra OS và quyền sudo.
2. Kiểm tra GPU:

```bash
nvidia-smi
```

3. Kiểm tra NVIDIA driver version.
4. Kiểm tra Docker.
5. Kiểm tra NVIDIA Container Toolkit.
6. Kiểm tra CUDA/cuDNN nếu cần.
7. Kiểm tra port cần dùng:
   - Backend port.
   - Riva port.
   - A2F port.
8. Kiểm tra Riva container/model tồn tại.
9. Kiểm tra Audio2Face cài đặt hoặc đường dẫn app.
10. Tự động cài package hệ thống an toàn nếu thiếu:
    - curl
    - git
    - docker dependencies
    - python/node runtime nếu project cần
11. Với thành phần cần license/tài khoản/manual download, script phải báo rõ và dừng có hướng dẫn.
12. Ghi log vào `logs/setup/setup.log`.
13. Hỗ trợ mode:

```bash
./setup.sh --check
./setup.sh --install
./setup.sh --start-services
./setup.sh --full
```

### Thời gian dự kiến

- 1 - 2 ngày.

### Tài nguyên cần thiết

- Linux host có GPU NVIDIA.
- Quyền sudo.
- Internet.
- Tài khoản NVIDIA/NGC nếu cần.

### Skill cần dùng

- `backend-skill`
- `security-skill`
- `testing-skill`
- `logging-skill`
- `documentation-skill`

### Điều kiện hoàn thành

- `setup.sh --check` chạy không phá hệ thống.
- `setup.sh --install` chỉ cài thứ nằm trong allowlist.
- Không tự động chạy lệnh nguy hiểm nếu chưa xác nhận.
- Có log setup rõ ràng.

---

## Phase 3: Backend service manager

### Mục tiêu

Backend có khả năng kiểm tra, bật, tắt, restart và lấy logs Riva/A2F qua API an toàn.

### API đề xuất

```text
GET  /api/services
GET  /api/services/{service_name}/status
POST /api/services/{service_name}/start
POST /api/services/{service_name}/stop
POST /api/services/{service_name}/restart
GET  /api/services/{service_name}/logs
WS   /ws/logs?service={service_name}
```

### Việc cần làm

1. Định nghĩa service allowlist:

```text
riva
audio2face
backend-worker
```

2. Tạo abstraction `ServiceManager`.
3. Implement adapter cho Docker Compose hoặc systemd/process.
4. Implement status/health check.
5. Implement logs reader theo allowlist path.
6. Implement realtime logs qua WebSocket/SSE.
7. Chặn mọi input có thể thành command injection.
8. Viết test cho allowlist và service actions.

### Thời gian dự kiến

- 2 - 3 ngày.

### Tài nguyên cần thiết

- Backend framework.
- Docker Compose/systemd config.

### Skill cần dùng

- `backend-skill`
- `security-skill`
- `testing-skill`
- `logging-skill`

### Điều kiện hoàn thành

- Dashboard có thể gọi API xem status.
- API chỉ cho thao tác service hợp lệ.
- Logs không đọc được file ngoài allowlist.
- Test pass.

---

## Phase 4: Backend pipeline Text → Speech → Face

### Mục tiêu

Xây API xử lý pipeline chính: text input → Riva TTS → audio → Audio2Face.

### API đề xuất

```text
POST /api/jobs
GET  /api/jobs/{job_id}
GET  /api/jobs/{job_id}/logs
GET  /api/jobs/{job_id}/audio
GET  /api/jobs/{job_id}/result
WS   /ws/jobs/{job_id}
```

### Job state đề xuất

```text
queued
validating_text
generating_speech
speech_ready
sending_to_a2f
animating_face
completed
failed
cancelled
```

### Việc cần làm

1. Tạo schema request:

```json
{
  "text": "...",
  "voice": "...",
  "language": "vi-VN",
  "a2fProfile": "default",
  "outputMode": "preview|export|stream"
}
```

2. Validate text length, language, voice allowlist.
3. Tích hợp Riva TTS client.
4. Lưu audio output theo job ID.
5. Tích hợp Audio2Face API/service.
6. Lưu result metadata.
7. Cập nhật trạng thái job realtime.
8. Ghi job log riêng.
9. Test với mock Riva/A2F trước, sau đó integration test với service thật.

### Thời gian dự kiến

- 3 - 5 ngày.

### Tài nguyên cần thiết

- Riva TTS model đã sẵn sàng.
- Audio2Face endpoint/app chạy được.
- Sample text tiếng Việt/tiếng Anh.

### Skill cần dùng

- `backend-skill`
- `security-skill`
- `testing-skill`
- `logging-skill`
- `documentation-skill`

### Điều kiện hoàn thành

- Tạo job từ text thành audio thành face result được.
- Có trạng thái realtime.
- Có audio/result truy xuất được.
- Có job logs.
- Test pass với mock và smoke test với NVIDIA service thật.

---

## Phase 5: Frontend dashboard nền tảng

### Mục tiêu

Xây frontend dashboard có layout, navigation và các trang chính.

### Trang cần có

1. Pipeline page:
   - Text input.
   - Voice/language/profile selection.
   - Run button.
   - Job progress.
   - Audio preview.
   - Face result preview/link.

2. Services page:
   - Riva card.
   - Audio2Face card.
   - Backend worker card.
   - GPU/system card.
   - Start/stop/restart actions.

3. Logs page:
   - Realtime log viewer.
   - Service filter.
   - Level filter.
   - Search keyword.
   - Pause/resume autoscroll.
   - Download logs.

4. Setup/System page:
   - Hardware/software checklist.
   - Missing dependencies.
   - Last setup run log.
   - Suggested command.

### Thời gian dự kiến

- 3 - 5 ngày.

### Tài nguyên cần thiết

- Frontend framework.
- API contract từ backend.
- Design direction.

### Skill cần dùng

- `frontend-skill`
- `frontend-design-skills`
- `testing-skill`
- `documentation-skill`

### Điều kiện hoàn thành

- Dashboard chạy được ở dev mode.
- Gọi được API backend.
- Hiển thị status/log/job realtime.
- UI responsive cơ bản.
- Có test UI hoặc smoke test thủ công ghi lại rõ.

---

## Phase 6: Logs và observability hoàn chỉnh

### Mục tiêu

Chuẩn hóa logging cho toàn hệ thống để dashboard có thể giám sát tất cả service.

### Việc cần làm

1. Chuẩn hóa log format:

```text
timestamp level service job_id message metadata
```

2. Backend app logs.
3. Job logs.
4. Setup logs.
5. Service logs Riva/A2F.
6. API đọc logs có pagination/tail.
7. WebSocket/SSE stream logs realtime.
8. Log rotation cơ bản.
9. UI filter logs theo service/level/keyword.

### Thời gian dự kiến

- 1 - 2 ngày.

### Tài nguyên cần thiết

- Logging library backend.
- Filesystem log directory.

### Skill cần dùng

- `logging-skill`
- `backend-skill`
- `frontend-skill`
- `testing-skill`

### Điều kiện hoàn thành

- Mỗi service có log riêng.
- Dashboard xem được logs realtime.
- Không expose path tùy ý.
- Có log rotation hoặc giới hạn đọc.

---

## Phase 7: Security hardening

### Mục tiêu

Đảm bảo dashboard quản trị service không tạo lỗ hổng command injection, path traversal, secret leak hoặc public exposure ngoài ý muốn.

### Việc cần làm

1. Service actions dùng allowlist, không nối command từ input thô.
2. Log viewer dùng service key, không nhận path từ client.
3. Validate text input và file output.
4. Không log secret/token.
5. CORS chỉ mở cho frontend origin hợp lệ.
6. Nếu dashboard không chỉ chạy local, thêm auth.
7. Rate limit endpoint tạo job.
8. Kiểm tra permission file logs/output.
9. Review `setup.sh` tránh chạy lệnh nguy hiểm không xác nhận.

### Thời gian dự kiến

- 1 - 2 ngày.

### Tài nguyên cần thiết

- Security checklist.
- Threat model ngắn.

### Skill cần dùng

- `security-skill`
- `backend-skill`
- `testing-skill`

### Điều kiện hoàn thành

- Pass security review nội bộ.
- Không có command injection từ service API.
- Không có path traversal ở logs/output API.
- Secret không xuất hiện trong logs.

---

## Phase 8: Testing tổng thể

### Mục tiêu

Đảm bảo từng phần và toàn pipeline hoạt động ổn định.

### Loại test cần có

1. Unit test backend:
   - validation.
   - service allowlist.
   - job state machine.
   - log path resolver.

2. Integration test backend:
   - mock Riva.
   - mock A2F.
   - job lifecycle.

3. Frontend test:
   - render dashboard.
   - service buttons.
   - log viewer.
   - job progress UI.

4. Setup test:
   - `setup.sh --check` trên máy không đủ dependency.
   - `setup.sh --check` trên máy đủ dependency.

5. Smoke test thật:
   - Start Riva.
   - Start Audio2Face.
   - Gửi text mẫu.
   - Nhận audio.
   - Nhận face result/preview/export.

### Thời gian dự kiến

- 2 - 3 ngày.

### Tài nguyên cần thiết

- Test runner backend/frontend.
- Máy GPU thật cho smoke test.

### Skill cần dùng

- `testing-skill`
- `backend-skill`
- `frontend-skill`
- `logging-skill`

### Điều kiện hoàn thành

- Unit/integration test pass.
- Smoke test NVIDIA thật được ghi nhận.
- Lỗi biên được ghi lại trong docs/logs.

---

## Phase 9: Documentation và vận hành

### Mục tiêu

Viết tài liệu đủ để cài đặt, chạy, debug và vận hành dự án.

### Tài liệu cần có

1. Setup guide.
2. Hardware/software requirements.
3. How to run backend.
4. How to run frontend.
5. How to start/stop Riva.
6. How to start/stop Audio2Face.
7. API docs.
8. Troubleshooting:
   - GPU not found.
   - Docker cannot access GPU.
   - Riva unavailable.
   - Audio2Face unavailable.
   - Port conflict.
   - Logs missing.
9. Testing guide.
10. Deployment/operations guide.

### Thời gian dự kiến

- 1 - 2 ngày.

### Tài nguyên cần thiết

- Documentation skill.
- Test results.
- Known issues từ implementation.

### Skill cần dùng

- `documentation-skill`
- `logging-skill`

### Điều kiện hoàn thành

- Người mới có thể setup theo docs.
- Có troubleshooting rõ.
- Có checklist vận hành.

---

## Phase 10: Review, push và quản trị release

### Mục tiêu

Review toàn bộ, đảm bảo test pass, ghi log/documentation và push code theo đúng quy trình.

### Việc cần làm

1. Review changed code.
2. Chạy lint/test toàn bộ.
3. Chạy security review.
4. Chạy smoke test nếu có GPU.
5. Cập nhật documentation task.
6. Cập nhật log task.
7. Commit theo message rõ ràng.
8. Push theo `push-code-skill`.

### Thời gian dự kiến

- 0.5 - 1 ngày.

### Tài nguyên cần thiết

- Git repository.
- Remote repository.
- CI nếu có.

### Skill cần dùng

- `push-code-skill`
- `testing-skill`
- `security-skill`
- `documentation-skill`
- `logging-skill`

### Điều kiện hoàn thành

- Test pass.
- Docs/logs đầy đủ.
- Code được push đúng quy trình.

## 7. Kế hoạch chia nhỏ milestone

### Milestone 1: Foundation

Gồm Phase 0, 1, 2.

Kết quả:

- Có skeleton dự án.
- Có setup script bản đầu.
- Có môi trường backend/frontend chạy được.

Thời gian: 2 - 4 ngày.

### Milestone 2: Backend Control Plane

Gồm Phase 3, một phần Phase 6 và Phase 7.

Kết quả:

- Backend quản lý service Riva/A2F.
- API status/start/stop/restart/logs hoạt động.
- Security boundary rõ.

Thời gian: 3 - 5 ngày.

### Milestone 3: AI Pipeline

Gồm Phase 4.

Kết quả:

- Text → Riva TTS → Audio → A2F chạy được.
- Có job state và job logs.

Thời gian: 3 - 5 ngày.

### Milestone 4: Dashboard

Gồm Phase 5 và phần còn lại Phase 6.

Kết quả:

- Dashboard quản lý pipeline, services, logs, setup/system.
- Realtime status/logs.

Thời gian: 4 - 7 ngày.

### Milestone 5: Hardening & Release

Gồm Phase 7, 8, 9, 10.

Kết quả:

- Security hardening.
- Test tổng thể.
- Documentation đầy đủ.
- Sẵn sàng push/release.

Thời gian: 4 - 7 ngày.

## 8. Ước lượng tổng thời gian

- Bản MVP chạy được local với service thật: 10 - 17 ngày.
- Bản ổn định có dashboard/logs/setup/docs/test đầy đủ: 16 - 28 ngày.

Ước lượng phụ thuộc mạnh vào:

- Riva/A2F đã cài sẵn hay chưa.
- Audio2Face chạy headless/automation được đến mức nào.
- Có GPU NVIDIA đúng cấu hình hay không.
- Yêu cầu preview face trong browser là realtime stream hay chỉ export/link file.

## 9. Rủi ro chính và cách xử lý

### Rủi ro 1: Audio2Face automation không ổn định

Cách xử lý:

- Phase 0 phải xác minh cách điều khiển A2F trước.
- Tách adapter A2F riêng để có thể đổi implementation.
- MVP có thể hỗ trợ export/result link trước, realtime stream sau.

### Rủi ro 2: Setup NVIDIA phụ thuộc license/tài khoản

Cách xử lý:

- `setup.sh` chỉ auto-cài phần hợp lệ.
- Với NGC/model/license, script hướng dẫn user đăng nhập/tải thủ công nếu cần.

### Rủi ro 3: Command injection từ service dashboard

Cách xử lý:

- Không nhận command từ frontend.
- Chỉ nhận service/action trong allowlist.
- Backend map action sang command cố định.

### Rủi ro 4: Logs leak secret hoặc đọc file ngoài ý muốn

Cách xử lý:

- Không cho truyền path.
- Redact secret trước khi ghi logs.
- Giới hạn service log key.

### Rủi ro 5: Pipeline job lâu hoặc treo

Cách xử lý:

- Job timeout.
- Job state rõ ràng.
- Cancel/retry ở backend.
- Logs theo job ID.

## 10. Quy trình bắt buộc khi triển khai từng phase

Với mỗi phase khi bắt đầu code phải làm đúng thứ tự:

1. Đọc skill liên quan.
2. Thực hiện phase.
3. Test phase theo `testing-skill`.
4. Ghi documentation phase theo `documentation-skill`.
5. Ghi log quá trình phase theo `logging-skill`.
6. Chỉ chuyển phase khi phase hiện tại pass testing.
7. Cuối dự án review security và push theo `push-code-skill`.

## 11. Câu hỏi cần chốt trước khi bắt đầu code

1. Dự án chạy trên Ubuntu bare metal, WSL2 hay Windows host?
2. GPU NVIDIA model nào, driver/CUDA hiện tại là gì?
3. Riva đã được cài/chạy thử chưa?
4. Audio2Face đã cài/chạy thử chưa, có cần headless không?
5. Output face mong muốn là realtime preview trong web, file export, hay điều khiển avatar trong app khác?
6. Dashboard chỉ dùng nội bộ local hay cần login/auth?
7. Muốn backend dùng Python FastAPI hay Node/NestJS?
8. Muốn frontend dùng React/Vite/Tailwind hay framework khác?
9. Có cần Docker Compose quản lý toàn bộ không?
10. Có repository remote để push chưa?

## 12. Đề xuất MVP đầu tiên

MVP nên làm theo thứ tự:

1. `setup.sh --check` kiểm tra GPU/Docker/Riva/A2F.
2. Backend FastAPI có `/health`, `/api/services`, `/api/services/{name}/status`.
3. Backend có API start/stop/restart Riva/A2F bằng allowlist.
4. Backend có log streaming từ files cố định.
5. Frontend dashboard hiển thị service status và logs realtime.
6. Tích hợp Riva TTS tạo audio từ text.
7. Tích hợp A2F nhận audio và tạo result.
8. Thêm job progress UI.
9. Hardening/test/docs.

MVP này giúp kiểm soát rủi ro NVIDIA service trước, sau đó mới mở rộng UI/UX và automation nâng cao.
