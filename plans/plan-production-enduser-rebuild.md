# Plan: Production End-User Rebuild

- Created: 2026-05-22 14:40
- Updated: 2026-05-22 15:06
- Status: completed
- Related log: logs/plans/production-enduser-rebuild.md

## Goal
Rebuild FaceSpeed from a technical dashboard into a production-ready end-user avatar studio: clean source, reliable setup, polished UI, complete frontend QA evidence, and a README that presents the product honestly and clearly.

## Scope
- In:
  - Redesign the web experience as an end-user product, not an internal service dashboard.
  - Validate every visible frontend function with real browser interaction and one strong screenshot per function.
  - Clean unused folders/artifacts while keeping `.codex/skills/` and useful project docs/evidence.
  - Refactor obvious codebase noise without changing intended behavior.
  - Build one `setup.sh` that can check, install, warn, and run the full project on a fresh machine.
  - Redesign `README.md` using `readme-style`, including a GIF demo banner.
- Out:
  - Shipping real NVIDIA Audio2Face NIM if license/model access is still blocked.
  - Buying or generating a commercial avatar license.
  - Cloud deployment, auth, billing, multi-user storage, or public hosting.
  - Pushing commits unless explicitly requested.

## Skills
- plan-skill: phase tracking, close criteria, log linkage.
- frontend-skill: product UI, responsive behavior, visual polish, accessibility.
- testing-skill: real browser QA, evidence folder, one screenshot per function, hygiene.
- readme-style: product README structure, banner, badges, flow, accuracy notes.
- documentation-skill: setup/run docs and cleanup notes.
- security-skill: secret scan, env handling, safe setup behavior.
- backend-skill: setup script/backend contract sanity where needed.

## Research Notes
- HeyGen emphasizes a direct creator flow: pick/upload avatar, type script, choose voice/language, generate video, with trust numbers and clear output state.
- Synthesia frames the product as create/localize/manage/publish/engage, with avatar selection, script/outfit controls, enterprise trust, and video output management.
- Tavus positions around real-time human interaction, with a large face-to-face preview and developer/enterprise paths.
- Design direction for this repo: a focused "Speaking Avatar Studio" with preview-first layout, script composer, voice/avatar controls, generation status, output playback, and service/system health tucked behind support/settings instead of dominating the first screen.

## Phases
| Phase | Goal | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Audit current source, runtime, visible routes, generated artifacts, and cleanup candidates | completed | `logs/plans/production-enduser-rebuild.md` audit section |
| 2 | Define production UX IA and visual direction from research | completed | Research notes and studio IA in this plan/log |
| 3 | Redesign frontend into end-user avatar studio | completed | `test/release-readiness-2026-05-23/app/01-home-voice-chat.png` |
| 4 | Make every visible frontend function real and non-dead | completed | Evidence screenshots 01-06 and `browser-report.json` |
| 5 | Clean source tree and remove unused artifacts/folders safely | completed | Cleanup manifest in log and `git status` review |
| 6 | Refactor noisy code and stabilize frontend/backend contracts | completed | Unit/integration tests and browser QA passed |
| 7 | Build one-command `setup.sh` for fresh machine setup + run | completed | Root script, shell check, `--status`, `--run` |
| 8 | Rebuild README with GIF demo banner and operational docs | completed | `README.md` and `docs/assets/voice-rag-avatar-demo.gif` |
| 9 | Final full QA pass and evidence packaging | completed | `test/release-readiness-2026-05-23/` |

## Phase Details

### Phase 1: Audit
- Inventory current routes/pages: Pipeline, Services, Logs, System.
- Identify generated folders and artifacts: `dist`, evidence folders, cache/model search, outputs, logs, local RPM/libs, downloaded models.
- Mark keep/delete/ignore categories.
- Verify current runtime ports and service assumptions.

### Phase 2: UX Direction
- Convert product from "dashboard" to "studio":
  - Main screen: avatar preview, script composer, voice/avatar controls, generate button, output playback.
  - Secondary drawer/page: run history, service health, setup diagnostics.
  - Settings/support: Riva/A2F status, model source, container controls if still needed.
- Keep technical details available but not first-viewport dominant.
- Use real model/avatar media in first viewport.

### Phase 3: Frontend Redesign
- Rework layout, typography, colors, responsive states, and interactions using `frontend-skill`.
- Remove nested-card/dashboard heaviness.
- Add clear loading, empty, error, completed, and speaking states.
- Ensure mobile/tablet/desktop do not overflow and controls remain tappable.

### Phase 4: Function Completeness
- Visible functions must work or be removed/disabled with honest copy.
- Candidate functions to validate:
  - Generate speech + avatar animation.
  - Play output audio and animate face.
  - Change script text.
  - Change voice/language/profile/output mode if exposed.
  - View/download/open animation artifact if exposed.
  - Service health/status if exposed.
  - Logs if exposed.
  - System checks if exposed.
  - Setup/help links if exposed.

### Phase 5: Source Cleanup
- Keep:
  - `backend/`, `frontend/`, `scripts/`, `docs/`, `plans/`, `skills/`, `.codex/skills/`, essential tests, README, configs.
  - Useful public models required by current app.
- Review before deleting:
  - `frontend/dist/`, `test/*evidence*`, `.cache/`, `.local-libs/`, `.local-rpms/`, `outputs/`, old phase docs/logs.
- Do not delete user files or unrelated work.
- Add/update `.gitignore` for generated runtime artifacts.

### Phase 6: Code Cleanup
- Remove stale copy like `browser-viseme-v1`.
- Consolidate config names and ports.
- Split large frontend component if it improves maintainability.
- Keep model loading and timeline logic readable.
- Add tests around any refactored logic.

### Phase 7: Setup Script
- `setup.sh` must support:
  - `--check`: inspect Python, Node, npm, Docker, NVIDIA GPU, VRAM, RAM, disk, ports.
  - `--setup`: create venv, install backend/frontend dependencies, prepare local browser deps when possible, check model assets.
  - `--run`: start backend/frontend and use Riva if already available.
  - `--setup-run`: one command for fresh machine.
  - `--stop`: stop project-owned processes/containers only.
  - `--status`: show ports, PIDs, containers, health endpoints.
- Hardware/resource gates warn by default, not block, unless a destructive/heavy action would be unsafe.
- If NGC/API/license key is needed, prompt clearly and never print secrets.
- If dependency install needs sudo/root, explain exact missing package and continue with fallback where possible.

### Phase 8: README
- Follow `readme-style`:
  - Product hero with GIF demo banner.
  - Badges and quick navigation.
  - Short overview and honest capability matrix.
  - Mermaid system flow.
  - One-command setup/run.
  - Hardware support and hạ tầng notes.
  - Repository map.
  - Evidence/demo section.
  - Accuracy notes and known limitations.
- Generate or record a short GIF demo from real app interaction.

### Phase 9: Final QA
- Create `test/release-readiness-2026-05-23/`.
- One best screenshot per function/state, no duplicates.
- Root README with scope, run environment, test results, blockers.
- Hygiene:
  - duplicate image hash scan.
  - secret pattern scan.
  - missing README scan.
  - verify no temporary raw dumps unless justified.

## Verification
- Backend:
  - `PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests`
  - API health and job creation through HTTP.
- Frontend:
  - `npm --prefix frontend test -- --run`
  - `npm --prefix frontend run build`
  - Playwright/E2E on desktop and mobile viewport.
  - Visual proof for each function in evidence folder.
- Setup:
  - `bash setup.sh --check`
  - `bash setup.sh --setup --dry-run` if implemented.
  - `bash setup.sh --status`
  - `bash setup.sh --run` or `--setup-run` on current machine.
- Docs:
  - README links/assets render.
  - GIF banner exists and is generated from real app.
  - Secret scan across README/evidence/logs.

## Close Criteria
- Product opens from one documented command on the target machine.
- First screen is end-user avatar studio, not service dashboard.
- No visible frontend function is decorative/dead.
- Every visible function has one reviewed screenshot proving the output/state.
- Source tree is cleaned and generated artifacts are ignored or intentionally documented.
- `setup.sh` handles checks, setup, run, stop, and status with safe warnings.
- README matches `readme-style` and includes a real GIF demo banner.
- All agreed tests pass, or remaining blockers are documented with evidence and concrete next actions.
