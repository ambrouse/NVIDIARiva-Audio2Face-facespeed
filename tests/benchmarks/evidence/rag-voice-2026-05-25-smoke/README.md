# RAG Voice Evidence - Smoke - 2026-05-25

Evidence này dùng để kiểm tra nhanh pipeline sau khi sửa provider/audio trước khi chạy batch benchmark đầy đủ.

| File | Nội dung |
| --- | --- |
| `frontend-answer.png` | Frontend có answer/citation/avatar trong smoke run. |
| `audio-input-question.wav` | Voice input smoke. |
| `asr-input-question.json` | Kết quả ASR input. |
| `audio-output*.wav` | Audio output từ pipeline. |
| `animation*.json` | Animation output. |
| `browser-report.json` | Browser report cho smoke run. |

Kết quả smoke không thay thế benchmark matrix; dùng `tests/benchmarks/README.md` để xem kết quả cuối.
