# Plan: Real NVIDIA Riva + Audio2Face + 3D Face Web + GitHub Release

## 1. Mục tiêu

Hoàn thiện dự án để chạy pipeline thật:

```text
Text input → NVIDIA Riva TTS thật → Audio file thật → NVIDIA Audio2Face thật → 3D face model/animation hiển thị trên web
```

Đồng thời chuẩn hóa repository GitHub:

```text
https://github.com/ambrouse/NVIDIARiva-Audio2Face-facespeed.git
```

## 2. Yêu cầu quan trọng

- Có plan rõ ràng trong `plans/`.
- Làm theo từng phase, mỗi phase phải có test, documentation và logging.
- Có script setup thật cho Riva/A2F trên NVIDIA Linux host.
- Có frontend hiển thị model 3D face trên web.
- Có CI/CD ban đầu.
- Có `.gitignore`, `.env.example`, README/version rõ ràng.
- Push code theo `push-code-skill` sau khi test pass.

## 3. Ràng buộc môi trường

Máy hiện tại đang là Windows. Test thật NVIDIA Riva server và Audio2Face cần tối thiểu:

- Linux host hoặc WSL2 GPU passthrough đã hoạt động.
- NVIDIA GPU tương thích.
- NVIDIA driver.
- Docker Engine.
- NVIDIA Container Toolkit.
- NVIDIA NGC CLI đã login.
- Quyền chấp nhận EULA/license của NVIDIA Riva và Audio2Face.
- Audio2Face app/service có API automation hoặc streaming endpoint.

Nếu thiếu môi trường NVIDIA host, phase test thật sẽ không thể pass thật trên máy hiện tại. Khi đó chỉ được đánh dấu là blocked, không claim pass thật.

## 4. Skill cần dùng

- `backend-skill`: backend pipeline, Riva/A2F adapters, service manager.
- `frontend-skill`: dashboard, 3D model UI.
- `frontend-design-skills`: bố cục, trạng thái, model viewer UX.
- `testing-skill`: unit/integration/smoke/E2E test.
- `documentation-skill`: setup guide, NVIDIA host guide, troubleshooting.
- `logging-skill`: log từng phase.
- `security-skill`: command allowlist, env/secrets, setup script safety.
- `push-code-skill`: gitignore, env, CI/CD, README, version, commit/push.
- `readme-style`: README chuẩn repo.

## 5. Phase 1: Chuẩn hóa repo và GitHub

### Mục tiêu

Biến thư mục hiện tại thành git repo đúng remote GitHub, có ignore/config/version/CI cơ bản.

### Việc cần làm

1. Kiểm tra git hiện tại.
2. `git init` nếu chưa có repo.
3. Add remote origin nếu chưa có:
   `https://github.com/ambrouse/NVIDIARiva-Audio2Face-facespeed.git`
4. Tạo `.gitignore`:
   - Python venv/cache.
   - Node modules/dist.
   - logs runtime.
   - outputs generated.
   - `.env`.
   - NVIDIA downloaded assets/models.
5. Tạo version file/package version rõ ràng.
6. Tạo GitHub Actions CI:
   - backend tests.
   - frontend tests/build.
   - setup script static tests.
7. Không push trước khi test pass.

### Thời gian dự kiến

0.5 ngày.

### Test

- `git status` sạch theo expected.
- CI yaml syntax hợp lệ.
- Local tests pass.

## 6. Phase 2: Setup installer thật cho NVIDIA host

### Mục tiêu

Mở rộng setup script để tải/cài/chạy Riva và kiểm tra Audio2Face thật trên NVIDIA host.

### Việc cần làm

1. Thêm mode:

```bash
./scripts/setup.sh --check-nvidia
./scripts/setup.sh --install-ngc
./scripts/setup.sh --install-riva
./scripts/setup.sh --start-riva
./scripts/setup.sh --check-riva
./scripts/setup.sh --check-a2f
./scripts/setup.sh --nvidia-full
```

2. Kiểm tra GPU/driver/docker/nvidia-container-toolkit.
3. Kiểm tra NGC CLI.
4. Nếu chưa login NGC thì báo user chạy login, không hardcode token.
5. Tải Riva Quick Start theo NGC CLI nếu môi trường đủ.
6. Start Riva server bằng script chính thức hoặc docker compose.
7. Kiểm tra Riva TTS gRPC bằng sample text.
8. Kiểm tra Audio2Face process/API.
9. Ghi logs vào `logs/setup/setup.log`.

### Thời gian dự kiến

1 - 2 ngày nếu có NVIDIA host.

### Test

- Static test script modes.
- Smoke test trên NVIDIA host:
  - `nvidia-smi` OK.
  - Docker GPU OK.
  - Riva server OK.
  - Riva TTS trả audio thật.
  - A2F API/process OK.

## 7. Phase 3: Backend smoke endpoints thật

### Mục tiêu

Tạo API kiểm tra Riva/A2F thật và pipeline smoke test.

### Việc cần làm

1. Endpoint:

```text
POST /api/integrations/riva/smoke
POST /api/integrations/a2f/smoke
POST /api/integrations/pipeline/smoke
```

2. Riva smoke sinh audio thật.
3. A2F smoke gửi audio sample thật.
4. Pipeline smoke tạo job thật.
5. Lưu artifact vào `outputs/smoke/`.
6. Không log secret/token.

### Thời gian dự kiến

1 ngày.

### Test

- Unit tests với mock.
- Integration tests với fake HTTP.
- Smoke thật trên NVIDIA host.

## 8. Phase 4: Web hiển thị model 3D face

### Mục tiêu

Frontend có viewport 3D hiển thị face model trên web.

### Hướng triển khai

Dùng Three.js + React Three Fiber hoặc Three.js thuần.

MVP:

- Load model GLB/GLTF từ `frontend/public/models/default-face.glb` hoặc URL kết quả từ backend.
- Hiển thị 3D viewer trong Pipeline page.
- Controls xoay/zoom.
- State loading/error.
- Khi pipeline xong, nhận `resultPath`/`modelUrl` và cập nhật viewer.

### Việc cần làm

1. Thêm dependency 3D viewer.
2. Tạo `FaceViewer` component.
3. Tạo placeholder GLB hợp lệ hoặc fallback primitive face nếu chưa có model file.
4. API backend trả `modelUrl` nếu A2F export ra model/animation.
5. UI hiện trạng thái đang chờ A2F.

### Thời gian dự kiến

1 - 2 ngày.

### Test

- Frontend test render viewer.
- Build pass.
- Manual browser check.
- Nếu có A2F artifact thật: viewer load artifact thật.

## 9. Phase 5: Documentation + README chuẩn

### Mục tiêu

Tài liệu đủ để người khác clone repo, setup NVIDIA host, chạy web và debug.

### Việc cần làm

1. Dùng `readme-style`.
2. README gồm:
   - overview.
   - architecture.
   - prerequisites.
   - setup Windows dev.
   - setup Linux NVIDIA host.
   - run backend/frontend.
   - Riva/A2F smoke test.
   - troubleshooting.
3. Docs riêng cho NVIDIA setup.
4. Docs riêng cho Audio2Face endpoint configuration.
5. Update phase reports/logs.

### Thời gian dự kiến

0.5 - 1 ngày.

### Test

- Commands trong docs phải khớp scripts thật.
- Không chứa secret/token.

## 10. Phase 6: Final test + push

### Mục tiêu

Test local + test thật NVIDIA nếu host sẵn sàng, sau đó commit và push.

### Việc cần làm

1. Backend tests.
2. Frontend tests/build.
3. Setup static tests.
4. NVIDIA smoke tests thật.
5. Security review command/env/logs.
6. Git status/diff/log.
7. Commit rõ thời gian và mô tả.
8. Push lên remote.

### Thời gian dự kiến

0.5 ngày nếu test thật pass.

### Điều kiện hoàn thành 100%

Chỉ được gọi là pass thật nếu:

- Riva server thật chạy và sinh audio thật.
- Audio2Face thật nhận audio và tạo animation/result thật.
- Web hiển thị model 3D face.
- Tests/build pass.
- Smoke logs/artifacts tồn tại.
- Code đã push lên GitHub.

## 11. Blockers cần xử lý ngay

1. Máy hiện tại có NVIDIA GPU và Linux/WSL2 GPU không?
2. Có quyền/tài khoản NVIDIA NGC không?
3. Audio2Face sẽ chạy dạng GUI app, headless service hay container?
4. Bạn có model face GLB/USDA/USD dùng cho web không, hay dùng placeholder trước?
5. Có cho phép mình `git init`, add remote, commit và push lên GitHub repo đã đưa không?

Nếu câu trả lời là chưa có NVIDIA host/NGC/A2F, mình vẫn có thể hoàn thiện code/setup/CI/3D viewer local, nhưng test thật sẽ bị blocked chứ không thể claim pass thật.
