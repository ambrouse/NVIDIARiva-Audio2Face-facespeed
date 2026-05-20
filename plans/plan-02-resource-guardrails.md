# Plan 02: Resource Guardrails

## Mục tiêu

Thêm guardrails để mọi thao tác setup/smoke/container đều check port, process, RAM, memory commit, disk, GPU/VRAM và Docker trước khi chạy.

## Skill phải đọc trước khi làm

- `backend-skill`
- `security-skill`
- `testing-skill`
- `documentation-skill`
- `logging-skill`

## Phạm vi

Làm:

1. Mở rộng `scripts/setup.sh` bằng modes read-only/lightweight.
2. Thêm env/resource thresholds vào config nếu cần.
3. Thêm tests static cho setup script.
4. Thêm docs ngắn về preflight nếu thay đổi user-facing behavior.

Không làm:

- Không start container GPU.
- Không chạy Docker prune nếu chưa được yêu cầu riêng.
- Không đổi port nếu conflict; hỏi user.

## Modes cần có trong setup script

```bash
./scripts/setup.sh --check-ports
./scripts/setup.sh --check-resources
./scripts/setup.sh --check-gpu-light
./scripts/setup.sh --check-docker-space
./scripts/setup.sh --dry-run-nvidia-full
```

## Hard gates

Phase nặng phải blocked nếu:

1. Target port conflict.
2. Free VRAM < `GPU_MIN_FREE_VRAM_PERCENT` hoặc default 10%.
3. Disk free < `DISK_MIN_FREE_PERCENT` hoặc default 10%.
4. RAM available < `RAM_MIN_FREE_PERCENT` hoặc default 10%.
5. Memory commit headroom `(CommitLimit - Committed_AS)` < 10%.
6. Docker daemon unavailable hoặc NVIDIA runtime lỗi.
7. GPU process list thay đổi bất thường hoặc GPU quá bận.

## Các bước chi tiết

### Step 1: Port guard

Target ports:

- Backend `8020`
- Frontend `6210`
- Riva `50100`
- A2F `8040`

Implementation rules:

- Dùng `ss` hoặc fallback `lsof` nếu có.
- Chỉ report owner PID/process.
- Không kill/free port.
- Nếu conflict: exit non-zero hoặc mark blocked, message yêu cầu user chọn port.

PASS nếu:

- Test chứng minh script detect string/mode đúng.
- Manual read-only output không kill process.

### Step 2: RAM/commit/disk guard

Check:

- `MemAvailable`
- `CommitLimit`
- `Committed_AS`
- `SwapFree`
- `df -P` cho project/cache path

PASS nếu:

- Output có percent/headroom rõ.
- Dưới threshold thì script báo BLOCKED, không tiếp tục.

### Step 3: GPU guard

Check nhẹ:

- GPU name
- VRAM total/used/free
- GPU utilization
- Process list từ `nvidia-smi pmon` hoặc query compute apps nếu available

PASS nếu:

- Máy không có GPU không crash script; báo unavailable.
- Có GPU thì output đủ baseline.

### Step 4: Docker guard

Check:

- `docker system df`
- active containers
- project labels if any

PASS nếu:

- Không xóa gì.
- Report rõ build cache/volumes/images/containers.

### Step 5: Tests

Cập nhật `tests/test_setup_script.py` hoặc test tương ứng.

Test cases:

1. Script có các mode mới.
2. Không có `pkill`, `killall`, `fuser -k` trong setup script.
3. Port conflict behavior không có kill.
4. Docker cleanup command không chạy trong check modes.
5. Threshold env names tồn tại.

## Đánh giá output

PASS khi:

- `python -m pytest tests` pass.
- Script modes chạy read-only trên server và không đổi process/container.
- Log ghi resource snapshot.

ASK khi:

- Cần cài tool mới như `lsof`, `shellcheck`, hoặc cần sudo.
- Port conflict target.

REDO khi:

- Script mode có side effect.
- Test không bắt được command nguy hiểm.
- Output thiếu threshold/owner process.

## Docs/logs

- Ghi log phase vào `logs/sessions/facespeed-safe-completion.md`.
- Nếu script behavior đổi, cập nhật `docs/nvidia-host-setup.md` hoặc docs troubleshooting.

## Close Comment

Status: PASS
Closed at: 2026-05-20 16:12
Evidence:
- Added read-only guardrail modes: `--check-ports`, `--check-resources`, `--check-gpu-light`, `--check-docker-space`, `--dry-run-nvidia-full`.
- `backend/.venv-linux/bin/python -m pytest tests`: 7 passed.
- `backend/.venv-linux/bin/python -m pytest backend tests`: 17 passed.
- `bash -n scripts/setup.sh`: PASS.
- Dry-run NVIDIA preflight reported ports/resources/GPU/Docker and did not download, start containers, cleanup Docker or kill processes.
- Docs updated in `docs/nvidia-host-setup.md`.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 02 - Resource Guardrails`
Next plan: `plans/plan-03-backend-hardening.md`
Notes:
- Commit headroom is close to the 10% threshold; re-run `bash scripts/setup.sh --check-resources` before heavy work.
- Direct `./scripts/setup.sh` is not executable in this checkout; use `bash scripts/setup.sh ...` unless file mode is intentionally changed later.
