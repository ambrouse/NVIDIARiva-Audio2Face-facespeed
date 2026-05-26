---
name: backend-skill
description: "Quy tắc bắt buộc khi thiết kế, viết và review code backend."
argument-hint: "backend task"
user-invocable: true
---

# Backend Skill

Áp dụng khi task chạm API, service, database, job, queue, integration, migration hoặc logic nghiệp vụ phía server.

## Nguyên Tắc

- Thiết kế rõ boundary: controller/route chỉ nhận request và trả response; service xử lý nghiệp vụ; repository/data layer xử lý truy cập dữ liệu.
- Ưu tiên schema/DTO rõ ràng cho input, output và contract nội bộ.
- Không trộn logic nghiệp vụ với framework glue code, query thô hoặc format response nếu có thể tách hợp lý.
- Không thêm abstraction khi chưa giảm được độ phức tạp thật hoặc chưa khớp pattern hiện có.
- Tên hàm, route, event, job và file phải nói đúng hành vi, tránh tên chung chung.

## API Và Dữ Liệu

- Validate input tại boundary; kiểm type, required field, enum, range, length, format và unknown field nếu cần.
- Response nên ổn định, có status code đúng, lỗi rõ nhưng không lộ stack trace, SQL, internal path hoặc secret.
- Query database phải dùng ORM/query builder/parameterized query an toàn.
- Migration cần có rollback hoặc kế hoạch khôi phục khi thay đổi dữ liệu quan trọng.
- Với tác vụ idempotent, webhook, retry hoặc queue, phải xử lý duplicate và race condition.

## Testing

- Test backend nên kiểm request thật qua HTTP/test client hoặc integration layer khi có API contract.
- Với service logic, test cả happy path, error path, edge case và side effect quan trọng.
- Không mock database/external service quá mức nếu mock làm mất niềm tin vào contract.

## Hoàn Thành

- Code đọc được, ít side effect ẩn và khớp architecture hiện có.
- API contract, validation, lỗi và side effect đã được verify.
- Nếu chạm auth, permission, dữ liệu nhạy cảm hoặc config, phải dùng thêm `security-skill`.
