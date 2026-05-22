---
name: testing-skill
description: Quy tắc bắt buộc khi thiết kế, viết, chạy, đánh giá và ghi nhận test cho frontend, backend, logic, UI, benchmark và lỗi biên.
argument-hint: "testing task"
user-invocable: true
---

# Testing Skill

Áp dụng khi viết/sửa/chạy test, kiểm chứng bugfix, tăng coverage, benchmark, QA checklist hoặc đánh giá chất lượng release.

## Mục tiêu
- Test phải chứng minh hành vi quan trọng của sản phẩm, không chỉ tăng coverage.
- Chọn tầng test nhỏ nhất nhưng đủ niềm tin: unit cho logic thuần, integration cho module phối hợp, backend/API cho request-contract-side effect, UI/E2E cho luồng người dùng thật.
- Với bugfix, phải có regression test hoặc ghi rõ vì sao không thể tự động hóa.
- Không mock quá mức; chỉ mock boundary ngoài hệ thống như payment, email, external API, clock, random, network.
- Test phải deterministic, chạy lại ổn định, không phụ thuộc thứ tự, sleep cố định, timezone, network thật hoặc state máy cá nhân.

## Evidence folder và ảnh chứng minh
- Khi task cần UI/manual/e2e validation, real app run, provider validation, release QA, hoặc kết quả không thể chứng minh đủ bằng command output, phải tạo folder evidence trong `test/` hoặc theo convention test của repo. Nếu repo chưa có convention, dùng mẫu tổng quát `test/<feature-or-task>-evidence-YYYY-MM-DD/`.
- Evidence folder phải đọc được trên GitHub: có `README.md` ở root evidence, và nếu có nhiều app/provider/module thì mỗi đối tượng có folder riêng kèm `README.md` riêng.
- Chia folder theo ý nghĩa kiểm chứng, không chia theo tool nội bộ. Mẫu mặc định có thể dùng: `app/` cho màn hình app đã mở và ready, `function/` cho từng chức năng người dùng thao tác, `lifecycle/` hoặc `status/` cho trạng thái run/health/metrics, `logs/` cho log/observability hiển thị trên UI, `blockers/` chỉ khi cần lưu ảnh lỗi để giải thích việc chưa pass.
- Mỗi ảnh pass phải chứng minh một hành vi cụ thể: nên thấy được input/action và output/result trong cùng khung hình khi có thể. Ảnh chỉ có loading, pending, empty state, trang home chưa thao tác, toast mơ hồ, console/log thuần kỹ thuật, hoặc bị crop mất kết quả thì không được tính là pass evidence.
- Với chức năng sinh output như chatbot/search/upload/report/checkout, ảnh pass phải có kết quả thật sau khi chạy xong: câu trả lời, danh sách kết quả, file đã xử lý, order/result id, bảng đã cập nhật, log đã stream, hoặc status đã đổi rõ ràng.
- Mỗi chức năng/state chỉ giữ một ảnh tốt nhất, đặt tên có thứ tự và hành vi rõ ràng, ví dụ `01-search-query-results.png`, `02-upload-completed-summary.png`, `03-service-logs-streaming.png`. Xóa ảnh trùng, ảnh lặp lại, ảnh sai, ảnh tạm, và ảnh không thêm niềm tin.
- Sau khi chụp ảnh phải đọc lại ảnh như người review: zoom/kiểm tra bằng mắt rằng kết quả có hiện rõ, không còn spinner/pending, không bị che, không trùng với ảnh khác, và không lộ secret/PII/token/key. Nếu ảnh không đạt, xóa và chụp lại.
- README trong evidence root phải nêu scope, đối tượng đã test, kết quả, điều kiện chạy quan trọng, giới hạn/skip nếu có, và link đến từng folder con. README trong mỗi folder đối tượng phải có run report ngắn: app chạy ở đâu, test bao lâu/kết quả, chức năng nào đã pass, blocker nào còn lại, commit/source fix liên quan nếu có.
- Evidence chỉ nên giữ artifact người review cần xem: ảnh `.png` và report `.md` là mặc định. File raw `.json`, `.txt`, `.log`, network dump, console dump chỉ được giữ khi task yêu cầu rõ hoặc đó là bằng chứng duy nhất; khi giữ phải redacted, có lý do trong README, và không thay thế ảnh UI nếu user cần frontend proof.
- Sau khi đóng gói evidence, phải chạy quick hygiene phù hợp với repo: scan duplicate image hash, scan missing README links, scan secret pattern, và kiểm tra folder không còn artifact tạm/kỹ thuật. Không nói "đã có ảnh chứng minh" nếu chưa đọc lại ảnh và chưa clean evidence.
- Khi lỗi đến từ bên thứ ba, thiếu key, quota, service ngoài, hay điều kiện môi trường, phải chụp/ghi bằng chứng lỗi vừa đủ để xác định nguyên nhân, không lộ secret, và đề xuất các hướng xử lý rõ ràng thay vì đánh dấu pass.

## Logs, docs và báo cáo
- Log test ngắn gọn: thời gian, mục tiêu, command, output/kết quả chính, blocker, rủi ro còn lại; không ghi secret/PII/payload production/stack trace nhạy cảm.
- Nếu test thay đổi vận hành, API contract, QA checklist hoặc release guide, cập nhật docs phù hợp bằng `documentation-skill`.
- Báo cáo cuối phải nêu test đã chạy, kết quả, test chưa chạy được và lý do; không nói “đã test” nếu chỉ đọc code hoặc chỉ chạy typecheck.

## Không được làm
- Không sửa test để khớp bug sai nếu requirement chưa đổi.
- Không xóa test fail mà không thay bằng test đúng hơn.
- Không bypass test/linter/hook bằng flag skip nếu user chưa yêu cầu rõ.
- Không đưa secret, token, dữ liệu thật hoặc PII vào fixture, snapshot, logs hay report.
