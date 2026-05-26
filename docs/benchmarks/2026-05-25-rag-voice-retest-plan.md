# RAG Voice Retest Plan

- Created: 2026-05-25 16:03 +07
- Status: blocked
- Related plan: `plans/running/plan-rag-voice-retest-100pdf.md`
- Related log: `logs/benchmarks/2026-05-25-rag-voice-retest-plan.md`

## Tóm Tắt

Project đã có port riêng trong dải `6000-6500` và corpus PDF thật. Lần test trước dừng ở batch nhẹ nhất vì Riva TTS `6051` offline, nên chưa được tính pass. Kế hoạch chạy lại sẽ bắt đầu bằng health check provider thật, sau đó chạy smoke, benchmark `10/30 câu x 1/10 user`, capture frontend/audio và report.

Snapshot lúc lập plan: chỉ thấy `6001-6003` đang listen; backend/frontend/Riva/provider bridge chưa listen. VRAM còn khoảng `12578MiB/48935MiB`, sát ngưỡng `25%`, nên full benchmark phải chạy với resource guard và dừng ngay nếu tụt dưới ngưỡng.

## Kết Quả Bắt Đầu Test 2026-05-25 16:12 +07

- Đã start backend/frontend trên `6320/6310`.
- Đã xác nhận `/api/documents`: `100` document indexed, `11022` chunks.
- Đã dọn `tests/` theo yêu cầu, chỉ giữ `tests/benchmarks/`.
- Smoke API thật bị blocked:
  - `/api/rag/search`: embedding API `6106` connection refused.
  - `/api/voice/chat`: embedding API `6106` connection refused.
  - `/api/voice/transcribe`: Riva ASR `6052` connection refused.
- Evidence blocker: `tests/benchmarks/evidence/rag-voice-2026-05-25-blocked/REPORT.md`.

## Điều Cần Sửa Trước Khi Pass

- Riva TTS `6051` và ASR `6052` phải online; không dùng mock/fallback để báo pass.
- Benchmark cần thêm case xã giao và ngoài phạm vi, vì script hiện chủ yếu sinh câu RAG answerable.
- Evidence audio input phải là tiếng nói thật hoặc file voice test có transcript kỳ vọng; tone WAV chỉ dùng để kiểm file plumbing, không đủ pass voice input.
- Nếu đổi upload/chunk/embed/prompt retrieval thì phải chạy lại batch bị ảnh hưởng từ đầu; nếu đổi upload pipeline thì reupload/reindex đủ 100 PDF.

## Artefact Bắt Buộc

- Benchmark reports trong `tests/benchmarks/runs/matrix/file-100/`.
- Evidence frontend trong `tests/benchmarks/evidence/rag-voice-YYYY-MM-DD/`.
- Audio input thật: `audio-input.wav`.
- Audio output thật: `audio-output.wav`.
- Screenshot thấy input, answer, citation/source và trạng thái không loading.
- Report cuối có latency p50/p95/max, pass rate, source match, hallucination, resource samples và danh sách fail nếu còn.

## Pass/Fail

Không tìm đúng file/page/chunk là fail cho câu RAG. Câu xã giao hoặc ngoài phạm vi không được bịa citation. Batch chỉ pass khi complete đủ số case, accepted, có evidence, và resource guard không bị vi phạm.
