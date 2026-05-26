# Running Plans

Thư mục này lưu plan đang mở hoặc đang chờ verify. Khi task hoàn thành và không còn việc mở, chuyển plan sang `plans/plan-{task-name}-YYYYMMDD-v1.md`.

Mỗi plan đang chạy nên có:

- `Created`, `Updated`, `Status`.
- Related log và related doc.
- Goal, Scope, Skills, Phases, Verification, Close Criteria.
- Status phase dùng `pending`, `in_progress`, `blocked`, `testing`, `done`, hoặc `skipped`.

`LATEST.md` có thể trỏ tới plan đang được ưu tiên nhất nếu có nhiều plan song song.
