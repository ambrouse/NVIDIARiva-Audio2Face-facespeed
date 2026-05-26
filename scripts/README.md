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

`setup.sh --setup` creates `.env` from `.env.example` on a fresh clone. `setup.sh --run`/`--setup-run` run the project in tmux sessions named `facespeed-riva-docker`, `facespeed-riva-tts`, `facespeed-riva-asr`, `facespeed-riva-backend`, and `facespeed-riva-frontend`. The Docker session includes nginx on `127.0.0.1:6300`, which proxies frontend and backend through one port. Use `./setup.sh --stop` to stop project-owned tmux sessions, local processes, and containers.
