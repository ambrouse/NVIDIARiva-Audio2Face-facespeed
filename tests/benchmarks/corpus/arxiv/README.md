# arXiv Corpus

Thư mục này chứa PDF arXiv dùng để tạo benchmark RAG Voice.

File quan trọng:

| File | Nội dung |
| --- | --- |
| `metadata.json` | Danh sách PDF, tiêu đề, URL, thời gian tải và đường dẫn local. |
| `ingest-results.json` | Kết quả ingest/index nếu có từ lần benchmark gần nhất. |
| `*.pdf` | PDF nguồn để parse, chunk và truy xuất. |

Snapshot hiện tại có 102 PDF trên disk; benchmark matrix ngày 2026-05-25 dùng 100 PDF và 11,022 chunk.
