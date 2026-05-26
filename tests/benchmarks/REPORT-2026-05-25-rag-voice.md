# RAG Voice Benchmark Report - 2026-05-25

## Tóm Tắt

Benchmark chạy trên 100 PDF arXiv đã index, tổng 11,022 chunk. Có 4 batch: 10 câu/1 user, 10 câu/10 user, 30 câu/1 user, 30 câu/10 user. Tổng cộng 80/80 case pass.

Kết quả có ý nghĩa nhất:

| Chỉ số | Kết quả |
| --- | ---: |
| RAG answer pass | 80/80 |
| Đúng file cần tìm | 80/80 |
| Đúng page cần tìm | 80/80 |
| Đúng chunk cần tìm | 80/80 |
| Judge correct | 80/80 |
| Judge grounded | 80/80 |
| Judge no hallucination | 80/80 |
| Có audio output | 80/80 |
| Có animation output | 80/80 |

Single-user p50 khoảng 6.3s. Batch 10-user p95 khoảng 57-58s, chủ yếu do Riva TTS đang chạy tuần tự để tránh crash.

## Bảng Hiệu Năng

| Batch | Runtime | Accuracy | File/page/chunk | Audio | Animation | Latency p50 / p95 / max | Resource thấp nhất |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 10 câu / 1 user | `_latest-10` | 100% | 100% | 100% | 100% | 6.31s / 13.90s / 13.90s | RAM free 67.98%, VRAM free 17.52% |
| 10 câu / 10 user | `_latest-10-users-10` | 100% | 100% | 100% | 100% | 56.76s / 58.21s / 58.21s | RAM free 67.88%, VRAM free 17.53% |
| 30 câu / 1 user | `_latest-30` | 100% | 100% | 100% | 100% | 6.32s / 6.59s / 6.64s | RAM free 67.41%, VRAM free 17.52% |
| 30 câu / 10 user | `_latest-30-users-10` | 100% | 100% | 100% | 100% | 56.01s / 57.82s / 57.91s | RAM free 67.27%, VRAM free 17.58% |

## VRAM

GPU trong evidence: NVIDIA RTX PRO 5000 Blackwell, 48,935 MiB.

| Mốc đo | VRAM |
| --- | ---: |
| Baseline snapshot trước provider runtime cuối | 35,827 MiB used |
| Max observed khi benchmark chạy | 39,833 MiB used |
| Min observed free khi benchmark chạy | 8,574 MiB free |
| Ước tính tăng thêm của FaceSpeed | khoảng 4,006 MiB |
| Budget ghi vào env | `PROJECT_VRAM_EXPECTED_MIB=4000` |
| Free VRAM nên có trước start | `PROJECT_VRAM_RECOMMENDED_FREE_MIB=9000` |

Cách tính: `39,833 - 35,827 = 4,006 MiB`. Đây là số đo vận hành trên máy benchmark, không phải cam kết cho mọi GPU/model.

## Câu Hỏi - Câu Trả Lời Mẫu

| # | Câu hỏi | Expected source | Answer summary | Judge |
| ---: | --- | --- | --- | --- |
| 1 | Summarize “differential subordination and form the foundation...” | `2605_22688v1.pdf` p.3 | Answer trích Janowski starlike class và differential subordination làm nền cho kết quả. | Correct, grounded |
| 2 | “scarcity of experimental data...” | `2605_22689v1.pdf` p.3 | Answer nói thiếu state-selective observation làm khó benchmark model. | Correct, grounded |
| 3 | “algorithm that runs...” | `2605_22690v1.pdf` p.2 | Answer nêu thuật toán `O(n^4 log n)` time, `O(n)` space. | Correct, grounded |
| 4 | “intrinsic properties of the data...” | `2605_22691v1.pdf` p.4 | Answer nói active latent dimensions phụ thuộc scaling/loss convention. | Correct, grounded |
| 5 | “data assimilation in conditional gaussian systems...” | `2605_22692v1.pdf` p.7 | Answer tóm tắt filtering/smoothing và closed-form Gaussian evolution. | Correct, grounded |
| 6 | “learning-informed planning framework...” | `2605_22693v1.pdf` p.5 | Answer mô tả SAP-IAP, information gain và GNN predictor. | Correct, grounded |
| 7 | Rogers, De Witt, Leites approaches | `2605_22694v1.pdf` p.5 | Answer nêu các hướng tiếp cận supermanifold và control theory. | Correct, grounded |
| 8 | “limited viewpoint diversity during training” | `2605_22695v1.pdf` p.2 | Answer nói về viewpoint invariance và temporal consistency. | Correct, grounded |
| 9 | “idealized model” | `2605_22696v1.pdf` p.7 | Answer nói về mô hình lý tưởng khi phân tích photon ring/Kerr black holes. | Correct, grounded |
| 10 | “cross-domain capabilities...” | `2605_22697v1.pdf` p.2 | Answer nói về motion cues + textual descriptions cho action recognition. | Correct, grounded |

Chi tiết đầy đủ nằm trong `runs/matrix/file-100/_latest-10/case-log.md` và `runs/matrix/file-100/_latest-30/case-log.md`.

## Audio Và Animation Evidence

Evidence cuối: `tests/benchmarks/evidence/rag-voice-2026-05-25-final/`.

| File | Nội dung |
| --- | --- |
| `frontend-answer.png` | Frontend hiển thị câu hỏi, answer, citation và avatar. |
| `audio-input-question.wav` | Voice input thật dùng để test ASR. |
| `asr-input-question.json` | ASR input nhận đúng lõi câu hỏi, confidence thấp. |
| `audio-output.wav` | Voice output từ frontend, 44.1 kHz mono, khoảng 18.19s. |
| `asr-output-answer.json` | ASR lại audio output; nhận lõi answer nhưng không dùng làm judge. |
| `voice-chat-evidence.json` | Response `/api/voice/chat` có answer, citation, audio, animation. |
| `voice-chat-animation-output.json` | Animation output từ API thật. |
| `browser-report.json` | Không có console error hoặc failed response trong evidence cuối. |

## Các Lỗi Đã Sửa Trước Khi Pass

- Search chậm do membership O(n^2): đổi sang set chunk id.
- Answer có thể chọn citation đầu tiên thay vì citation tốt hơn: thêm chọn citation theo phrase/keyword/context quality.
- TTS từng bị fallback che lỗi: bỏ fallback, audio fail là case fail.
- Riva TTS crash khi synthesize đồng thời: thêm `RIVA_TTS_MAX_CONCURRENCY=1`.
- Riva TTS postprocessor resample 22.05 kHz -> 44.1 kHz: đổi `RIVA_SAMPLE_RATE_HZ=44100`.
- Voice text quá dài gây tải TTS: rút spoken text, giữ answer/citation đầy đủ trên frontend.
- Gate được siết thêm `answer_source_cited` và `answer_source_expected_document`.

## Rủi Ro Còn Lại

- 10-user latency khoảng 56-58s, chưa đạt mục tiêu interactive dưới 15s.
- ASR confidence thấp với tên PDF/ký hiệu kỹ thuật; không dùng ASR làm judge cuối.
- Cold-start Riva TTS sau restart vẫn có thể timeout nếu chưa warm-up.
- Citation phụ có thể trỏ sang tài liệu liên quan khác; gate hiện đảm bảo answer source đúng file và expected file/page/chunk có trong citation.
