# RAG Voice Benchmark

Benchmark này kiểm tra luồng thật: PDF -> Docling -> embedding/rerank/Qdrant -> LLM answer -> Riva TTS -> animation artifact. Không tính pass nếu chỉ có text; mỗi case phải có citation đúng, audio URL và animation URL.

## Kết Quả Mới Nhất

Ngày chạy: 2026-05-25.

| Hạng mục | Kết quả |
| --- | --- |
| Corpus trên disk | 102 PDF arXiv trong `tests/benchmarks/corpus/arxiv/` |
| Số PDF dùng cho benchmark matrix | 100 PDF |
| Số chunk đã index | 11,022 chunk |
| Tổng case đã chấm | 80 case qua 4 batch |
| Pass tổng | 80/80, đạt 100% |
| Đúng file cần tìm | 80/80, đạt 100% |
| Đúng page cần tìm | 80/80, đạt 100% |
| Đúng chunk cần tìm | 80/80, đạt 100% |
| LLM judge correct/grounded/no hallucination | 100% cả 3 gate |
| Audio output | 100% case có `audioUrl` |
| Animation output | 100% case có `animationUrl` |

Kết luận ngắn: truy xuất đúng file/page/chunk trong toàn bộ benchmark hiện có. Single-user đủ dùng cho demo tương tác; 10-user còn chậm vì Riva TTS đang queue `RIVA_TTS_MAX_CONCURRENCY=1` để tránh crash provider.

## Hiệu Năng

| Batch | Concurrency | Case | Pass | Latency p50 | Latency p95 | Max | VRAM used max | VRAM free min | RAM free min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `_latest-10` | 1 | 10 | 10/10 | 6.31s | 13.90s | 13.90s | 39,831 MiB | 17.52% | 67.98% |
| `_latest-10-users-10` | 10 | 10 | 10/10 | 56.76s | 58.21s | 58.21s | 39,825 MiB | 17.53% | 67.88% |
| `_latest-30` | 1 | 30 | 30/30 | 6.32s | 6.59s | 6.64s | 39,833 MiB | 17.52% | 67.41% |
| `_latest-30-users-10` | 10 | 30 | 30/30 | 56.01s | 57.82s | 57.91s | 39,801 MiB | 17.58% | 67.27% |

VRAM note: benchmark chạy trên NVIDIA RTX PRO 5000 Blackwell 48,935 MiB. Snapshot baseline trước runtime provider cuối dùng 35,827 MiB; max benchmark dùng 39,833 MiB. Ước tính phần tăng thêm của FaceSpeed là khoảng 4,006 MiB. README gốc và `.env.example` dùng `PROJECT_VRAM_EXPECTED_MIB=4000`, `PROJECT_VRAM_RECOMMENDED_FREE_MIB=9000`.

## Câu Hỏi - Câu Trả Lời Mẫu

Các dòng dưới lấy từ `_latest-10/results.json`. Đây là mẫu để reviewer đọc nhanh xem hệ thống thật sự trả lời gì, tìm file nào, và có trỏ đúng nguồn không.

| # | Câu hỏi | File/page đúng | Trả lời chính | Kết quả |
| ---: | --- | --- | --- | --- |
| 1 | Summarize phrase “differential subordination and form the foundation...” | `2605_22688v1.pdf` p.3 | Nói về Janowski starlike class và differential subordination làm nền cho kết quả bài báo. | Pass, đúng file/page/chunk |
| 2 | Passage containing “scarcity of experimental data...” | `2605_22689v1.pdf` p.3 | Nêu thiếu dữ liệu thí nghiệm state-selective làm khó benchmark model phổ X-ray/EUV. | Pass, đúng file/page/chunk |
| 3 | Passage around “algorithm that runs...” | `2605_22690v1.pdf` p.2 | Thuật toán tối ưu hai rectangle chạy `O(n^4 log n)` time và `O(n)` space. | Pass, đúng file/page/chunk |
| 4 | Passage around “intrinsic properties of the data...” | `2605_22691v1.pdf` p.4 | Giải thích active latent dimensions phụ thuộc scaling/loss convention, không phải tính chất nội tại. | Pass, đúng file/page/chunk |
| 5 | Phrase “data assimilation in conditional gaussian systems...” | `2605_22692v1.pdf` p.7 | Tóm tắt filtering/smoothing trong conditional Gaussian systems và closed-form evolution. | Pass, đúng file/page/chunk |
| 6 | Phrase “learning-informed planning framework...” | `2605_22693v1.pdf` p.5 | Trình bày SAP-IAP cho robot team, dùng information gain và GNN predictor. | Pass, đúng file/page/chunk |
| 7 | Passage around Rogers/De Witt/Leites approaches | `2605_22694v1.pdf` p.5 | Nêu các hướng tiếp cận supermanifold và liên hệ điều khiển trên Lie supergroup. | Pass, đúng file/page/chunk |
| 8 | Phrase “limited viewpoint diversity during training” | `2605_22695v1.pdf` p.2 | Nói về viewpoint invariance và temporal consistency trong action detection. | Pass, đúng file/page/chunk |
| 9 | Passage around “idealized model” | `2605_22696v1.pdf` p.7 | Nói về mô hình lý tưởng để phân tích photon flux/photon ring quanh Kerr black holes. | Pass, đúng file/page/chunk |
| 10 | Phrase “cross-domain capabilities...” | `2605_22697v1.pdf` p.2 | Nói về kết hợp motion cues và textual descriptions cho cross-domain human action recognition. | Pass, đúng file/page/chunk |

Xem toàn bộ câu hỏi, expected excerpt, answer, citation và judge reason ở:

- `tests/benchmarks/runs/matrix/file-100/_latest-10/case-log.md`
- `tests/benchmarks/runs/matrix/file-100/_latest-30/case-log.md`

## Gate Pass

Một case chỉ pass khi tất cả điều kiện sau đúng:

| Gate | Ý nghĩa |
| --- | --- |
| `api` | API trả success. |
| `has_answer` | Có answer text. |
| `has_citations` | Có citation. |
| `expected_document_cited` | Citation chứa đúng PDF kỳ vọng. |
| `expected_page_cited` | Citation chứa đúng page kỳ vọng. |
| `expected_chunk_cited` | Citation chứa đúng chunk kỳ vọng. |
| `answer_source_cited` | Answer tự ghi source và source đó nằm trong citation. |
| `answer_source_expected_document` | Source trong answer là đúng PDF kỳ vọng. |
| `judge_correct` | LLM judge đánh giá answer đúng. |
| `judge_grounded` | LLM judge đánh giá answer bám nguồn. |
| `judge_no_hallucination` | LLM judge không thấy hallucination. |
| `audio_url` | Response có audio artifact. |
| `animation_url` | Response có animation artifact. |
| `dashboard_edges` | Agent trace có đủ các cạnh chính: user, lead, search, qdrant, teacher, review. |
| `latency_ok` | Latency nằm trong ngưỡng benchmark của batch. |

## Artifact Quan Trọng

| Đường dẫn | Nội dung |
| --- | --- |
| `runs/matrix/file-100/_latest-10/summary.json` | 10 câu, 1 user. |
| `runs/matrix/file-100/_latest-10-users-10/summary.json` | 10 câu, 10 user đồng thời. |
| `runs/matrix/file-100/_latest-30/summary.json` | 30 câu, 1 user. |
| `runs/matrix/file-100/_latest-30-users-10/summary.json` | 30 câu, 10 user đồng thời. |
| `evidence/rag-voice-2026-05-25-final/` | Evidence cuối: screenshot frontend, voice input/output, ASR, animation. |
| `REPORT-2026-05-25-rag-voice.md` | Báo cáo tổng hợp cùng số liệu chính. |

## Rủi Ro Còn Lại

- 10-user p95 khoảng 58s, chưa phù hợp nếu SLA yêu cầu phản hồi dưới 15s cho nhiều user đồng thời.
- ASR confidence thấp với tên PDF/ký hiệu kỹ thuật, nên ASR chỉ chứng minh pipeline voice thật, không dùng làm judge correctness cuối.
- Cold start Riva TTS sau restart có thể timeout; benchmark hiện chạy sau warm-up.
