# Scripts

Operational scripts for setup, verification, demos, and cleanup.

| Script | Purpose |
| --- | --- |
| `setup.sh` | Main setup/check/run entrypoint used by root `./setup.sh`. |
| `manage-logs.sh` | Shows and removes disposable runtime logs. |
| `capture-release-demo.mjs` | Captures the real browser app and writes the release GIF banner. |
| `install-playwright-local-libs.sh` | Installs local browser shared libraries when the host lacks them. |
| `provision-riva-asr-local.sh` | Provisions the separate local Riva ASR runtime. |
| `a2f3d_v3_pipeline.py` | Historical Audio2Face-3D proof asset pipeline. |

Run scripts from the repository root unless a script says otherwise.

`setup.sh --setup` creates `.env` from `.env.example` on a fresh clone, and `setup.sh --run`/`--setup-run` detach backend/frontend processes with PID files in `logs/runtime/`. Use `./setup.sh --stop` to stop project-owned local processes.
