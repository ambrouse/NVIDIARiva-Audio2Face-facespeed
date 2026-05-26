---
name: logging-skill
description: "Quy tắc bắt buộc khi ghi và quản lý log phiên làm việc của dự án."
argument-hint: "logging task"
user-invocable: true
---

# Logging Skill

Áp dụng khi task có plan, nhiều phase, thay đổi quan trọng, verification đáng ghi lại hoặc cần hồ sơ để tra cứu sau này.

## Lưu Trữ

- Log phiên làm việc lưu trong `logs/` ở root repo.
- Chọn thư mục theo loại task: `logs/skills/`, `logs/documentation/`, `logs/security/`, `logs/testing/`, `logs/release/` hoặc convention sẵn có.
- Mỗi plan quan trọng cần có một log riêng, liên kết ngược tới plan và doc nếu có.

## Nội Dung

- Viết tiếng Việt có dấu, ngắn gọn và dễ tra cứu.
- Ghi thời gian bắt đầu/kết thúc, mục tiêu, phase chính, file đã sửa, verify đã chạy, blocker và rủi ro còn lại.
- Không copy output dài; chỉ ghi command quan trọng và kết quả chính.
- Không ghi secret, token, credential, PII, stack trace nhạy cảm hoặc payload production.

## Cập Nhật Theo Phase

- Cập nhật log khi bắt đầu task, sau phase quan trọng, sau verification và khi đóng task.
- Nếu đổi hướng, ghi lý do đổi và ảnh hưởng tới plan/test.
- Khi task xong, log phải có kết quả cuối và trạng thái `completed` hoặc lý do chưa hoàn thành.
