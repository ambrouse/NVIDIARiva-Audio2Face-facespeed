---
name: plan-skill
description: "Quy tắc bắt buộc khi lập kế hoạch dự án theo phase."
argument-hint: "planning task"
user-invocable: true
---

# Plan Skill

Áp dụng cho task có nhiều bước, nhiều file, nhiều skill, rủi ro cao hoặc cần theo dõi tiến trình rõ ràng.

## Mục Tiêu

- Plan phải nêu mục tiêu, phạm vi, ngoài phạm vi, skill cần dùng, rủi ro, phase, status, verify và close criteria.
- Plan không cần dài, nhưng phải đủ rõ để làm đúng và không bỏ sót.
- Nếu yêu cầu mơ hồ hoặc có phase rủi ro, hỏi trước hoặc ghi giả định rõ trong plan.

## File Plan

- Plan đang chạy lưu trong `plans/running/plan-{task-name}.md`.
- Khi task hoàn thành và không còn việc mở, chuyển plan ra `plans/plan-{task-name}.md`.
- Tên task dùng kebab-case, ngắn và dễ tìm.
- Mỗi plan quan trọng phải có log tương ứng trong `logs/` và doc tương ứng trong `docs/`.
- Tên plan nên kèm thời gian và version nếu có: `plans/plan-{task-name}-YYYYMMDD-v1.md`.
- Trong mỗi folder con luôn có file `README.md` để mô tả mục đích và cách sử dụng các doc trong đó, readme phải rõ ràng dễ hiểu có mô tả chi tiết folder này lưu trữ doc gì, về gì, sơ qua nội dung, v.v.v.v.

## Format Bắt Buộc

```md
# Plan: {task-name}

- Created: YYYY-MM-DD HH:mm
- Updated: YYYY-MM-DD HH:mm
- Status: planned | in_progress | blocked | verifying | completed | closed
- Related log: logs/{type}/{file}.md
- Related doc: docs/{type}/{file}.md

## Goal
...

## Scope
- In: ...
- Out: ...

## Skills
- ...

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | ... | pending | ... |

## Verification
- ...

## Close Criteria
- ...
```

## Phase Workflow

- Status phase dùng: `pending`, `in_progress`, `blocked`, `testing`, `done`, `skipped`.
- Bắt đầu phase thì cập nhật `in_progress`; khi verify thì cập nhật `testing`; đạt thì cập nhật `done`.
- Không chuyển phase nếu phase hiện tại chưa đạt verify, trừ khi ghi rõ blocker hoặc lý do skip.
- Nếu đổi hướng, cập nhật plan ngay: lý do, phase bị ảnh hưởng và verify/log mới.

## Verification Và Đóng Plan

- Backend/API phase dùng thêm `backend-skill` và `testing-skill`.
- Frontend/UI phase dùng thêm `frontend-skill` và `testing-skill`.
- Security/config/secret phase dùng thêm `security-skill`.
- Khi toàn bộ phase đạt, chuyển status thành `completed`; sau log/doc cuối, chuyển thành `closed`.
- Không tự push nếu user chưa yêu cầu; nếu push, dùng `push-code-skill`.

## Ngôn Ngữ

- Viết tiếng Việt có dấu.
