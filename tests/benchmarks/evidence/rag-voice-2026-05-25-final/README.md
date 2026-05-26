# RAG Voice Evidence - Final - 2026-05-25

Evidence cuối cho benchmark RAG Voice ngày 2026-05-25.

| File | Nội dung |
| --- | --- |
| `frontend-answer.png` | Frontend hiển thị câu hỏi, answer, citation và avatar. |
| `audio-input-question.wav` | Voice input thật dùng để test ASR. |
| `asr-input-question.json` | ASR input. |
| `audio-output.wav` | Voice output từ frontend. |
| `asr-output-answer.json` | ASR lại audio output, chỉ để tham khảo. |
| `voice-chat-evidence.json` | Response `/api/voice/chat` có answer/citation/audio/animation. |
| `voice-chat-audio-output.wav` | Audio output từ response API thật. |
| `voice-chat-animation-output.json` | Animation output từ response API thật. |
| `browser-report.json` | Browser report, không có console error/failed response trong evidence cuối. |

Kết quả tổng hợp nằm trong `tests/benchmarks/REPORT-2026-05-25-rag-voice.md`.
