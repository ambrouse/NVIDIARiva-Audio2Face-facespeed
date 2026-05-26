---
name: documentation-skill
description: "Quy tắc bắt buộc khi viết và cập nhật tài liệu dự án."
argument-hint: "documentation task"
user-invocable: true
---

# Documentation Skill

Áp dụng khi task tạo mới hoặc cập nhật README, docs, release note, hướng dẫn vận hành, kiến trúc, API, changelog hoặc tài liệu theo plan.

## Lưu Trữ

- Tài liệu task lưu trong `docs/` ở root repo.
- Chọn thư mục theo mục đích: `docs/task/`, `docs/plan/`, `docs/summary/`, `docs/bug/`, `docs/knowledge/` hoặc convention sẵn có của repo.
- Mỗi plan quan trọng cần có một doc riêng để ghi mục tiêu, phạm vi, thay đổi, thời gian, kết quả và cách verify.
- Tên doc nên kèm thời gian và version nếu có: `docs/task/task1-YYYYMMDD-v1.md`.
- Trong mỗi folder con luôn có file `README.md` để mô tả mục đích và cách sử dụng các doc trong đó, readme phải rõ ràng dễ hiểu có mô tả chi tiết folder này lưu trữ doc gì, về gì, sơ qua nội dung, v.v.v.v.

## Nội Dung

- Viết tiếng Việt có dấu, rõ ý, tránh câu dài và tránh lặp.
- Ghi ngày/thời gian khi tài liệu mô tả một task hoặc quyết định.
- Tài liệu phải khớp source hiện tại; không mô tả file, workflow, feature hoặc test không tồn tại.
- Nếu chỉ là task nhỏ, doc nên ngắn và tập trung vào kết quả review cần biết.
- Không đưa secret, token, credential, payload nhạy cảm hoặc dữ liệu cá nhân vào docs.

## Sau Khi Sửa

- Rà lại docs liên quan để xóa thông tin lỗi thời hoặc ghi chú rủi ro còn lại.
- Nếu thay đổi ảnh hưởng README/changelog/release note, cập nhật các file đó cùng task.
- Nếu không thể verify nội dung, ghi rõ giả định hoặc blocker.
