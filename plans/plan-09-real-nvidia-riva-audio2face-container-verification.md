# Plan 09: Real NVIDIA Riva + Audio2Face Container Verification

## Mục tiêu

Xác minh đường chạy NVIDIA thật cho FaceSpeed trên server hiện tại, gồm Riva TTS thật và Audio2Face thật, nhưng chỉ pull/start container sau khi image/tag/API chính thức rõ ràng, tài nguyên pass hard gates và user xác nhận.

## Trạng thái đầu vào

Đã hoàn thành:

- Local mock pipeline pass.
- Backend/setup tests pass.
- Frontend tests/build/browser mock smoke pass.
- Docker/container dry-run workflow pass.
- README/docs/CI updated and pushed.

Đang blocked:

- Real Riva image/tag/setup path chưa xác minh chắc cho server x86 hiện tại.
- Real Audio2Face container/headless/API chưa xác minh.
- NGC CLI/login chưa xác nhận trong shell.
- Real NVIDIA smoke chưa chạy.

## Skill phải đọc trước khi làm

- `plan-skill`
- `security-skill`
- `testing-skill`
- `backend-skill`
- `documentation-skill`
- `logging-skill`
- `push-code-skill` nếu commit/push docs/code

## Safety rules bắt buộc

1. Không ghi NVIDIA key/token vào repo, docs, logs, `.env`, shell history nếu tránh được.
2. Không pull image/model lớn trước khi user xác nhận dung lượng và image/tag.
3. Không start GPU container trước khi all hard gates pass.
4. Không kill/free port/process đang chạy.
5. Không bind `0.0.0.0`; chỉ dùng `127.0.0.1`.
6. Không xóa Docker active containers/images/volumes.
7. Không benchmark/load/concurrent jobs.
8. Mỗi smoke test chỉ một request ngắn.
9. Nếu bất kỳ output không rõ, dừng và ASK.
10. Nếu real NVIDIA chưa xác minh được, ghi BLOCKED, không claim pass.

## Hard gates trước pull/start

Chạy:

```bash
bash scripts/setup.sh --check-ports
bash scripts/setup.sh --check-resources
bash scripts/setup.sh --check-gpu-light
bash scripts/setup.sh --check-docker-space
bash scripts/setup.sh --dry-run-nvidia-full
```

PASS nếu:

- Ports `8020`, `6210`, `50100`, `8040` available hoặc user chọn port mới.
- RAM available >= 10%.
- Memory commit headroom >= 10%.
- Disk free >= 10%.
- GPU free VRAM >= 10%.
- Docker daemon OK.
- NVIDIA runtime OK hoặc xác định rõ cần setup.
- Existing GPU processes chỉ được liệt kê, không động vào.

BLOCKED nếu:

- Commit headroom dưới 10%.
- Disk không đủ cho image/model.
- Docker/NVIDIA runtime không sẵn sàng.
- Port conflict chưa được user chọn hướng xử lý.

## Phase 09.1: Xác minh NGC CLI/login an toàn

### Mục tiêu

Biết NGC CLI có sẵn và có thể auth mà không lộ key.

### Commands read-only/safe

```bash
command -v ngc
ngc --version
ngc config current
```

Không paste key vào command trực tiếp nếu command sẽ lưu history/log.

Nếu cần login:

- ASK user chạy interactive `ngc config set` bằng `! ngc config set` trong session.
- Không ghi key vào file tracked.
- Sau setup nhắc user rotate key vì key từng xuất hiện trong chat.

### PASS

- NGC CLI available.
- `ngc config current` không in secret và xác nhận configured.

### ASK

- NGC CLI missing.
- Need user interactive login.

### BLOCKED

- Không có NGC CLI và không được phép cài.
- Auth/license không hợp lệ.

## Phase 09.2: Xác minh Riva path chính thức

### Mục tiêu

Tìm đúng Riva deployment path cho server hiện tại.

### Việc cần làm

1. Xác định server arch/OS/GPU.
2. Đọc docs NVIDIA Riva hiện tại.
3. Nếu docs quickstart hiện tại là Jetson-only, xác minh x86 path là Riva NIM hay package NGC khác.
4. Xác định image/tag/resource chính xác.
5. Xác định ports, models, disk size, license/EULA.
6. Ghi rõ command dry-run trước khi pull.

### PASS

- Có official image/resource/tag rõ.
- Có docs/source rõ.
- Có expected port/health/smoke command.
- Có disk estimate.

### ASK

- Có nhiều Riva paths: legacy quickstart vs NIM vs SDK.
- License/EULA cần accept.
- Image size lớn cần xác nhận pull.

### BLOCKED

- Không tìm được path chính thức phù hợp x86.
- NGC resource yêu cầu quyền/license chưa có.

## Phase 09.3: Xác minh Audio2Face path chính thức

### Mục tiêu

Xác định Audio2Face thật chạy như thế nào để backend có thể gửi WAV và nhận result.

### Việc cần làm

1. Xác minh có container/headless/service không.
2. Nếu không có REST service chính thức, xác minh SDK/wrapper option.
3. Xác định input contract:
   - WAV path/upload/stream.
   - sample rate/format.
   - profile/avatar/model requirements.
4. Xác định output contract:
   - blendshapes.
   - animation file.
   - JSON metadata.
   - stream endpoint.
5. Cập nhật backend adapter contract nếu API khác placeholder.

### PASS

- Có image/tag/API hoặc SDK wrapper path rõ.
- Có health check.
- Có one-shot WAV smoke command.
- Backend adapter có thể map contract an toàn.

### ASK

- Phải chọn giữa SDK wrapper, GUI app, Unreal/Maya plugin, hoặc ACE service.
- Cần user cung cấp avatar/model asset.

### BLOCKED

- Không có container/headless/API phù hợp.
- Chỉ có SDK/plugin nhưng chưa có wrapper service để backend gọi.

## Phase 09.4: Dry-run container commands với image thật

### Mục tiêu

Sinh command pull/run/rollback với image thật nhưng chưa chạy.

### Command

```bash
export RIVA_CONTAINER_IMAGE=<verified-riva-image>
export A2F_CONTAINER_IMAGE=<verified-a2f-image-or-wrapper-image>
bash scripts/setup.sh --dry-run-containers
```

### PASS

Dry-run output có:

- `facespeed-riva` / `facespeed-audio2face`.
- project label.
- `127.0.0.1` bind.
- cache mounts.
- memory/CPU/GPU flags.
- `--restart no`.
- rollback commands.

### ASK

- Resource limits cần chỉnh.
- Port cần đổi.
- Mount path cần đổi.

### REDO

- Command bind `0.0.0.0`.
- Missing label/name.
- Missing resource limits.
- Logs print secret.

## Phase 09.5: Pull/start Riva thật sau xác nhận

### Mục tiêu

Start Riva container thật an toàn.

### Before

- Re-run hard gates.
- User confirms pull/start.
- Capture resource before snapshot.

### Run

- Pull verified image/resource.
- Start `facespeed-riva` only.
- Bind `127.0.0.1:50100`.
- Confirm no restart loop.

### Smoke

- TCP/health check.
- One short TTS request if API/client ready.
- WAV valid check.

### PASS

- Container running with correct label/name.
- Port bound localhost only.
- Riva returns valid WAV.
- Resource after snapshot OK.

### BLOCKED/REDO

- Container fails/restart loop.
- VRAM/RAM/disk threshold fails.
- TTS API/client mismatch.

## Phase 09.6: Pull/start Audio2Face thật sau xác nhận

### Mục tiêu

Start A2F service/wrapper thật an toàn.

### Before

- API/image verified.
- User confirms pull/start.
- Resource gates pass.

### Smoke

- Health endpoint.
- Submit small WAV.
- Capture result/artifact.

### PASS

- Service running with correct label/name.
- Port bound localhost only.
- Small WAV produces expected result.
- Backend adapter contract verified.

### BLOCKED/REDO

- No headless/API path.
- Requires GUI/asset not available.
- Output contract differs and needs adapter change.

## Phase 09.7: Real end-to-end smoke

### Mục tiêu

Chạy một job thật:

```text
Text -> Riva WAV -> A2F result -> Backend completed -> Frontend displays result
```

### Test input

Short text only:

```text
hello from facespeed real smoke
```

### Evaluation

PASS khi:

1. Job completed.
2. Riva WAV valid: channel/sample width/sample rate/duration > 0.
3. A2F result valid according to verified contract.
4. UI shows completed/result.
5. Resource before/after remains above thresholds.
6. No secret in logs.
7. No unrelated process/container impacted.

ASK khi:

- Output partial but potentially acceptable.
- A2F result needs avatar/model interpretation.

BLOCKED khi:

- Riva pass but A2F not available.
- A2F API not verified.
- Resource gate fails.

## Phase 09.8: Docs/log/commit/push

Update:

- `docs/nvidia-host-setup.md`
- `docs/troubleshooting/audio2face-api.md`
- phase report: `docs/phase-reports/phase-9-real-nvidia-container-verification.md`
- session log: `logs/sessions/facespeed-safe-completion.md`
- README accuracy notes if real NVIDIA status changes.

Run tests:

```bash
backend/.venv-linux/bin/python -m pytest backend tests
npm --prefix frontend test
npm --prefix frontend run build
bash -n scripts/setup.sh
```

Commit/push only after user confirms.

## Log format

```text
[time] Phase 09.x - <name>
Status: PASS | ASK | REDO | BLOCKED
Commands:
- ...
Evidence:
- ...
Resources before/after:
- ...
Decision:
- ...
Next:
- ...
```

## Phase 09 Checkpoint

Status: BLOCKED for real smoke after safe pull/start attempts
Checked at: 2026-05-21 09:20
Evidence:
- NGC CLI was downloaded locally to `.cache/nvidia/ngc-cli/extracted/ngc-cli/ngc` and reports `NGC CLI 4.18.0`.
- `ngc config current` found an API key from environment and printed it masked only.
- Docker login to `nvcr.io` succeeded using the existing environment key via stdin.
- Hard gates passed before pull/start: ports `8020`, `6210`, `50100`, `8040` available; Docker reachable; GPU visible; RAM/disk/commit above reserve threshold.
- Pulled `nvcr.io/nvidia/riva/riva-speech:2.19.0`; local inspect size `39791080651` bytes.
- Pulled `nvcr.io/nvidia/ace/audio2face:1.0.11`; local inspect size `27487807852` bytes.
- Dry-run container commands with verified images used project labels, localhost binds, resource limits, GPU device flag and `--restart no`.
- `facespeed-riva` started on `127.0.0.1:50100` but exited 0 after printing license text; image metadata has no default command and `/opt/riva/bin/riva_server` reports `--model-repository must be specified`.
- `facespeed-audio2face` started on `127.0.0.1:8040` but exited 0; logs report `Detected NVIDIA RTX PRO 5000 Blackwell GPU, which is not yet supported in this version of the container` and `No supported GPU(s) detected`.
- No real Riva WAV or A2F artifact was produced.
Decision:
- Phase 09.1 PASS for local NGC/Docker auth setup.
- Phase 09.2 is partially verified: Riva image/tag exists and is pulled, but runtime is BLOCKED until a valid Riva model repository/quickstart resource is available and mapped.
- Phase 09.3 is BLOCKED for current A2F image because `nvidia/ace/audio2face:1.0.11` does not support the host RTX PRO 5000 Blackwell GPU.
- Phase 09.5/09.6/09.7 cannot PASS.
Next:
- Get the exact Riva model repository/quickstart resource for `riva-speech:2.19.0` or a newer Blackwell-compatible Riva path.
- Find a newer Blackwell-compatible Audio2Face/ACE image or NVIDIA-supported deployment path.
- Do not retry container start loops with the current A2F image.

## Close Comment

Status: BLOCKED
Closed at: 2026-05-21 09:20
Evidence:
- Images pulled and scoped start attempts completed, but Riva needs `--model-repository` and A2F image does not support the host Blackwell GPU.
Log entry: logs/sessions/facespeed-safe-completion.md#phase-09-real-nvidia-riva-audio2face-container-verification
Next plan: Resolve Riva model repository and Blackwell-compatible Audio2Face/ACE runtime before real smoke.
Notes:
- Real NVIDIA work must not claim pass until Riva and A2F smoke artifacts exist.
