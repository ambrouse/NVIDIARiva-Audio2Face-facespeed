# PDF CRUD va Agent Canvas

- Created: 2026-05-23 19:00
- Status: completed
- Plan: ../../plans/plan-pdf-crud-agent-canvas.md

## Pipeline RAG Hien Tai
1. User upload PDF.
2. Backend gui PDF sang Docling provider de parse thanh markdown.
3. Backend tach markdown thanh sections va chunks khoang 130 tu.
4. Embedding API tao vector cho tung chunk, luu vao `storage/rag/embeddings`.
5. Khi user hoi, backend embedding cau hoi va so cosine voi chunk vectors.
6. Chunk qua nguong `RAG_MIN_VECTOR_SCORE` duoc mo rong them chunk lien ke.
7. Rerank API sap xep lai ung vien.
8. Review agent chi pass neu confidence dau tien vuot `RAG_MIN_CONFIDENCE`.
9. Teacher agent ghep cau tra loi tu citation, chua co LLM sinh cau tra loi tu nhieu bang chung.
10. Riva TTS tao WAV, browser avatar dung viseme/timeline local de mo mieng.

## Vi Sao Cam Giac Hoat Dong Kem
- Cau tra loi hien la extractive template: cat ghep citation, khong co LLM reasoning/summarization that.
- Chunk page dang uoc luong theo section index/local index, khong phai page mapping chinh xac tu PDF.
- Vector threshold co the loai chunk lien quan neu embedding provider cho diem thap.
- Neu PDF scan/OCR kem, Docling markdown se nhieu ky tu loi, lam retrieval te.
- Trace hien tai chi la list text, khong giup user thay duong di giua agents/provider/database.

## Muc Tieu Thay Doi Lan Nay
- CRUD PDF context dong bo memory + JSON files.
- Trace canvas animated mo ta flow: User -> Lead -> Search -> Vector DB -> Rerank -> Review -> Teacher -> Riva/Avatar, co loop de xem lai.
- UI Sources quan ly PDF ro rang: upload, rename metadata, delete, refresh.

## Ket Qua
- Da them `PATCH /api/documents/{documentId}` de sua title, summary, language.
- Da them `DELETE /api/documents/{documentId}` de xoa document, embeddings, chunk embeddings trong memory va turns co citation tro toi document.
- Da xoa PDF vua upload `docling-rag-evidence.pdf` id `0987c3de69f08a20`.
- Trace modal da doi sang canvas animated co node agent/provider/database va luong particle loop.
- Sources modal co upload, refresh, edit, save, delete.

## Verify
- `backend/.venv-linux/bin/python -m pytest tests/backend/test_rag_api.py`: 7 passed.
- `npm --prefix frontend test -- --run`: 4 passed, jsdom co warning canvas getContext khong anh huong ket qua.
- `npm --prefix frontend run build`: pass, co Vite chunk-size warning hien co.
- Playwright desktop/mobile co screenshot trong `.cache/facespeed/evidence/pdf-crud-agent-canvas-evidence-2026-05-23/`.
