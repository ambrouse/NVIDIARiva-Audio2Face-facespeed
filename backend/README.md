# Backend

FastAPI backend for FaceSpeed Voice RAG.

## Main Responsibilities

- PDF upload and Docling parsing.
- Embedding search and rerank through the configured provider service.
- Riva ASR transcription and Riva TTS voice output.
- Cited answer assembly and browser avatar timeline artifacts.
- Runtime status, service logs, artifacts, and machine checks.

## Important Paths

| Path | Purpose |
| --- | --- |
| `src/main.py` | FastAPI app and router registration. |
| `src/config.py` | Environment-driven settings. |
| `src/routes/rag.py` | Voice RAG and document APIs. |
| `src/services/rag_service.py` | Main RAG orchestration path. |
| `src/services/docling_client.py` | Docling provider client. |
| `src/services/embedding_client.py` | Embedding/rerank provider client. |
| `tests/` | Backend API and service tests. |

## Test

```bash
backend/.venv-linux/bin/python -m pytest tests
```
