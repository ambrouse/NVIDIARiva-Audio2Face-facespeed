---
name: fix
description: Quy trình bắt buộc khi fix lỗi, đặc biệt lỗi quan trọng: dùng plan-skill để lập plan, chia phase, fix, test thật và log tiến trình.
argument-hint: "fix task"
user-invocable: true
---

# Fix Skill

Áp dụng khi user yêu cầu fix bug, sửa lỗi production, regression, test fail, build fail, security bug, UI bug hoặc hành vi sai quan trọng.

## Nguyên tắc
- Không fix mò; phải hiểu lỗi, phạm vi ảnh hưởng, nguyên nhân gốc và cách verify trước khi báo xong.
- Lỗi quan trọng bắt buộc dùng `plan-skill` để tạo plan nhiều phase có status và log tương ứng.
- Mỗi fix phải dùng skill liên quan: `backend-skill`, `frontend-skill`, `security-skill`, `testing-skill`, `logging-skill`, `documentation-skill` khi phù hợp.
- Không che lỗi bằng bypass, skip test, xóa assertion, catch rỗng hoặc fallback giả nếu chưa hiểu nguyên nhân.

## Pipeline bắt buộc
1. Triage: mô tả lỗi, expected vs actual, phạm vi, độ nghiêm trọng, file/khu vực nghi ngờ và cách tái hiện.
2. Plan: dùng `plan-skill` tạo/cập nhật plan trong `plans/`, chia phase có status và close criteria.
3. Reproduce: tái hiện lỗi bằng test, request thật, UI thật hoặc command đáng tin; nếu chưa tái hiện được, ghi rõ giả thuyết và bước điều tra.
4. Root cause: xác định nguyên nhân gốc, không chỉ symptom.
5. Fix: sửa nhỏ nhất đủ đúng, không refactor ngoài phạm vi.
6. Test: dùng `testing-skill` để chạy test phù hợp; backend phải test request thật và đánh giá output/side effect, frontend phải soi giao diện thật khi có UI change.
7. Security check: nếu lỗi chạm auth, permission, dữ liệu, input/output, dependency hoặc config, dùng `security-skill`.
8. Log: dùng `logging-skill` ghi thời gian, phase, cách chắt lọc, fix đã làm, test đã chạy, output chính, blocker và rủi ro còn lại.
9. Close: cập nhật plan phase `done`, plan `closed` khi đạt close criteria; báo rõ test đã chạy và việc chưa verify được nếu có.

## Reproduce và evidence
- Ưu tiên bằng chứng executable: failing test, API request/response, browser observation, log an toàn, command output.
- Backend/API: kiểm status code, response schema/body, headers, database/side effect, audit/log event nếu liên quan.
- Frontend/UI: kiểm layout thật, interaction, responsive, loading/empty/error, focus/accessibility và visual regression bằng browser/dev server khi có thể.
- Không claim “fixed” nếu chỉ đọc code hoặc chỉ typecheck mà chưa verify hành vi lỗi.

## Khi test fail hoặc blocker
- Đọc lỗi để xác định root cause; không bypass hook/test/linter nếu user chưa yêu cầu rõ.
- Nếu test cũ sai vì requirement đổi, cập nhật test cùng lý do ngắn.
- Nếu không thể test do thiếu môi trường/credential/service, ghi rõ blocker, rủi ro và cách user có thể verify.

## Báo cáo cuối
- Nêu nguyên nhân gốc, thay đổi đã làm, test/verify đã chạy, kết quả và rủi ro còn lại.
- Dẫn chiếu plan/log nếu task có nhiều phase.
- Không tự commit/push trừ khi user yêu cầu; nếu push, dùng `push-code-skill`.
