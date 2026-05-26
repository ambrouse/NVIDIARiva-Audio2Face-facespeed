# Operations

Date: 2026-05-26

## Local Ports

| Service | Default |
| --- | --- |
| Nginx app proxy | `http://127.0.0.1:6300` |
| Frontend | `http://127.0.0.1:6310` |
| Backend | `http://127.0.0.1:6320` |
| Postgres | `127.0.0.1:6001` |
| Qdrant HTTP/gRPC | `127.0.0.1:6002/6003` |
| Audio2Face-3D optional gRPC/HTTP | `127.0.0.1:6040/6041` |
| Riva TTS | `127.0.0.1:6051` |
| Riva ASR | `127.0.0.1:6052` |
| Docling | `http://127.0.0.1:8005` |
| Embedding/rerank | `http://127.0.0.1:8006` |
| LLM judge/teacher | `http://127.0.0.1:8007/v1` |

Project-owned runtime ports must stay inside `6000-6500`. Port `6000` is avoided because it is already used by another local service on the current workstation.

Use `http://127.0.0.1:6300/` as the browser URL when working through an IDE or remote port forward. Nginx serves as the single browser-facing entry point: `/api/*` goes to backend `127.0.0.1:6320`, and all other app paths go to frontend `127.0.0.1:6310`. The nginx container is started by Docker Compose inside the `facespeed-riva-docker` tmux session.

Docling, embedding/rerank, and vLLM are existing provider services on this workstation. They are not browser-facing app ports and should stay on `8005`, `8006`, and `8007` unless those provider services move.

Riva TTS is serialized with `RIVA_TTS_MAX_CONCURRENCY=1` in `.env` to keep the local Riva postprocessor stable under multi-user voice tests.
Use `RIVA_SAMPLE_RATE_HZ=44100`, matching the local Riva TTS model rate, so benchmark traffic does not force postprocessor resampling.
Use `VOICE_CHAT_TTS_MAX_CHARS=150` for the spoken preview. Longer cited answers remain in chat text, but the audio preview is shortened to avoid local Riva/Triton streaming timeouts.

## Runtime Logs

Curated task logs are kept in `logs/`. Runtime logs are inspected through tmux sessions, especially `facespeed-riva-docker`, `facespeed-riva-backend`, and `facespeed-riva-frontend`.

```bash
tmux attach -t facespeed-riva-docker
tmux attach -t facespeed-riva-backend
tmux attach -t facespeed-riva-frontend
```

Disposable log files can still be cleaned with:

```bash
bash scripts/manage-logs.sh --status
bash scripts/manage-logs.sh --dry-run
bash scripts/manage-logs.sh --clean
```

## Evidence

Current release evidence:

```text
.cache/facespeed/evidence/release-readiness-2026-05-23/
```

README banner hiện tại là screenshot thật qua nginx:

```text
docs/assets/facespeed-readme-banner.png
```

Recreate the historical GIF banner:

```bash
node scripts/capture-release-demo.mjs
```

This writes:

- `.cache/facespeed/evidence/release-readiness-2026-05-23/demo/facespeed-release-demo.gif`
- `docs/assets/voice-rag-avatar-demo.gif`

## Verification

```bash
bash -n scripts/setup.sh
docker compose config --quiet
curl -fsS http://127.0.0.1:6300/api/rag/status
npm --prefix frontend test -- --run
npm --prefix frontend run build
backend/.venv-linux/bin/python -m pytest tests
```

## Cleanup

Safe cleanup targets:

- `frontend/dist/`
- `.pytest_cache/`
- `backend/.pytest_cache/`
- Python `__pycache__/`
- `logs/*.log`
- `logs/jobs/`
- `logs/runtime/`

Do not delete:

- `frontend/public/models/readyplayer-talk-arkit.glb`
- `docs/assets/facespeed-readme-banner.png`
- `docs/assets/voice-rag-avatar-demo.gif`
- current release evidence in `.cache/facespeed/evidence/release-readiness-2026-05-23/`
- project-local venv/node modules during an active QA session unless you intend to reinstall.
