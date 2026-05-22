# Contributing

FaceSpeed is a local Voice RAG and 3D avatar product. Contributions should keep the main path direct: provider failure should surface as an error, not silently switch to a fake fallback.

## Development Setup

```bash
./setup.sh --setup
./setup.sh --run
```

Open `http://127.0.0.1:6310/`.

## Quality Gates

Run these before a pull request:

```bash
npm --prefix frontend test -- --run
npm --prefix frontend run build
PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests
bash setup.sh --check
```

For UI or pipeline changes, also capture release evidence:

```bash
node scripts/capture-release-demo.mjs
```

## Code Rules

- Keep code scoped and readable.
- Prefer existing project structure over new abstractions.
- Do not add fallback behavior to the RAG/voice main path.
- Delete unused assets, test folders, generated artifacts, and dead code.
- Keep secrets out of code, docs, screenshots, logs, and fixtures.

## Evidence Rules

- Current release evidence lives in `test/release-readiness-2026-05-23/`.
- Keep only useful screenshots, GIF/video, audio input/output, and short JSON reports.
- Do not commit raw runtime logs or duplicated evidence folders.

## Logs

Use:

```bash
bash scripts/manage-logs.sh --dry-run
bash scripts/manage-logs.sh --clean
```

Curated task logs live in `logs/plans/`. Runtime logs are disposable.
