# Plan 04: Frontend Dashboard

## Mục tiêu

Hoàn thiện dashboard React/Vite để user chạy pipeline mock/NVIDIA có kiểm soát, xem trạng thái tài nguyên, logs, services, output audio/result và 3D face preview mà không gây tải server.

## Skill phải đọc trước khi làm

- `frontend-skill`
- `frontend-design-skills`
- `testing-skill`
- `security-skill`
- `documentation-skill`
- `logging-skill`

## Phạm vi

Làm:

1. Pipeline page UX.
2. Services/system/logs UI.
3. Resource warning UI.
4. Error/loading/empty states.
5. Frontend tests/build.
6. Manual localhost/VS Code forwarding verification.

Không làm:

- Không mở public network.
- Không polling quá dày.
- Không load 3D asset nặng mặc định.

## Cấu trúc frontend mục tiêu

```text
frontend/src/
  components/
    FaceViewer.tsx
    ResourceSummary.tsx
    ServiceCard.tsx
    LogViewer.tsx
  pages/
    PipelinePage.tsx
    ServicesPage.tsx
    LogsPage.tsx
    SystemPage.tsx
  services/
    api.ts
  styles/
    app.css
  utils/
```

Nếu repo hiện chưa đúng hoàn toàn, refactor vừa đủ, không over-engineer.

## UI contract

### Pipeline page

Hiển thị:

- Text input.
- Voice/language/profile/output mode.
- Run button.
- Job state timeline.
- Audio preview/link.
- A2F result metadata.
- 3D face fallback.
- Error state rõ.
- Mock/NVIDIA mode badge.

PASS nếu:

- Mock job golden path render đúng.
- Error từ backend hiển thị rõ.
- Button disable khi request đang chạy hoặc hard gate fail.

### System page

Hiển thị:

- Backend/frontend/Riva/A2F target ports.
- Port conflict status.
- RAM/commit/disk/GPU/VRAM snapshot nếu backend cung cấp.
- Docker summary nếu backend/script cung cấp.
- Suggested commands dạng copy/manual, không auto-run.

PASS nếu:

- Không trigger command nặng từ UI.
- Polling >= 5s hoặc manual refresh.

### Services page

Rules:

- Start/stop/restart real service phải có confirm và backend allowlist.
- Nếu chưa implement safe backend action, UI chỉ show hướng dẫn/manual.

ASK nếu:

- User muốn nút start/stop thật trong UI.

### Logs page

Rules:

- Tail limit default.
- Pause/resume autoscroll.
- No arbitrary path input.
- No secret display if backend redacts.

### 3D viewer

Rules:

- Procedural fallback lightweight.
- Lazy load model only if artifact URL exists.
- Error boundary/no crash if WebGL/model fails.

## Test plan

Commands:

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

Test cases:

1. Pipeline page renders input/run button.
2. Job success shows completed/audio/result.
3. Job error shows error box.
4. System warnings render hard gate fail.
5. Logs page empty/loading states.
6. FaceViewer fallback renders without model.

Manual verification:

1. Start backend on `127.0.0.1:8020` if safe.
2. Start frontend on `127.0.0.1:6210` if port free.
3. User forwards port using VS Code/Visual.
4. Create mock job.
5. Confirm UI output and no browser console fatal errors.

Manual verification is required before claiming UI complete. If not possible, mark BLOCKED/manual-not-run.

## Đánh giá output

PASS khi:

1. Tests/build pass.
2. Manual mock flow verified in browser or explicitly blocked.
3. UI states cover loading/error/empty/success.
4. Polling not too frequent.
5. No public bind.

ASK khi:

- Need visual/design decision.
- Need real service control buttons.
- Need auth because user wants LAN/public.

REDO khi:

- UI claims completed but no artifact/result.
- Error hidden from user.
- Frontend build fails.
- Polling causes high CPU/network.

## Docs/logs

- Update README/docs if run ports or UI flow changes.
- Log tests/manual verification in `logs/sessions/facespeed-safe-completion.md`.

## Close Comment

Status: PASS
Closed at: 2026-05-20 16:38
Evidence:
- Frontend API default now uses `http://127.0.0.1:8020`.
- Pipeline page includes local mock-safe badge, backend notice, voice/language/profile/output controls, char limit, state timeline and error/result states.
- System page shows localhost target ports and safe preflight commands.
- Service actions require browser confirmation.
- `npm --prefix frontend test`: 3 passed.
- `npm --prefix frontend run build`: PASS with existing FaceViewer chunk-size warning.
- Browser smoke launched backend/frontend on localhost only, created a mock job, verified Pipeline/System UI and captured `logs/runtime/frontend-phase04-smoke.png` with no console/page errors.
Log entry: `logs/sessions/facespeed-safe-completion.md` section `Phase 04 - Frontend Dashboard`
Next plan: `plans/plan-05-nvidia-container-setup.md`
Notes:
- Playwright Chromium was installed after user approval; local `.local-libs/usr/lib64/libasound.so.2` symlink was used for headless browser runtime.
- Dev servers started for verification were stopped after smoke test.
- NVIDIA real services were not started in this phase.
