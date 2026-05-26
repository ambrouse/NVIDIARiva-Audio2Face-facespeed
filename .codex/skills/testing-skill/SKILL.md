---
name: testing-skill
description: "Quy tắc bắt buộc khi thiết kế, chạy, đánh giá và ghi nhận test."
argument-hint: "testing task"
user-invocable: true
---

# Testing Skill

Áp dụng khi viết/sửa/chạy test, kiểm chứng bugfix, tăng coverage, benchmark, QA checklist hoặc đánh giá chất lượng release.


## Evidence Và Ảnh Chứng Minh

- luôn dùng ảnh, audio, video, để chứng minh nó chạy ổn và pass test phải đọc kỹ ảnh chụp để chứng minh không phải chụp là xong, dùng `test/type test/<feature-or-task>-evidence-YYYY-MM-DD/`.
- Evidence folder phải đọc được trên GitHub, có `README.md` ở root evidence và folder con theo app/provider/module nếu cần.
- Ảnh pass phải chứng minh hành vi cụ thể: thấy input/action và output/result trong cùng khung hình khi có thể.
- Không tính là pass nếu ảnh chỉ có loading, pending, empty state, toast mơ hồ, console log hoặc bị crop mất kết quả.
- Sau khi chụp ảnh, đọc lại ảnh như reviewer: kết quả rõ, không spinner, không bị che, không trùng và không lộ secret/PII/token/key.

## Logs, Docs Và Báo Cáo

- Log test ghi ngắn: thời gian, mục tiêu, command, kết quả chính, blocker và rủi ro còn lại.
- Nếu test thay đổi vận hành, API contract, QA checklist hoặc release guide, cập nhật docs bằng `documentation-skill`.
- Báo cáo cuối phải nêu test đã chạy, kết quả, test chưa chạy được và lý do.
- Không nói “đã test” nếu chỉ đọc code hoặc chỉ chạy typecheck mà chưa verify hành vi liên quan.
- Tên file test nên kèm thời gian và version nếu có: `tests/frontend-navbar/test-{feature-or-task}-YYYYMMDD-v1.md`.
- Trong mỗi folder con luôn có file `README.md` để mô tả mục đích và cách sử dụng các doc trong đó, readme phải rõ ràng dễ hiểu có mô tả chi tiết folder này lưu trữ doc gì, về gì, sơ qua nội dung, v.v.v.v.

## Không Được Làm

- Không sửa test để khớp bug sai nếu requirement chưa đổi.
- Không xóa test fail mà không thay bằng test đúng hơn.
- Không bypass test/linter/hook bằng flag skip nếu user chưa yêu cầu rõ.
- Không đưa secret, token, dữ liệu thật hoặc PII vào fixture, snapshot, logs hay report.
