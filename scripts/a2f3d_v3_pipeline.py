#!/usr/bin/env python3
"""Prepare and verify a local NVIDIA Audio2Face-3D v3.0 mesh pipeline."""

from __future__ import annotations

import argparse
import base64
import json
import math
import shutil
import struct
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
A2F_MODEL_DIR = ROOT / ".cache/nvidia/audio2face-v3.0"
MAYA_FACE_PATH = ROOT / ".cache/nvidia/maya-ace-assets/james_arkit_v3.ma"
SAMPLE_AUDIO = ROOT / ".cache/nvidia/Audio2Face-3D-Samples/example_audio/Mark_neutral.wav"
OUTPUT_DIR = ROOT / "outputs/a2f3d-v3"
PUBLIC_MODEL = ROOT / "frontend/public/models/a2f-james-v3.glb"
PROOF_IMAGE = OUTPUT_DIR / "a2f3d-v3-james-speaking-proof.png"
PROOF_TIMELINE = OUTPUT_DIR / "a2f3d-v3-james-timeline.json"
PROOF_AUDIO = OUTPUT_DIR / "mark-neutral-16khz.wav"
SKIN_VERTEX_COUNT = 24002
SKIN_FLOAT_COUNT = SKIN_VERTEX_COUNT * 3
TONGUE_FLOAT_COUNT = 5602 * 3


def require_file(path: Path, hint: str) -> None:
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"Missing {path}. {hint}")


def parse_maya_head_faces(path: Path) -> np.ndarray:
    """Parse the first head mesh topology from a Maya ASCII file."""
    require_file(path, "Download Maya-ACE LFS assets first.")
    edges: list[tuple[int, int]] = []
    faces: list[list[int]] = []
    in_head = False
    mode: str | None = None

    for raw_line in path.read_text(encoding="latin-1").splitlines():
        line = raw_line.strip().rstrip(";")
        if line.startswith('createNode mesh -n "c_headWatertight_hiShapeOrig"'):
            in_head = True
            continue
        if in_head and line.startswith("createNode mesh -n ") and "c_headWatertight_hiShapeOrig" not in line:
            break
        if not in_head:
            continue

        if '".ed[' in line:
            mode = "edges"
            payload = line.split("]", 1)[1]
        elif '".fc[' in line:
            mode = "faces"
            payload = ""
        elif line.startswith("setAttr ") and mode:
            mode = None
            payload = ""
        else:
            payload = line

        if mode == "edges" and payload:
            values = [int(value) for value in payload.split() if _is_int(value)]
            for index in range(0, len(values) - 2, 3):
                edges.append((values[index], values[index + 1]))
        elif mode == "faces" and payload.startswith("f "):
            tokens = payload.split()
            count = int(tokens[1])
            edge_refs = [int(value) for value in tokens[2 : 2 + count]]
            vertices = []
            for edge_ref in edge_refs:
                if edge_ref >= 0:
                    vertices.append(edges[edge_ref][0])
                else:
                    vertices.append(edges[abs(edge_ref) - 1][1])
            faces.append(vertices)

    if not edges or not faces:
        raise SystemExit(f"Could not parse head topology from {path}")

    triangles: list[tuple[int, int, int]] = []
    for face in faces:
        for index in range(1, len(face) - 1):
            triangles.append((face[0], face[index], face[index + 1]))
    return np.asarray(triangles, dtype=np.uint32)


def _is_int(value: str) -> bool:
    return value.lstrip("-").isdigit()


def load_blendshape_data(actor: str = "James") -> tuple[np.ndarray, dict[str, np.ndarray], list[str]]:
    npz_path = A2F_MODEL_DIR / f"bs_skin_{actor}.npz"
    require_file(npz_path, "Run the v3.0 model download first.")
    data = np.load(npz_path, allow_pickle=False)
    neutral = np.asarray(data["neutral"], dtype=np.float32)
    names = [name.decode("utf-8") if isinstance(name, bytes) else str(name) for name in data["poseNames"]]
    names = [name for name in names if name != "neutral" and name in data]
    deltas = {name: np.asarray(data[name], dtype=np.float32) for name in names}
    return neutral, deltas, names


def compute_vertex_normals(vertices: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    normals = np.zeros_like(vertices, dtype=np.float32)
    tri_vertices = vertices[triangles]
    face_normals = np.cross(tri_vertices[:, 1] - tri_vertices[:, 0], tri_vertices[:, 2] - tri_vertices[:, 0])
    lengths = np.linalg.norm(face_normals, axis=1)
    face_normals[lengths > 0] /= lengths[lengths > 0, None]
    for corner in range(3):
        np.add.at(normals, triangles[:, corner], face_normals)
    lengths = np.linalg.norm(normals, axis=1)
    normals[lengths > 0] /= lengths[lengths > 0, None]
    return normals.astype(np.float32)


def write_glb(path: Path, vertices: np.ndarray, triangles: np.ndarray, deltas: dict[str, np.ndarray], names: list[str]) -> None:
    normals = compute_vertex_normals(vertices, triangles)
    chunks: list[bytes] = []
    buffer_views = []
    accessors = []

    def add_buffer(array: np.ndarray, target: int | None, component_type: int, accessor_type: str, minmax: bool = False) -> int:
        byte_offset = sum(len(chunk) for chunk in chunks)
        data = np.ascontiguousarray(array).tobytes()
        chunks.append(data + (b"\x00" * ((4 - len(data) % 4) % 4)))
        buffer_view_index = len(buffer_views)
        view = {"buffer": 0, "byteOffset": byte_offset, "byteLength": len(data)}
        if target is not None:
            view["target"] = target
        buffer_views.append(view)
        accessor = {
            "bufferView": buffer_view_index,
            "componentType": component_type,
            "count": int(array.shape[0]),
            "type": accessor_type,
        }
        if minmax:
            accessor["min"] = array.min(axis=0).astype(float).tolist()
            accessor["max"] = array.max(axis=0).astype(float).tolist()
        accessors.append(accessor)
        return len(accessors) - 1

    position_accessor = add_buffer(vertices.astype(np.float32), 34962, 5126, "VEC3", True)
    normal_accessor = add_buffer(normals, 34962, 5126, "VEC3")
    index_accessor = add_buffer(triangles.reshape(-1).astype(np.uint16), 34963, 5123, "SCALAR")
    target_accessors = [add_buffer(deltas[name].astype(np.float32), 34962, 5126, "VEC3", True) for name in names]

    binary = b"".join(chunks)
    gltf = {
        "asset": {"version": "2.0", "generator": "FaceSpeed A2F3D v3 asset pipeline"},
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": buffer_views,
        "accessors": accessors,
        "materials": [
            {
                "name": "warm skin",
                "doubleSided": True,
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.78, 0.54, 0.42, 1.0],
                    "roughnessFactor": 0.58,
                    "metallicFactor": 0.0,
                },
            }
        ],
        "meshes": [
            {
                "name": "NVIDIA_James_A2F3D_v3_skin",
                "primitives": [
                    {
                        "attributes": {"POSITION": position_accessor, "NORMAL": normal_accessor},
                        "indices": index_accessor,
                        "material": 0,
                        "targets": [{"POSITION": accessor} for accessor in target_accessors],
                    }
                ],
                "weights": [0.0 for _ in target_accessors],
                "extras": {"targetNames": names},
            }
        ],
        "nodes": [{"name": "NVIDIA_James_A2F3D_v3_face", "mesh": 0}],
        "scenes": [{"nodes": [0]}],
        "scene": 0,
    }
    json_bytes = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    json_bytes += b" " * ((4 - len(json_bytes) % 4) % 4)
    glb = (
        b"glTF"
        + struct.pack("<II", 2, 12 + 8 + len(json_bytes) + 8 + len(binary))
        + struct.pack("<I4s", len(json_bytes), b"JSON")
        + json_bytes
        + struct.pack("<I4s", len(binary), b"BIN\x00")
        + binary
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(glb)


def run_v3_inference(audio_path: Path) -> np.ndarray:
    import onnxruntime as ort

    require_file(A2F_MODEL_DIR / "network.onnx", "Download nvidia/Audio2Face-3D-v3.0 first.")
    with wave.open(str(audio_path), "rb") as wav_file:
        if wav_file.getnchannels() != 1 or wav_file.getsampwidth() != 2 or wav_file.getframerate() != 16000:
            raise SystemExit("Proof audio must be mono PCM-16 WAV at 16 kHz.")
        samples = np.frombuffer(wav_file.readframes(16000), dtype="<i2").astype(np.float32) / 32768.0
    window = np.pad(samples[:16000], (0, max(0, 16000 - len(samples))))[:16000][None, :]
    identity = np.array([[0.0, 1.0, 0.0]], dtype=np.float32)
    emotion = np.zeros((1, 30, 10), dtype=np.float32)
    emotion[..., 6] = 0.25
    latents = np.zeros((2, 2, 1, 256), dtype=np.float32)
    noise = np.random.default_rng(7).standard_normal((1, 3, 60, 88831), dtype=np.float32) * 0.25
    session = ort.InferenceSession(str(A2F_MODEL_DIR / "network.onnx"), providers=["CPUExecutionProvider"])
    prediction, _output_latents = session.run(
        None,
        {
            "window": window.astype(np.float32),
            "identity": identity,
            "emotion": emotion,
            "input_latents": latents,
            "noise": noise,
        },
    )
    return np.asarray(prediction[0], dtype=np.float32)


def solve_blendshape_timeline(prediction: np.ndarray, deltas: dict[str, np.ndarray], names: list[str]) -> list[dict]:
    mask = np.load(A2F_MODEL_DIR / "bs_skin_James.npz", allow_pickle=False)["frontalMask"]
    matrix = np.stack([deltas[name][mask].reshape(-1) for name in names], axis=1)
    frames = []
    # NVIDIA's diffusion model emits 60 frames; center 30 are the usable half-second window.
    for output_index, frame_index in enumerate(range(15, 45)):
        target = prediction[frame_index, :SKIN_FLOAT_COUNT].reshape(SKIN_VERTEX_COUNT, 3)[mask].reshape(-1)
        weights, *_ = np.linalg.lstsq(matrix, target, rcond=None)
        weights = np.clip(weights, 0.0, 1.0)
        blend_shapes = {name: round(float(weight), 5) for name, weight in zip(names, weights)}
        frames.append(
            {
                "t": round(output_index / 30, 3),
                "jawOpen": round(float(blend_shapes.get("jawOpen", 0.0)), 3),
                "mouthWide": round(
                    float((blend_shapes.get("mouthStretchLeft", 0.0) + blend_shapes.get("mouthStretchRight", 0.0)) / 2),
                    3,
                ),
                "mouthSmile": round(
                    float((blend_shapes.get("mouthSmileLeft", 0.0) + blend_shapes.get("mouthSmileRight", 0.0)) / 2),
                    3,
                ),
                "blendShapes": blend_shapes,
            }
        )
    return frames


def render_proof_image(vertices_neutral: np.ndarray, generated_vertices: np.ndarray, triangles: np.ndarray, path: Path) -> None:
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), (5, 10, 18))
    draw = ImageDraw.Draw(image)
    render_mesh(draw, vertices_neutral, triangles, (0, 0, width // 2, height), "neutral mesh")
    render_mesh(draw, generated_vertices, triangles, (width // 2, 0, width, height), "A2F v3.0 audio frame")
    image.save(path)


def render_mesh(draw: ImageDraw.ImageDraw, vertices: np.ndarray, triangles: np.ndarray, box: tuple[int, int, int, int], label: str) -> None:
    x0, y0, x1, y1 = box
    verts = vertices.copy()
    center = verts.mean(axis=0)
    verts -= center
    angle = math.radians(-10)
    rotation = np.array(
        [[math.cos(angle), 0, math.sin(angle)], [0, 1, 0], [-math.sin(angle), 0, math.cos(angle)]],
        dtype=np.float32,
    )
    verts = verts @ rotation.T
    scale = min((x1 - x0) * 0.72 / (np.ptp(verts[:, 0]) or 1), (y1 - y0) * 0.78 / (np.ptp(verts[:, 1]) or 1))
    points = np.empty((len(verts), 3), dtype=np.float32)
    points[:, 0] = x0 + (x1 - x0) / 2 + verts[:, 0] * scale
    points[:, 1] = y0 + (y1 - y0) / 2 - verts[:, 1] * scale
    points[:, 2] = verts[:, 2]
    tri_points = points[triangles]
    depths = tri_points[:, :, 2].mean(axis=1)
    light = np.array([0.25, 0.35, 0.9], dtype=np.float32)
    light /= np.linalg.norm(light)
    order = np.argsort(depths)
    for tri_index in order:
        tri = tri_points[tri_index]
        v0, v1, v2 = verts[triangles[tri_index]]
        normal = np.cross(v1 - v0, v2 - v0)
        normal_length = np.linalg.norm(normal)
        if normal_length == 0:
            continue
        normal /= normal_length
        shade = max(0.18, float(np.dot(normal, light)) * 0.75 + 0.35)
        color = tuple(int(channel * shade) for channel in (196, 139, 112))
        polygon = [(float(p[0]), float(p[1])) for p in tri]
        draw.polygon(polygon, fill=color)
    draw.rectangle((x0 + 24, y0 + 24, x0 + 360, y0 + 70), fill=(15, 23, 42))
    draw.text((x0 + 40, y0 + 38), label, fill=(226, 232, 240), font=ImageFont.load_default())


def write_timeline(frames: list[dict], path: Path) -> None:
    timeline = {
        "engine": "nvidia-audio2face-3d-v3-onnx",
        "status": "completed",
        "profile": "james-v3",
        "outputMode": "preview",
        "fps": 30,
        "model": "nvidia/Audio2Face-3D-v3.0",
        "audio": str(PROOF_AUDIO.relative_to(ROOT)),
        "modelAsset": str(PUBLIC_MODEL.relative_to(ROOT)),
        "frames": frames,
    }
    path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")


def build_assets() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    require_file(SAMPLE_AUDIO, "Clone NVIDIA Audio2Face-3D-Samples or provide a 16 kHz WAV.")
    shutil.copyfile(SAMPLE_AUDIO, PROOF_AUDIO)
    neutral, deltas, names = load_blendshape_data("James")
    triangles = parse_maya_head_faces(MAYA_FACE_PATH)
    write_glb(PUBLIC_MODEL, neutral, triangles, deltas, names)
    prediction = run_v3_inference(PROOF_AUDIO)
    np.savez_compressed(OUTPUT_DIR / "a2f3d-v3-james-real-prediction.npz", prediction=prediction)
    frames = solve_blendshape_timeline(prediction, deltas, names)
    write_timeline(frames, PROOF_TIMELINE)
    best_frame = max(range(15, 45), key=lambda index: float(np.linalg.norm(prediction[index, :SKIN_FLOAT_COUNT])))
    generated_vertices = neutral + prediction[best_frame, :SKIN_FLOAT_COUNT].reshape(SKIN_VERTEX_COUNT, 3)
    render_proof_image(neutral, generated_vertices, triangles, PROOF_IMAGE)
    print(json.dumps({
        "glb": str(PUBLIC_MODEL),
        "proofImage": str(PROOF_IMAGE),
        "timeline": str(PROOF_TIMELINE),
        "audio": str(PROOF_AUDIO),
        "triangles": int(len(triangles)),
        "blendshapes": len(names),
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-assets", action="store_true", help="Export GLB, run v3.0 ONNX proof inference, and render proof PNG.")
    args = parser.parse_args()
    if args.build_assets:
        build_assets()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
