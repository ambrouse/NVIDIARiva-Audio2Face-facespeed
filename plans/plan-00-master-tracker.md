# Plan 00: Master Tracker - FaceSpeed Safe Completion

## Mục tiêu

Theo dõi toàn bộ quá trình hoàn thiện FaceSpeed theo nhiều plan nhỏ, mỗi plan có pass gate, ask gate, redo gate, log handoff và comment đóng plan.

## Quy tắc làm việc chung

Mỗi plan phase phải đi theo loop:

```text
Read required skills -> Check current state -> Implement scoped work -> Run tests -> Evaluate output -> Update docs -> Write logs -> Close plan comment -> Move next
```

Không được chuyển phase nếu chưa có một trong hai trạng thái:

- `PASS`: đủ tiêu chí pass và log đã ghi.
- `BLOCKED`: có lý do rõ, cần user/hạ tầng/secret/NVIDIA/service.

Không dùng trạng thái mơ hồ như “gần xong”.

## Cách đánh giá trạng thái

### PASS khi

1. Tất cả test bắt buộc của phase pass.
2. Output được kiểm chứng bằng artifact cụ thể: command output, API response, UI screenshot/manual checklist, file generated, hoặc resource snapshot.
3. Không vi phạm safety: port/process/RAM/VRAM/disk/commit/Docker.
4. Không có secret trong repo/log/docs.
5. Docs/log phase đã cập nhật.
6. Có comment đóng plan trong file plan phase.

### ASK khi

1. Cần quyết định có rủi ro: port conflict, cleanup destructive, start container GPU, download model lớn, sudo/system install, push remote.
2. Có nhiều hướng triển khai hợp lý: Audio2Face image/API, resource limit, cache location, public vs localhost.
3. Test thật có thể ảnh hưởng server.
4. Output/failure không rõ có được chấp nhận hay không.

### REDO khi

1. Test fail do code/logic.
2. Output không khớp contract.
3. Phase tạo regression ở phần khác.
4. Security/resource guardrail bị vi phạm.
5. Docs/log thiếu thông tin để tiếp tục.

### BLOCKED khi

1. Thiếu NVIDIA login/image/license/service.
2. Resource dưới threshold 10%.
3. Port conflict mà user chưa chọn port mới.
4. Docker/GPU runtime lỗi ngoài phạm vi sửa an toàn.
5. User chưa xác nhận thao tác risky.

## Danh sách plan phase

| Phase | File | Mục tiêu | Status |
|---|---|---|---|
| 0 | `plans/plan-01-baseline-audit.md` | Audit repo, baseline resource, test nhẹ | PASS |
| 1 | `plans/plan-02-resource-guardrails.md` | Port/RAM/commit/disk/GPU/Docker guardrails | PASS |
| 2 | `plans/plan-03-backend-hardening.md` | Backend config/job/adapters/service safety | PASS |
| 3 | `plans/plan-04-frontend-dashboard.md` | Dashboard, resource UI, pipeline UX | PASS |
| 4 | `plans/plan-05-nvidia-container-setup.md` | Riva/A2F container setup workflow | PASS dry-run / BLOCKED real start |
| 5 | `plans/plan-06-smoke-output-evaluation.md` | Smoke tests, output/algorithm evaluation | PASS mock / BLOCKED real NVIDIA |
| 6 | `plans/plan-07-docs-readme-cicd.md` | README/docs/CI/CD/version/release gates | PASS |
| 7 | `plans/plan-08-final-review-push.md` | Final review, security, push if approved | PASS + pushed |
| 8 | `plans/plan-09-real-nvidia-riva-audio2face-container-verification.md` | Verify real Riva/A2F image/API and gated smoke | BLOCKED real smoke |
| 9 | `docs/phase-reports/phase-10-browser-viseme-3d-speaking-model.md` | Text → WAV → browser viseme JSON → 3D speaking face | PASS |

## Log handoff protocol

Mỗi lần làm phase phải ghi log vào:

```text
logs/sessions/facespeed-safe-completion.md
```

Format log tối thiểu:

```text
[YYYY-MM-DD HH:MM] Phase X - <name>
Status: PASS | BLOCKED | REDO | ASK
Commands/tests:
- ...
Evidence:
- ...
Resource snapshot:
- ...
Next:
- ...
```

## Comment đóng plan

Khi phase xong, thêm cuối file phase:

```text
## Close Comment

Status: PASS | BLOCKED
Closed at: YYYY-MM-DD HH:MM
Evidence:
- ...
Log entry: logs/sessions/facespeed-safe-completion.md#phase-x
Next plan: plans/plan-0Y-...
Notes:
- ...
```

## Safety baseline hiện tại

- Host nhiều project quan trọng; mọi process đang chạy coi là quan trọng.
- Chỉ localhost.
- Port đề xuất: backend `8020`, frontend `6210`, Riva `50100`, A2F `8040`.
- Nếu port conflict: hỏi user, không tự đổi.
- Chừa tối thiểu 10% VRAM/RAM/disk/commit.
- Riva/A2F chạy container mới cho project, không can thiệp service khác.
- Docker cleanup chỉ stopped/unused sau xác nhận.
- NVIDIA key không được ghi vào repo/log/docs; nhắc user rotate key sau setup.
