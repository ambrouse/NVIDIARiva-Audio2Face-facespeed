# Release Readiness Evidence

Date: 2026-05-23

## Result

Pass. This folder is the single current evidence package for the FaceSpeed v0.3.0 release candidate.

## Runtime Under Test

| Service | Address |
| --- | --- |
| Frontend | `http://127.0.0.1:6310` |
| Backend | `http://127.0.0.1:8020` |
| Riva TTS | `127.0.0.1:50051` |
| Riva ASR | `127.0.0.1:50151` |
| Docling | `http://127.0.0.1:8005` |
| Embedding/rerank | `http://127.0.0.1:8006` |

## Evidence Map

| Path | Purpose |
| --- | --- |
| `demo/facespeed-release-demo.gif` | Smooth GitHub banner demo captured from the real browser app. |
| `app/01-home-voice-chat.png` | Product home: voice button, chat history, avatar panel, no landing clutter. |
| `app/02-chat-answer-avatar.png` | Provider-backed RAG answer, cited source, autoplay voice, replay icon, no audio bar. |
| `app/03-avatar-picker-popup.png` | Avatar profile and face/expression tuning popup. |
| `app/04-sources-popup.png` | PDF source/library popup. |
| `app/05-runtime-popup.png` | Runtime provider status popup. |
| `app/06-trace-popup.png` | Agent trace popup. |
| `app/07-atlas-calm-model-selected.png` | Alternate face profile selected. |
| `app/08-operations-page.png` | Provider-backed main path cards without mock/fallback status. |
| `app/09-activity-page.png` | Service log viewer. |
| `app/10-setup-page.png` | Machine readiness view. |
| `app/11-mobile-chat.png` | Mobile layout without horizontal overflow. |
| `pipeline/input-question.wav` | Test voice input artifact. |
| `pipeline/docling-output-answer.wav` | Riva voice answer artifact. |
| `pipeline/docling-avatar-3d-moving.webm` | Browser avatar video output. |
| `pipeline/docling-rag-evidence.pdf` | PDF used for Docling/RAG retrieval. |
| `pipeline/docling-report.json` | Provider-backed pipeline report. |
| `browser-report.json` | Browser QA metrics. |

## Browser Metrics

- Console errors: `0`
- Page errors: `0`
- Failed HTTP responses: `0`
- Visible audio controls: `0`
- Replay latest buttons: `1`
- Hidden audio elements: `1`
- Avatar mouth rig: `model-morphs`
- Mouth morph mesh count: `4`
- Jaw delta during audio: `0.373`
- Mobile overflow: `false`
- GIF size: `2.1 MB`, below the `100 MB` limit.

## Verification Commands

```bash
npm --prefix frontend test -- --run
npm --prefix frontend run build
PYTHONPATH=backend backend/.venv-linux/bin/python -m pytest backend/tests tests
node scripts/capture-release-demo.mjs
```
