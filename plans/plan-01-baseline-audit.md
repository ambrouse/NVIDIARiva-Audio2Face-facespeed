# Plan 01: Baseline Audit

## Mục tiêu

Audit repo và hạ tầng hiện tại bằng thao tác read-only/lightweight để biết chính xác đang ở đâu trước khi implement tiếp.

## Skill phải đọc trước khi làm

- `backend-skill`
- `frontend-skill`
- `testing-skill`
- `security-skill`
- `logging-skill`

## Phạm vi

Làm:

1. Kiểm tra git status/diff.
2. Kiểm tra cấu trúc thư mục hiện tại so với target structure.
3. Kiểm tra `.env.example`, `.gitignore`, CI workflow, README/docs.
4. Chạy test nhẹ không GPU nếu preflight OK.
5. Ghi baseline resource snapshot.

Không làm:

- Không start/stop/kill process.
- Không start Docker GPU container.
- Không download model/container NVIDIA.
- Không cleanup Docker thêm nếu chưa hỏi.
- Không push/commit.

## Các bước chi tiết

### Step 1: Repo state audit

Commands dự kiến:

```bash
git status --short
git diff --stat
find . -maxdepth 3 -type f | sort
```

Đánh giá output:

- Biết chính xác file modified/untracked.
- Không có secret/token trong diff.
- Không có logs/outputs/cache vô tình tracked.

PASS nếu:

- Repo state được ghi vào log.
- Nếu thấy secret/cache/log tracked thì tạo REDO task để sửa `.gitignore`/remove khỏi staging.

ASK nếu:

- Có file lạ không rõ có phải user work-in-progress không.

### Step 2: Structure audit

Kiểm tra target folders:

```text
backend/src/{models,routes,services,utils}
backend/tests
frontend/src/{components,pages,services,styles,utils}
scripts
configs
docs/phase-reports
logs/sessions
outputs/smoke
.cache/nvidia
.github/workflows
```

PASS nếu:

- Thiếu folder nào thì ghi rõ cần tạo ở phase phù hợp.
- Không tạo folder mới nếu chưa cần, trừ `logs/sessions` đã được dùng cho plan tracking.

### Step 3: Resource baseline

Read-only commands:

```bash
free -h
cat /proc/meminfo | grep -E 'MemAvailable|CommitLimit|Committed_AS|SwapFree'
df -h . /home
ss -ltnp | grep target ports
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu --format=csv
docker system df
```

PASS nếu:

- Resource snapshot ghi vào log.
- Nếu dưới threshold 10%, đánh dấu BLOCKED cho phase nặng.

ASK nếu:

- Target ports conflict.

### Step 4: Lightweight test audit

Test dự kiến:

```bash
python -m pytest tests
backend/.venv-linux/bin/python -m pytest backend tests
npm --prefix frontend test
npm --prefix frontend run build
```

Chỉ chạy command phù hợp với env hiện tại, không tự install package nếu thiếu mà chưa hỏi.

PASS nếu:

- Test pass, hoặc thiếu dependency được ghi BLOCKED/REDO rõ.
- Không claim frontend manual pass nếu chưa chạy browser.

REDO nếu:

- Test fail do code hiện tại và lỗi nằm trong scope fix an toàn.

ASK nếu:

- Cần install dependency hoặc thay đổi lockfile.

## Output cần tạo

- Log entry trong `logs/sessions/facespeed-safe-completion.md`.
- Nếu cần, cập nhật master tracker status.
- Không cần docs dài ở phase này, chỉ log audit.

## Close Comment

Status: PASS with environment note
Closed at: 2026-05-20 16:07
Evidence:
- Backend/root tests via project venv: `14 passed in 0.42s`.
- Frontend tests: `1 passed`.
- Frontend production build: PASS with Vite chunk-size warning for FaceViewer bundle.
- System Python `python -m pytest tests` blocked by missing pytest; project venv pytest path passed, so this is environment-specific rather than code failure.
- Resource snapshot captured: `/home` 142G available, target ports `8020/6210/50100/8040` free, GPU has active important Python/VLLM processes and about 13.4GiB VRAM free.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 01 - Baseline Audit`
Next plan: `plans/plan-02-resource-guardrails.md`
Notes:
- Future backend/root pytest should prefer `backend/.venv-linux/bin/python` unless installing pytest into system Python is explicitly approved.
- Commit headroom is above threshold but relatively narrow; re-check before heavy Docker/GPU work.
