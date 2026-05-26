---
name: push-code-skill
description: "Quy tắc bắt buộc khi commit, tag và push dự án."
argument-hint: "push task"
user-invocable: true
---

# Push Code Skill

Áp dụng khi user yêu cầu commit, tag, push, release hoặc publish thay đổi lên remote.

## Trước Khi Commit

- Kiểm tra `git status --short --branch` và đọc diff staged/unstaged.
- Không revert hoặc ghi đè thay đổi của user ngoài phạm vi task.
- Chạy test/validation phù hợp với repo; tối thiểu phải có lý do rõ nếu không chạy được.
- Kiểm tra CI/CD hiện có; nếu repo chưa có validation cơ bản và task phù hợp, thêm hoặc cập nhật workflow.
- Rà `.gitignore`, `.env`, `.env.example` nếu task chạm config hoặc có nguy cơ lộ secret.

## Version Và Release

- Mỗi lần push release phải cập nhật `VERSION`, `CHANGELOG.md` và `RELEASE_NOTES.md` nếu repo đang dùng các file này.
- Tạo tag rõ ràng theo version, ví dụ `v0.3.1`.
- Commit message phải có thời gian hoặc ngày, mô tả ngắn gọn và body nêu thay đổi chính.

## README Và Metadata

- Nếu thay đổi ảnh hưởng cách dùng repo, skill list, workflow, CI hoặc version, cập nhật README.
- Dùng `readme-style` khi sửa README.
- README và release metadata viết tiếng Việt có dấu nếu repo đang thống nhất tiếng Việt.

## Bảo Mật

- Trước khi push, scan cơ bản để tránh commit secret, token, `.env` thật, private key hoặc dữ liệu nhạy cảm.
- Không dùng force push, rewrite history hoặc xóa evidence nếu user chưa yêu cầu rõ.

## Sau Khi Push

- Xác nhận branch/tag trên remote.
- Báo commit hash, tag, test/validation đã chạy và trạng thái working tree.
