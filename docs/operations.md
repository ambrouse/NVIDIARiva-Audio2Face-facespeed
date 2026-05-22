# Operations

Date: 2026-05-23

## Local Ports

| Service | Default |
| --- | --- |
| Frontend | `http://127.0.0.1:6310` |
| Backend | `http://127.0.0.1:8020` |
| Riva TTS | `127.0.0.1:50051` |
| Riva ASR | `127.0.0.1:50151` |
| Docling | `http://127.0.0.1:8005` |
| Embedding/rerank | `http://127.0.0.1:8006` |
| Audio2Face-3D optional gRPC | `127.0.0.1:8040` |

## Runtime Logs

Curated task logs are kept in `logs/plans/`. Runtime logs are disposable and ignored by git.

```bash
bash scripts/manage-logs.sh --status
bash scripts/manage-logs.sh --dry-run
bash scripts/manage-logs.sh --clean
```

## Evidence

Current release evidence:

```text
test/release-readiness-2026-05-23/
```

Recreate the GIF banner:

```bash
node scripts/capture-release-demo.mjs
```

This writes:

- `test/release-readiness-2026-05-23/demo/facespeed-release-demo.gif`
- `docs/assets/voice-rag-avatar-demo.gif`

## Verification

```bash
bash setup.sh --check
npm --prefix frontend test -- --run
npm --prefix frontend run build
PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests
node scripts/capture-release-demo.mjs
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
- `docs/assets/voice-rag-avatar-demo.gif`
- current release evidence in `test/release-readiness-2026-05-23/`
- project-local venv/node modules during an active QA session unless you intend to reinstall.
