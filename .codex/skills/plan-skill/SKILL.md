---
name: plan-skill
description: 'Những quy tắt bắt buộc khi lập kế hoạch dự án.'
argument-hint: 'tuân thủ các quy tắc đã đề ra.'
user-invocable: true
---

# Plan Skill

Áp dụng cho task có nhiều bước, nhiều file, cần fix lỗi quan trọng, cần phối hợp nhiều skill hoặc cần theo dõi tiến trình rõ ràng.

## Mục tiêu
- Mỗi task quan trọng phải có plan rõ để biết mục tiêu, phạm vi, phase, status, test, log và điều kiện đóng task.
- Plan không phải tài liệu dài; phải đủ chi tiết để làm đúng, theo dõi được và tránh bỏ sót.
- Nếu requirement mơ hồ, hỏi trước khi lập plan hoặc trước khi bắt đầu phase rủi ro.

## File plan
- Lưu plan trong `plans/plan-{task-name}.md`.
- Tên task dùng kebab-case, ngắn, dễ tìm.
- Plan phải có: mục tiêu, phạm vi, ngoài phạm vi, skill cần dùng, rủi ro, phase, status, test/verify, log liên quan.

## Format bắt buộc
```md
# Plan: {Task Name}

- Created: YYYY-MM-DD HH:mm
- Updated: YYYY-MM-DD HH:mm
- Status: planned | in_progress | blocked | verifying | completed | closed
- Related log: logs/{type}/{file}.md

## Goal
...

## Scope
- In: ...
- Out: ...

## Skills
- frontend-skill / backend-skill / testing-skill / security-skill / documentation-skill / logging-skill / push-code-skill

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | ... | pending | ... |

## Verification
- ...

## Close criteria
- ...
```

## Phase workflow
- Chia task thành nhiều phase nhỏ, mỗi phase có status: `pending`, `in_progress`, `blocked`, `testing`, `done`, `skipped`.
- Mỗi phase phải nêu goal, việc làm, skill áp dụng, test/verify cần chạy và evidence cần log.
- Làm tuần tự theo phase; không chuyển phase tiếp nếu phase hiện tại chưa đạt test/verify, trừ khi ghi rõ blocker hoặc lý do skip.
- Khi bắt đầu phase, cập nhật status `in_progress`; khi test, cập nhật `testing`; khi đạt, cập nhật `done`.
- Nếu đổi hướng, cập nhật plan ngay: lý do đổi, phase bị ảnh hưởng, test/log mới cần có.

## Kết hợp logs
- Mỗi plan phải có log tương ứng trong `logs/` theo `logging-skill`.
- Log phải ghi trong phiên làm việc: thời gian, mục tiêu, cách chắt lọc, cách phân chia phase, thay đổi đã làm, test/verify, blocker, kết quả.
- Luôn cập nhật log sau mỗi phase quan trọng, sau khi test/verify và khi đóng task.
- Log chỉ ghi điểm chính, không copy toàn bộ plan hoặc output dài; nếu nhiều log liên quan thì gom/tóm tắt để dễ tra cứu.

## Test và verification
- Phase backend phải dùng `testing-skill`: ưu tiên test request thật qua HTTP/test client hoặc integration layer và đánh giá output/side effect.
- Phase frontend phải dùng `frontend-skill` + `testing-skill`: chạy app/browser khi có UI change, soi giao diện thật, đánh giá responsive/state/accessibility và tối ưu nếu cần.
- Phase security phải dùng `security-skill`: kiểm auth, permission, input/output, secrets, dependency, config và logging nhạy cảm.
- Không claim hoàn thành nếu chưa có evidence test/verify hoặc chưa ghi rõ vì sao chưa test được.

## Đóng plan
- Khi toàn bộ phase đạt, chuyển Status thành `completed`, ghi summary kết quả và evidence.
- Sau khi log cuối đã cập nhật và task không còn việc mở, chuyển Status thành `closed`.
- Close criteria tối thiểu: code/docs/logs đúng phạm vi, test/verify đạt hoặc có lý do chưa chạy, rủi ro còn lại được ghi rõ.
- Không tự push sau khi hoàn thành trừ khi user yêu cầu; nếu push, dùng `push-code-skill`.
