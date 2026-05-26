# Frontend

React/Vite product UI for FaceSpeed.

## Main Screens

- Voice: chat history, hold-to-talk, RAG answer, replay-only voice playback, and 3D avatar.
- Operations: provider-backed runtime status for Riva ASR, Docling, embedding/rerank, and knowledge index.
- Activity: service log viewer.
- Setup: machine readiness checks.

## Important Paths

| Path | Purpose |
| --- | --- |
| `src/pages/PipelinePage.tsx` | Voice RAG product surface. |
| `src/components/FaceViewer.tsx` | Three.js avatar renderer, autoplay audio, replay button. |
| `src/services/api.ts` | Backend API client and contracts. |
| `src/styles/app.css` | Product UI styling. |
| `public/models/readyplayer-talk-arkit.glb` | Production-safe browser avatar model. |
| `../tests/frontend/App.test.tsx` | UI regression tests. |

## Commands

```bash
npm --prefix frontend install
npm --prefix frontend test -- --run
npm --prefix frontend run build
VITE_API_BASE_URL=http://127.0.0.1:6320 npm --prefix frontend run dev -- --host 127.0.0.1 --port 6310 --strictPort
```
