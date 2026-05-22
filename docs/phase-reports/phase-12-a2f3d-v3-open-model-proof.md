# Phase 12: Audio2Face-3D v3.0 Open Model Proof

Date: 2026-05-22

## Result

- Downloaded `nvidia/Audio2Face-3D-v3.0` open model files into `.cache/nvidia/audio2face-v3.0`.
- Downloaded the real NVIDIA Maya-ACE James v3 ARKit mesh from Git LFS into `.cache/nvidia/maya-ace-assets`.
- Parsed the Maya mesh topology and exported a browser proof GLB during this phase:
  - `frontend/public/models/a2f-james-v3.glb` was later removed from the production frontend because browser QA showed it did not meet the visual quality bar.
  - 24,002 vertices
  - 48,000 triangles
  - 52 ARKit skin morph targets
- Ran real ONNX Runtime inference with `network.onnx` on NVIDIA sample audio:
  - `outputs/a2f3d-v3/mark-neutral-16khz.wav`
  - `outputs/a2f3d-v3/a2f3d-v3-james-real-prediction.npz`
- Solved A2F geometry output back to 52 ARKit blendshape weights:
  - `outputs/a2f3d-v3/a2f3d-v3-james-timeline.json`
- Rendered a non-browser proof image directly from the mesh and A2F v3.0 output:
  - `outputs/a2f3d-v3/a2f3d-v3-james-speaking-proof.png`

## Reproduce

Install asset/proof dependencies in the backend venv:

```bash
backend/.venv-linux/bin/python -m pip install -r scripts/requirements-a2f3d-v3.txt
```

Then rebuild the GLB, timeline, and proof image:

```bash
backend/.venv-linux/bin/python scripts/a2f3d_v3_pipeline.py --build-assets
```

## Notes

- The v3.0 model output is geometry: `skin_size=72006`, `tongue_size=16806`, `jaw_size=15`, `eyes_size=4`.
- The GLB uses the NVIDIA James v3 topology and the v3.0 `bs_skin_James.npz` ARKit deltas.
- The proof image is rendered from mesh triangles, not captured from the web UI.
- Ready Player Me was not used because this host could not resolve `readyplayer.me` / `models.readyplayer.me` during local download.
