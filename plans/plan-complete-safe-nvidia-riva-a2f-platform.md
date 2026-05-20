# Plan: Hoàn thiện FaceSpeed an toàn tài nguyên server

## 1. Mục tiêu

Hoàn thiện dự án FaceSpeed thành nền tảng web chạy pipeline:

```text
Text input -> NVIDIA Riva TTS -> WAV audio -> NVIDIA Audio2Face -> face animation/result -> web dashboard + 3D preview
```

Plan này ưu tiên **an toàn cho server đang chạy nhiều dự án quan trọng**. Mọi phase phải tránh gây crash, tranh chấp port, ngốn VRAM/RAM/CPU/GPU, kill nhầm process, hoặc tự động cài/chạy tác vụ nặng khi chưa có xác nhận.

Baseline kiểm tra ngày 2026-05-20 trên host hiện tại:

- CPU: 40 cores, load khoảng 6.x.
- RAM: 125GiB total, khoảng 97GiB available.
- Disk `/home`: ban đầu 372G total, 71G available, dùng 81%; sau cleanup unused Docker build cache/volumes còn 142G available, dùng 62%.
- GPU: NVIDIA RTX PRO 5000 Blackwell, 48,935MiB VRAM total, 34,982MiB used, 13,423MiB free, utilization khoảng 37%.
- GPU đang có process quan trọng: Python và VLLM; không được kill/stop/restart.
- Port đang bận trong nhóm phổ biến: `3000`, `3100`, `8001`, `8080`.
- Host từng xuất hiện dấu hiệu memory allocation pressure trong journal (`setroubleshootd out of memory`); trước phase nặng phải check thêm `CommitLimit` và `Committed_AS`, không chỉ `MemAvailable`.
- Port localhost đề xuất đã check trống theo dải liên tục:
  - Backend API: `127.0.0.1:8020`.
  - Frontend dev: `127.0.0.1:6210`.
  - Riva gRPC clone mới: `127.0.0.1:50100`.
  - Audio2Face API clone mới: `127.0.0.1:8040`.
- Docker baseline read-only: images 28.25GB, containers 515.8MB, local volumes 24.24GB với 22.34GB reclaimable, build cache 29.95GB reclaimable. Cleanup chỉ được làm với unused resources và phải hỏi/xác nhận trước lệnh xóa.
- NVIDIA/Riva/A2F cache/assets đặt trong project: `.cache/nvidia/`, không ghi secret vào repo/env tracked.


## 2. Nguyên tắc bắt buộc về an toàn server

1. Không tự động chạy job GPU/Riva/A2F thật nếu chưa có xác nhận rõ từ user.
2. Không tự động kill process theo tên rộng như `pkill`, `killall`, `pgrep -fa` rồi kill. Tất cả process hiện đang chạy được coi là quan trọng; chỉ thao tác process do dự án này tạo ra và có PID file/metadata rõ.
3. Không bind port nếu chưa check port đang dùng và xác định owner process.
4. Ưu tiên dải port localhost liên tục đã check trống: backend `8020`, frontend `6210`, Riva `50100`, A2F `8040`; nếu conflict thì dừng và hỏi user, không tự đổi port.
5. Riva và Audio2Face phải setup/clone mới từ đầu cho dự án này, chạy bằng container, không tái sử dụng hoặc can thiệp process/service đang chạy của dự án khác.
6. NVIDIA/Riva/A2F cache/assets lưu trong `.cache/nvidia/` của project; key/token chỉ dùng qua secure local secret hoặc interactive login, không ghi vào repo, plan, docs, logs, `.env.example`.
7. Sau khi key đã xuất hiện trong chat, sau setup phải nhắc user rotate NVIDIA key.
8. Chỉ cleanup Docker theo phạm vi stopped/unused resources sau khi show report và hỏi xác nhận; không xóa active containers/images/volumes.
9. Không tải/cài NVIDIA model/container lớn nếu chưa hỏi user xác nhận dung lượng, vị trí lưu và thời điểm chạy.
10. Luôn chừa tối thiểu 10% tài nguyên trống: VRAM, RAM, disk và memory commit headroom; nếu dưới ngưỡng thì dừng phase nặng và báo blocked.
11. Không chạy smoke test GPU nặng khi server đang bận hoặc chưa check GPU/VRAM/RAM/CPU/commit/disk.
12. Dashboard chỉ bind localhost; user sẽ test qua VS Code/Visual port forwarding.
13. Mọi service/container của project phải bind `127.0.0.1`, không bind `0.0.0.0`.
14. Không claim test NVIDIA thật pass nếu chưa chạy trên host có Riva/A2F thật và có artifact/log chứng minh.
15. Mọi lệnh setup cài hệ thống phải dry-run hoặc confirm trước nếu ảnh hưởng shared host.
16. Log không được chứa token, NGC API key, path nhạy cảm, hoặc env secret.
17. Tất cả phase phải có test, documentation và session log theo skill tương ứng.

## 3. Thông tin cần chốt với user trước khi chạy phần nặng

Thông tin đã chốt hoặc tự kiểm tra:

1. Hạ tầng/port do Claude tự kiểm tra bằng lệnh read-only trước mỗi phase nặng.
2. Tất cả process hiện đang chạy đều quan trọng; không kill/stop/restart process ngoài project.
3. Ưu tiên port localhost liên tục và ghi vào env:
   - Backend: `127.0.0.1:8020`.
   - Frontend: `127.0.0.1:6210`.
   - Riva clone mới: `127.0.0.1:50100`.
   - Audio2Face clone mới: `127.0.0.1:8040`.
4. Nếu port đề xuất bị chiếm khi triển khai thì dừng và hỏi user.
5. Riva và Audio2Face phải clone/setup mới từ đầu cho project này và chạy bằng container.
6. NVIDIA/Riva/A2F cache/assets lưu trong `.cache/nvidia/` của project.
7. NVIDIA API key đã được user cung cấp trong chat nhưng không được ghi vào repo/log/plan/env tracked; nên dùng bằng secret local hoặc lệnh interactive và rotate key sau khi setup nếu cần.
8. Docker cleanup chỉ được phép với unused resources sau khi report và xác nhận; không xóa active containers/images/volumes.
9. Luôn chừa tối thiểu 10% trống cho VRAM/RAM/disk/commit; không chạy phase nặng nếu không đạt ngưỡng.
10. Dashboard chỉ chạy localhost; user sẽ test bằng VS Code/Visual port forwarding.
11. Docker unused cleanup đã chạy theo xác nhận user: build cache về `0B`, disk `/home` còn khoảng 142G; các cleanup tiếp theo vẫn chỉ được làm với stopped/unused resources.
12. Nếu port đề xuất bị chiếm thì phải hỏi user, không tự đổi.

Vẫn cần hỏi trước khi chạy phần nặng:

1. Audio2Face container sẽ dùng image/tag chính xác nào nếu NVIDIA có nhiều lựa chọn.
2. Thời điểm nào được phép chạy download/setup/smoke test GPU thật.
3. Có cho phép chạy cleanup unused Docker cụ thể sau khi xem danh sách reclaim hay không.

## 4. Skill cần dùng

- `backend-skill`: backend API, job orchestration, Riva/A2F adapter, service manager, cleanup logs/temp, cấu trúc `src/routes`, `src/services`, `src/models`, `src/utils`.
- `frontend-skill`: React dashboard, API integration, UI state, component structure, accessibility, responsive behavior.
- `frontend-design-skills`: UX trạng thái tài nguyên, cảnh báo, preview 3D, loading/error/empty states.
- `testing-skill`: unit/integration/smoke/manual verification, test matrix, output evaluation, algorithm validation, regression/failure cases.
- `documentation-skill`: docs setup, vận hành, troubleshooting, tài nguyên, phase reports, cleanup docs sau mỗi task.
- `logging-skill`: log tiến độ từng phase và kết quả test, log ngắn có timestamp trong `logs/`.
- `security-skill`: command allowlist, process/port safety, secrets, CORS/auth, dependency/container/CI security gates.
- `push-code-skill`: CI/CD review, commit, versioning, README, push sau khi pass test.
- `readme-style`: README cuối cùng, badge, flow diagram, repo map, accuracy notes.

## 4.1 Vòng lặp triển khai bắt buộc cho từng phase

Mỗi phase phải chạy theo loop sau, không được nhảy phase nếu chưa đạt gate:

```text
Read related skills -> Inspect current code/state -> Implement smallest safe increment ->
Run targeted tests -> Evaluate output/algorithm/resource impact -> Update docs ->
Write session log -> Review diff/security -> Decide pass/blocked -> Next phase
```

Gate để qua phase:

1. Test liên quan pass hoặc có blocked note hợp lệ.
2. Output được đánh giá bằng artifact/log/screenshot/API response, không chỉ nhìn code.
3. Không tạo regressions rõ ràng ở backend/frontend/setup/CI.
4. Không vi phạm server safety: port/process/RAM/VRAM/disk/commit/Docker.
5. Documentation và session log của phase đã cập nhật.
6. Security/secret check không phát hiện token/key/log nhạy cảm trong repo.

Nếu fail:

1. Dừng phase.
2. Ghi lỗi, command, output chính và nguyên nhân nghi ngờ vào log task.
3. Sửa trong phạm vi nhỏ nhất.
4. Chạy lại test liên quan.
5. Chỉ tiếp tục khi pass hoặc user chấp nhận blocked.

## 4.2 Cấu trúc thư mục mục tiêu

```text
backend/
  src/
    config.py
    dependencies.py
    models/
    routes/
    services/
    utils/
  tests/
  pytest.ini
frontend/
  public/
  src/
    components/
    pages/
    services/
    styles/
    utils/
  package.json
scripts/
  setup.sh
configs/
  services.json
docs/
  nvidia-host-setup.md
  troubleshooting/
  phase-reports/
logs/
  setup/
  sessions/
  tests/
outputs/
  smoke/
plans/
.cache/
  nvidia/
    ngc/
    riva/
    audio2face/
.github/
  workflows/
    ci.yml
```

Rules:

- `logs/`, `outputs/`, `.cache/`, model assets, secrets, downloaded containers metadata phải gitignored.
- README chỉ mô tả đường dẫn quan trọng; docs chi tiết nằm trong `docs/`.
- Backend/frontend test nằm gần layer tương ứng, không trộn smoke artifacts vào tests.

## 4.3 Test matrix và đánh giá output

Test phải chứng minh hành vi sản phẩm, không chỉ coverage.

| Layer | Test | Output cần đánh giá |
|---|---|---|
| Backend config | Env uppercase/camelCase, port/origin/resource thresholds | `Settings` đúng giá trị, không đọc secret vào log |
| Backend API | `/health`, jobs, services, system | HTTP status/schema/state/error rõ |
| Riva adapter | Mock + fake Riva PCM | WAV hợp lệ: channel/sample width/sample rate/audio frames |
| A2F adapter | Fake HTTP success/error/timeout | Payload đúng, timeout/error không leak secret |
| Job algorithm | State machine Text -> Speech -> A2F -> completed/failed | State transitions đúng thứ tự, logs theo job, artifact path an toàn |
| Resource guard | Port/RAM/commit/disk/GPU checks | Block đúng khi dưới ngưỡng 10%, không start process |
| Docker workflow | Dry-run, label/name, localhost bind | Không đụng active container, commands có scope project |
| Frontend UI | Render pages, loading/error/empty states | Text trạng thái đúng, button disable đúng, không polling quá dày |
| 3D viewer | Fallback procedural face | Render nhẹ, không crash khi thiếu model artifact |
| E2E/manual | VS Code port forward backend/frontend | User flow tạo mock job, xem audio/result/error |
| Security | Secret scan, command/path allowlist, CORS localhost | Không hardcode key/token, không bind public |
| CI/CD | Backend tests, setup tests, frontend tests/build | CI pass, không cần GPU thật |

Test command dự kiến:

```bash
backend/.venv-linux/bin/python -m pytest backend tests
python -m pytest tests
npm --prefix frontend test
npm --prefix frontend run build
```

Nếu môi trường khác venv hiện tại, dùng Python/npm đã được preflight xác nhận. Không chạy GPU smoke trong CI mặc định.

## 4.4 Đánh giá thuật toán pipeline

Pipeline algorithm cần kiểm tra theo tiêu chí:

1. Input normalization: trim/collapse whitespace, reject empty text, giới hạn độ dài.
2. State order: `validating_text -> generating_speech -> speech_ready -> sending_to_a2f -> animating_face -> completed` hoặc `failed`.
3. Artifact contract:
   - Audio path nằm trong `outputs/audio` hoặc `outputs/smoke`.
   - Audio thật là WAV hợp lệ, sample rate theo config.
   - A2F result là JSON metadata hợp lệ hoặc error có message an toàn.
4. Failure behavior:
   - Riva missing/unreachable -> job failed, log rõ, không retry vô hạn.
   - A2F timeout/error -> job failed, không leak payload nhạy cảm.
   - Resource hard gate fail -> không tạo job GPU thật.
5. Performance/resource:
   - Không concurrent GPU jobs mặc định.
   - Timeout rõ.
   - Không polling frontend quá dày.

## 4.5 CI/CD và release gates

CI/CD phải duy trì non-GPU safe pipeline:

1. Backend unit/integration tests với mocks/fakes.
2. Setup script static tests và shell syntax checks nếu khả thi.
3. Frontend unit tests và production build.
4. Secret hygiene check: không có NVIDIA key/token trong tracked files.
5. Gitignore check cho `logs/`, `outputs/`, `.cache/`, `.env`, Playwright cache, NVIDIA assets.
6. Optional security scans nếu không gây tải lớn:
   - Python dependency audit nếu tool có sẵn.
   - npm audit/report nếu không thay đổi package ngoài ý muốn.
   - Dockerfile/container scan chỉ khi có Dockerfile/image project.
7. GPU smoke test là manual gated job, không chạy tự động trên shared server.

Release gate:

- Version file/package version rõ.
- README/docs cập nhật.
- Tests/build pass.
- Security review pass hoặc có accepted risk.
- NVIDIA thật pass hoặc ghi blocked rõ.
- Chỉ push khi user xác nhận theo `push-code-skill`.

## 4.6 README và documentation requirements

README cuối phải có:

1. Banner/title/badges theo `readme-style`.
2. Overview và Mermaid flow.
3. Quick start local mock dùng port `8020/6210`.
4. NVIDIA container setup safe workflow.
5. Resource safety checklist: port/process/RAM/VRAM/disk/commit/Docker.
6. VS Code port forwarding guide.
7. Repository map.
8. Test commands.
9. Accuracy notes: mock vs real NVIDIA, blocked conditions.
10. Secret warning: không commit NGC/NVIDIA key.

Docs trong `docs/` phải có timestamp, tóm tắt quan trọng, và cleanup docs sau mỗi task theo `documentation-skill`.

## 4.7 Logging requirements

Session/task logs nằm trong `logs/sessions/` hoặc `logs/tests/`, có timestamp, ngắn gọn, không chứa secret.

Mỗi phase log:

1. Phase name/time.
2. Commands chính đã chạy.
3. Test result summary.
4. Resource snapshot nếu phase liên quan setup/smoke.
5. Decision: pass/blocked/fail.
6. Next action.

Không commit logs; chỉ dùng làm artifact local, trừ khi user yêu cầu trích summary vào docs.

## 4.8 Security and safety review checklist

Trước khi báo hoàn thành hoặc push:

1. Không hardcode secret/token/key.
2. Không log secret/authorization/env nhạy cảm.
3. Không command injection từ service actions.
4. Không path traversal ở logs/output/artifact APIs.
5. CORS chỉ localhost nếu chưa auth.
6. Không bind service vào `0.0.0.0`.
7. Docker command có label/name project, không pattern rộng.
8. Cleanup chỉ stopped/unused và có xác nhận.
9. Dependency/package changes có lý do.
10. CI không chạy GPU/heavy jobs tự động.

## 4.9 Resource-safe implementation loop

Trước mọi thao tác có thể ảnh hưởng server:

```text
Check ports -> Check RAM/commit -> Check disk -> Check GPU/VRAM/process -> Check Docker -> Ask if risky -> Execute scoped command -> Verify -> Log summary
```

Không dùng sleep/poll loop dày. Frontend/backend polling mặc định phải >= 5s hoặc manual refresh cho system/service checks.


## 5. Phase 0: Audit hiện trạng và baseline an toàn

### Mục tiêu

Nắm trạng thái repo, thay đổi pending, test hiện tại và các rủi ro tài nguyên trước khi code tiếp.

### Việc cần làm

1. Đọc toàn bộ cấu trúc backend/frontend/scripts/docs hiện tại.
2. Ghi danh sách file đang modified/untracked.
3. Chạy test nhẹ, không GPU:
   - Backend unit tests.
   - Setup script static tests.
   - Frontend tests/build nếu không cần browser GPU.
4. Không chạy Riva/A2F thật ở phase này.
5. Kiểm tra `.env.example`, default ports, CORS origins.
6. Kiểm tra `.gitignore` tránh commit logs, outputs, model cache, local RPM/libs, Playwright cache.

### Thời gian dự kiến

0.5 ngày.

### Tài nguyên cần thiết

- Python env local.
- Node modules frontend.
- Không cần GPU.

### Test hoàn thành

- Có báo cáo baseline test.
- Không có command nặng được chạy.
- Không làm thay đổi service/process đang chạy.

## 6. Phase 1: Resource guardrails và system inspection API/script

### Mục tiêu

Thêm lớp kiểm tra tài nguyên trước mọi thao tác service/smoke test để tránh ảnh hưởng server.

### Việc cần làm

1. Mở rộng `scripts/setup.sh` với mode nhẹ:
   - `--check-ports`.
   - `--check-resources`.
   - `--check-gpu-light`.
   - `--dry-run-nvidia-full`.
2. `--check-ports` phải chỉ đọc thông tin, không kill process:
   - Check backend/frontend/Riva/A2F ports.
   - In owner PID/process nếu có.
   - Gợi ý đổi port thay vì chiếm port.
3. `--check-resources`:
   - RAM available.
   - Memory commit headroom: `CommitLimit - Committed_AS`.
   - Disk free cho outputs/cache/models.
   - CPU load hiện tại.
4. `--check-gpu-light`:
   - `nvidia-smi` query nhẹ nếu có.
   - VRAM total/used/free.
   - Process đang dùng GPU.
   - Không start container.
5. Backend thêm endpoint system status nhẹ nếu chưa đủ:
   - Port/config hiện tại.
   - Mode mock/nvidia.
   - Không expose secret.
6. Frontend system page hiển thị cảnh báo port/process/VRAM/RAM nếu backend có API.
7. Hard gate cho phase nặng:
   - Port target conflict -> blocked và hỏi user.
   - Free VRAM < 10% -> blocked.
   - Free disk < 10% -> blocked.
   - RAM available hoặc memory commit headroom < 10% -> blocked.
   - GPU đang quá bận hoặc có process lạ tăng mạnh -> blocked.
   - Docker daemon/GPU runtime lỗi -> blocked.
8. Cache/artifact layout bắt buộc:
   - `.cache/nvidia/ngc/` cho NGC metadata/cache nếu cần.
   - `.cache/nvidia/riva/` cho Riva assets.
   - `.cache/nvidia/audio2face/` cho Audio2Face assets.
   - `outputs/smoke/` cho smoke artifacts.
   - `logs/setup/` cho setup logs.
   - Tất cả cache/log/output phải nằm trong `.gitignore`.

### Thời gian dự kiến

1 ngày.

### Tài nguyên cần thiết

- Linux tools: `ss` hoặc `lsof` nếu có.
- `nvidia-smi` nếu host có GPU.

### Skill theo phase

- `backend-skill`.
- `frontend-skill`.
- `security-skill`.
- `testing-skill`.
- `documentation-skill`.
- `logging-skill`.

### Test hoàn thành

- Unit/static tests cho script modes.
- Test trên máy không có GPU phải không fail cứng.
- Script không kill/start bất kỳ process nào.

## 7. Phase 2: Backend hardening cho config, jobs và adapters

### Mục tiêu

Đảm bảo backend chạy an toàn ở mock/nvidia mode, không leak secret, không đọc/ghi path tùy ý, xử lý lỗi rõ.

### Việc cần làm

1. Hoàn thiện `Settings`:
   - Đọc env uppercase và camelCase.
   - Default port rõ.
   - Validate `pipelineMode` trong allowlist.
   - Validate allowed origins.
2. Job API:
   - Validate text length.
   - Validate language/voice/profile/outputMode bằng allowlist hoặc schema rõ.
   - Có timeout cho Riva/A2F nếu gọi thật.
   - Không block server quá lâu nếu job dài; cân nhắc background execution có giới hạn concurrency.
3. Output path:
   - Chỉ ghi trong `outputDir`.
   - Job ID không nhận từ user khi tạo file.
4. Riva adapter:
   - WAV output hợp lệ.
   - Lỗi thiếu package rõ.
   - Không retry vô hạn.
5. A2F adapter:
   - Config endpoint/path an toàn.
   - Timeout rõ.
   - Không gửi path ngoài output allowlist nếu không cần.
6. Service manager:
   - Chỉ thao tác service allowlist.
   - Không dùng shell command ghép từ input user.
   - Nếu cần start/stop thật, phải qua command cố định và có confirm/manual instruction.
7. Container metadata/rollback:
   - Tất cả container project phải có name prefix `facespeed-` và label `com.facespeed.project=NVIDIARiva-Audio2Face-facespeed`.
   - Stop/cleanup chỉ dựa trên label/name chính xác của project, không dùng pattern rộng.
   - Có thủ tục rollback dừng container project, giữ volume/cache mặc định, chỉ xóa volume/cache nếu user xác nhận.
8. Container resource limits:
   - Có memory limit và CPU limit nếu image hỗ trợ chạy ổn.
   - GPU access tối thiểu cần thiết; tránh `--gpus all` nếu có thể pin device cụ thể.
   - Restart policy không tự loop vô hạn; tránh restart storm gây tải server.

### Thời gian dự kiến

1 - 2 ngày.

### Tài nguyên cần thiết

- Python/FastAPI test env.
- Fake Riva/A2F clients cho integration tests.

### Skill theo phase

- `backend-skill`.
- `security-skill`.
- `testing-skill`.
- `documentation-skill`.
- `logging-skill`.

### Test hoàn thành

- Backend tests pass.
- Tests cho config/env.
- Tests cho Riva WAV.
- Tests cho A2F timeout/payload bằng fake HTTP.
- Security review nội bộ cho path/command/secret.

## 8. Phase 3: Frontend dashboard hoàn thiện và cảnh báo tài nguyên

### Mục tiêu

Dashboard hiển thị pipeline, services, logs, system checks và cảnh báo rủi ro tài nguyên rõ trước khi user chạy tác vụ nặng.

### Việc cần làm

1. Pipeline page:
   - Hiển thị job state, error, audio preview, result metadata.
   - Disable run nếu system báo thiếu backend/Riva/A2F trong nvidia mode.
   - Cảnh báo nếu đang ở mock mode.
2. Services page:
   - Status service.
   - Nút start/stop/restart phải hiển thị confirm và giải thích rủi ro.
   - Không spam polling quá dày; interval nhẹ, ví dụ 5-10s hoặc manual refresh.
3. System page:
   - Port status.
   - RAM/CPU/GPU/VRAM snapshot.
   - Disk free.
   - Suggested command dạng copy, không auto-run.
4. Logs page:
   - Tail giới hạn số dòng.
   - Pause/resume autoscroll.
   - Không poll quá dày.
5. 3D Face Viewer:
   - Procedural fallback nhẹ.
   - Không load asset nặng tự động nếu chưa có artifact.

### Thời gian dự kiến

1 - 2 ngày.

### Tài nguyên cần thiết

- Frontend dev server.
- Browser manual verification.
- Không cần GPU thật cho UI mock.

### Skill theo phase

- `frontend-skill`.
- `frontend-design-skills`.
- `testing-skill`.
- `documentation-skill`.
- `logging-skill`.

### Test hoàn thành

- Frontend unit tests pass.
- Production build pass.
- Manual browser check: pipeline mock, error state, system warnings, logs.
- Không tạo polling quá nặng.

## 9. Phase 4: NVIDIA setup workflow an toàn

### Mục tiêu

Chuẩn hóa quy trình setup Riva/A2F thật nhưng không tự động làm việc nặng hoặc phá shared server.

### Việc cần làm

1. `scripts/setup.sh --nvidia-full` phải có preflight:
   - Port free.
   - RAM/VRAM/disk/commit đủ.
   - GPU process hiện tại được hiển thị.
   - NGC login status nhưng không in token/key.
   - Docker GPU access.
   - Docker disk usage và reclaimable unused resources.
2. Với thao tác nặng, script phải yêu cầu xác nhận hoặc hướng dẫn user chạy thủ công:
   - Download Riva quickstart/model vào `.cache/nvidia/riva`.
   - Pull/start Riva container trên localhost port `50100`.
   - Xác minh Audio2Face container image/tag/API trước, không giả định endpoint `/api/process-audio` đúng khi chưa test.
   - Pull/start Audio2Face container trên localhost port `8040` sau khi xác minh image/tag/API.
3. Docker cleanup chỉ được phép với stopped/unused resources sau report và xác nhận; ưu tiên build cache/unused volumes, không đụng active containers đang chạy.
4. Không tự chọn port khác âm thầm; nếu conflict thì dừng và hỏi user.
5. Container phải bind localhost, có label/name project, có resource limits và rollback command rõ.
6. Không dùng sudo install nếu chưa explicit mode.
7. Logs setup ghi vào `logs/setup/setup.log`, nhưng không commit và không chứa secret.
8. Docs giải thích từng mode script và rủi ro tài nguyên.

### Thời gian dự kiến

1 - 2 ngày nếu chưa cần test NVIDIA thật; lâu hơn nếu phải setup thật.

### Tài nguyên cần thiết

- NVIDIA host.
- Docker/NVIDIA Container Toolkit.
- NGC CLI/login.
- Dung lượng disk cho Riva assets.

### Skill theo phase

- `security-skill`.
- `testing-skill`.
- `documentation-skill`.
- `logging-skill`.
- `backend-skill` nếu cần API liên quan.

### Test hoàn thành

- Static tests cho các mode setup.
- Dry-run trên server không thay đổi process.
- Nếu user cho phép: check nhẹ GPU/Docker/NGC.
- Không start container nếu chưa xác nhận.

## 10. Phase 5: Smoke tests thật có kiểm soát tài nguyên

### Mục tiêu

Chạy smoke test NVIDIA thật chỉ khi được phép và có guardrail rõ.

### Việc cần làm

1. Trước smoke test phải chụp baseline:
   - `nvidia-smi` VRAM/process.
   - RAM available và memory commit headroom.
   - CPU load.
   - Ports.
   - Disk free.
   - Docker container status theo label project.
2. User xác nhận giới hạn và thời điểm chạy.
3. Smoke Riva:
   - Text ngắn.
   - Một request.
   - Timeout ngắn/rõ.
   - Ghi WAV artifact nhỏ.
4. Smoke A2F:
   - Dùng WAV nhỏ.
   - Timeout rõ.
   - Không chạy batch.
5. Pipeline smoke:
   - Một job ngắn.
   - Không concurrent load.
6. Sau smoke test chụp lại resource snapshot.
7. Nếu resource vượt ngưỡng, dừng test và không retry tự động.

### Thời gian dự kiến

0.5 - 1 ngày nếu Riva/A2F đã sẵn sàng; có thể blocked nếu thiếu host/license/service.

### Tài nguyên cần thiết

- NVIDIA host được user cho phép chạy test.
- Riva server thật.
- Audio2Face endpoint thật.

### Skill theo phase

- `testing-skill`.
- `security-skill`.
- `logging-skill`.
- `documentation-skill`.

### Test hoàn thành

- Có smoke logs/artifacts.
- Có resource before/after.
- Không có crash hoặc ảnh hưởng process khác.
- Nếu blocked, ghi rõ blocked vì thiếu điều kiện nào.

## 11. Phase 6: Documentation, README và vận hành

### Mục tiêu

Tài liệu đủ để clone, chạy local mock, setup NVIDIA host an toàn, debug port/process/resource, và vận hành không ảnh hưởng server khác.

### Việc cần làm

1. README theo `readme-style`:
   - Overview.
   - Flow.
   - Quick start mock/local.
   - NVIDIA host setup.
   - Resource safety checklist.
   - Repository map.
   - Accuracy notes.
2. Docs NVIDIA host:
   - Required GPU/driver/Docker/NGC.
   - Port allocation.
   - VRAM/RAM/disk estimate.
   - Safe smoke test process.
3. Troubleshooting:
   - Port conflict.
   - Riva unavailable.
   - A2F unavailable.
   - GPU busy/low VRAM.
   - Disk low.
   - Memory commit/OOM pressure.
   - VS Code port forwarding disconnect/reconnect.
4. Manual localhost verification:
   - Backend `127.0.0.1:8020`.
   - Frontend `127.0.0.1:6210`.
   - User forward port bằng VS Code/Visual.
   - Không mở public/LAN nếu chưa thêm auth.
5. Phase report cho từng phase đã làm.
5. Session log theo `logging-skill`.

### Thời gian dự kiến

0.5 - 1 ngày.

### Tài nguyên cần thiết

- Kết quả test phase trước.
- Resource/smoke notes nếu có.

### Skill theo phase

- `documentation-skill`.
- `logging-skill`.
- `readme-style`.

### Test hoàn thành

- Commands trong docs khớp script thật.
- Không chứa secret.
- Accuracy notes không claim quá mức.

## 12. Phase 7: Final review, tests, security review và push

### Mục tiêu

Đưa repo về trạng thái sẵn sàng push/release sau khi pass test phù hợp với môi trường.

### Việc cần làm

1. Review diff toàn bộ.
2. Chạy test nhẹ bắt buộc:
   - Backend tests.
   - Setup tests.
   - Frontend tests/build.
3. Chạy security review pending changes.
4. Nếu có quyền và điều kiện, chạy smoke NVIDIA thật; nếu không thì ghi blocked.
5. Kiểm tra git status không chứa secret/log/output/model/cache.
6. Commit theo quy tắc.
7. Push theo `push-code-skill` nếu user xác nhận.

### Thời gian dự kiến

0.5 ngày.

### Tài nguyên cần thiết

- Local dev env.
- Git remote access nếu push.

### Skill theo phase

- `testing-skill`.
- `security-skill`.
- `push-code-skill`.
- `documentation-skill`.
- `logging-skill`.

### Test hoàn thành

- Tests/build pass hoặc có blocked note hợp lệ cho NVIDIA thật.
- Không có secret/log/output trong commit.
- Push chỉ thực hiện khi user đồng ý.

## 13. Checklist không được làm nếu chưa hỏi lại user

- Start/stop/restart Riva hoặc Audio2Face thật.
- Start Docker container GPU.
- Download model/container NVIDIA lớn.
- Cài package hệ thống bằng sudo.
- Kill process hoặc free port.
- Xóa Docker resources ngoài phạm vi stopped/unused đã được user xác nhận.
- Xóa active container/image/volume hoặc volume/cache project khi chưa xác nhận rõ.
- Chạy benchmark/load test/concurrent jobs.
- Chạy smoke test GPU khi GPU đang bận.
- Bind service vào `0.0.0.0` hoặc mở dashboard ra network ngoài localhost.
- Push code lên remote.

## 14. Definition of Done

Dự án chỉ được coi là hoàn thiện khi:

1. Backend mock mode chạy ổn và tests pass.
2. Frontend dashboard build pass và manual check pass.
3. Setup script có preflight an toàn cho port/process/RAM/CPU/GPU/VRAM/disk/commit/Docker.
4. Container Riva/A2F có localhost bind, project label/name, resource limits và rollback procedure.
5. Documentation có hướng dẫn setup local và NVIDIA host an toàn.
6. Security review không còn vấn đề nghiêm trọng.
7. Không commit secret/log/output/model/cache.
8. Nếu có NVIDIA host được phép dùng: Riva/A2F smoke test thật pass với artifact/log/resource snapshot.
9. Nếu chưa có NVIDIA host/quyền chạy: ghi rõ blocked, không claim pass thật.
10. Code được push lên remote chỉ sau khi user xác nhận.

## 15. Câu hỏi còn cần user trả lời trước phase NVIDIA thật

Những điểm đã chốt: Claude tự check hạ tầng/port, mọi process hiện tại đều quan trọng, dùng localhost only, dùng dải port `8020/6210/50100/8040`, Riva/A2F setup mới từ đầu, chừa tối thiểu 10% tài nguyên.

Còn cần chốt trước khi download/setup/smoke test NVIDIA thật:

1. Audio2Face container image/tag chính xác là gì nếu NVIDIA có nhiều lựa chọn.
2. Thời điểm nào được phép chạy download/setup/smoke test GPU thật để giảm rủi ro ảnh hưởng các project đang chạy.
3. Có ngưỡng cụ thể nào thấp hơn mặc định 10% cho VRAM/RAM/disk/commit mà user muốn áp dụng không? Nếu không, dùng mặc định 10%.
4. Có xác nhận chạy cleanup unused Docker sau khi xem report chi tiết không; cleanup mặc định chỉ được phép với unused resources.
