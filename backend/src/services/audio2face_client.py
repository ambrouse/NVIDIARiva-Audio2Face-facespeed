import asyncio
import json
import math
from pathlib import Path
import struct
import wave

import httpx

from src.config import Settings


class Audio2FaceClient:
    def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path, text: str = "") -> Path:
        raise NotImplementedError


class MockAudio2FaceClient(Audio2FaceClient):
    def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path, text: str = "") -> Path:
        resultPath.parent.mkdir(parents=True, exist_ok=True)
        durationSeconds, envelope = self._audioEnvelope(audioPath, fps=60)
        result = self._buildBrowserVisemeTimeline(durationSeconds, profile, outputMode, envelope, text)
        resultPath.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return resultPath

    def _buildBrowserVisemeTimeline(
        self,
        durationSeconds: float,
        profile: str,
        outputMode: str,
        envelope: list[float] | None = None,
        text: str = "",
    ) -> dict:
        fps = 60
        frameCount = max(2, int(durationSeconds * fps) + 1)
        frames = []
        smoothEnergy = envelope[0] if envelope else 0.0
        smoothBlendShapes: dict[str, float] = {}
        visemes = self._textVisemes(text)
        speechProgress = self._speechProgress(envelope)
        for index in range(frameCount):
            t = round(index / fps, 3)
            envelopeIndex = min(len(envelope) - 1, max(0, int(index * (len(envelope) / frameCount)))) if envelope else 0
            if envelope:
                targetEnergy = envelope[envelopeIndex]
            else:
                syllable = 0.5 + 0.5 * math.sin((t * 4.4) * math.tau)
                phrase = 0.72 + 0.28 * math.sin((t * 0.85) * math.tau + 0.6)
                targetEnergy = max(0.0, min(1.0, (syllable**1.6) * phrase))
            attack = 0.26 if targetEnergy > smoothEnergy else 0.18
            smoothEnergy += (targetEnergy - smoothEnergy) * attack
            easedEnergy = smoothEnergy**0.72
            microMotion = 0.5 + 0.5 * math.sin((t * 7.2) * math.tau + 0.4)
            progress = speechProgress[envelopeIndex] if speechProgress else t / max(0.001, durationSeconds)
            visemeShapes = self._sampleVisemeShapes(visemes, progress)
            targetBlendShapes = self._energyScaledBlendShapes(visemeShapes, easedEnergy, microMotion)
            smoothBlendShapes = (
                targetBlendShapes
                if not smoothBlendShapes
                else self._mixShapes(smoothBlendShapes, targetBlendShapes, 0.3)
            )
            blendShapes = smoothBlendShapes
            jawOpen = max(0.02, min(0.64, blendShapes["jawOpen"]))
            mouthWide = max(0.11, min(0.56, (blendShapes["mouthStretchLeft"] + blendShapes["mouthStretchRight"]) / 2))
            mouthSmile = max(0.02, min(0.18, (blendShapes["mouthSmileLeft"] + blendShapes["mouthSmileRight"]) / 2))
            frames.append(
                {
                    "t": t,
                    "jawOpen": round(jawOpen, 3),
                    "mouthWide": round(mouthWide, 3),
                    "mouthSmile": round(mouthSmile, 3),
                    "blendShapes": {key: round(value, 5) for key, value in blendShapes.items()},
                }
            )
        return {
            "engine": "browser-viseme-v2",
            "status": "completed",
            "profile": profile,
            "outputMode": outputMode,
            "durationSeconds": round(durationSeconds, 3),
            "fps": fps,
            "channels": ["jawOpen", "mouthWide", "mouthSmile", "blendShapes"],
            "frames": frames,
        }

    def _audioEnvelope(self, audioPath: Path, fps: int = 60) -> tuple[float, list[float]]:
        try:
            with wave.open(str(audioPath), "rb") as wavFile:
                channels = wavFile.getnchannels()
                sampleWidth = wavFile.getsampwidth()
                sampleRate = wavFile.getframerate()
                frameCount = wavFile.getnframes()
                if channels != 1 or sampleWidth != 2 or sampleRate <= 0 or frameCount <= 0:
                    return self._audioDurationSeconds(audioPath), []
                payload = wavFile.readframes(frameCount)
        except wave.Error:
            return 1.5, []

        samples = struct.unpack("<" + "h" * (len(payload) // 2), payload)
        windowSize = max(1, int(sampleRate / fps))
        rmsValues: list[float] = []
        for offset in range(0, len(samples), windowSize):
            window = samples[offset : offset + windowSize]
            if not window:
                continue
            rmsValues.append(math.sqrt(sum(sample * sample for sample in window) / len(window)) / 32768.0)

        if not rmsValues:
            return frameCount / sampleRate, []

        sortedRms = sorted(rmsValues)
        floor = sortedRms[min(len(sortedRms) - 1, max(0, int(len(sortedRms) * 0.12)))]
        ceiling = sortedRms[min(len(sortedRms) - 1, max(0, int(len(sortedRms) * 0.92)))]
        span = max(0.0001, ceiling - floor)
        envelope = [max(0.0, min(1.0, max(0.0, (value - floor) / span) ** 0.62)) for value in rmsValues]
        return frameCount / sampleRate, envelope

    def _speechProgress(self, envelope: list[float]) -> list[float]:
        if not envelope:
            return []
        weights = [0.012 + max(0.0, value - 0.08) ** 1.35 for value in envelope]
        total = sum(weights)
        if total <= 0:
            return [index / max(1, len(envelope) - 1) for index in range(len(envelope))]
        running = 0.0
        progress = []
        for weight in weights:
            running += weight
            progress.append(max(0.0, min(1.0, running / total)))
        progress[0] = 0.0
        progress[-1] = 1.0
        return progress

    def _textVisemes(self, text: str) -> list[str]:
        value = "".join(character.lower() if character.isalnum() else " " for character in text)
        collapsed = " ".join(value.split())
        if not collapsed:
            return ["rest", "open", "rest"]
        visemes: list[str] = []
        for character in collapsed:
            if character in "mbp":
                visemes.extend(["closed", "closed"])
            elif character in "fv":
                visemes.append("teeth")
            elif character in "ouwq":
                visemes.extend(["round", "round"])
            elif character in "ae":
                visemes.extend(["open", "open"])
            elif character in "iy":
                visemes.extend(["wide", "wide"])
            elif character in "r":
                visemes.append("roundSoft")
            elif character in "tdnlszxcjkg":
                visemes.append("narrow")
            elif character == " ":
                visemes.append("rest")
            else:
                visemes.append("mid")
        return visemes or ["rest", "open", "rest"]

    def _sampleVisemeShapes(self, visemes: list[str], progress: float) -> dict[str, float]:
        if not visemes:
            return self._visemeShape("rest")
        position = max(0.0, min(0.999, progress)) * (len(visemes) - 1)
        leftIndex = int(position)
        rightIndex = min(len(visemes) - 1, leftIndex + 1)
        amount = position - leftIndex
        amount = amount * amount * (3 - 2 * amount)
        currentShape = self._mixShapes(self._visemeShape(visemes[leftIndex]), self._visemeShape(visemes[rightIndex]), amount)
        previousShape = self._visemeShape(visemes[max(0, leftIndex - 1)])
        nextShape = self._visemeShape(visemes[min(len(visemes) - 1, rightIndex + 1)])
        coarticulated = self._mixShapes(currentShape, previousShape, 0.08 * (1 - amount))
        return self._mixShapes(coarticulated, nextShape, 0.08 * amount)

    def _visemeShape(self, viseme: str) -> dict[str, float]:
        base = {
            "jawOpen": 0.08,
            "jawForward": 0.01,
            "mouthClose": 0.0,
            "mouthFunnel": 0.02,
            "mouthPucker": 0.01,
            "mouthSmileLeft": 0.04,
            "mouthSmileRight": 0.04,
            "mouthStretchLeft": 0.18,
            "mouthStretchRight": 0.18,
            "mouthLowerDownLeft": 0.04,
            "mouthLowerDownRight": 0.04,
            "mouthUpperUpLeft": 0.02,
            "mouthUpperUpRight": 0.02,
            "mouthShrugLower": 0.015,
            "mouthShrugUpper": 0.01,
            "mouthPressLeft": 0.0,
            "mouthPressRight": 0.0,
            "tongueOut": 0.0,
        }
        variants = {
            "rest": {"jawOpen": 0.025, "mouthClose": 0.04, "mouthStretchLeft": 0.12, "mouthStretchRight": 0.12},
            "closed": {"jawOpen": 0.015, "mouthClose": 0.58, "mouthPressLeft": 0.28, "mouthPressRight": 0.28, "mouthStretchLeft": 0.08, "mouthStretchRight": 0.08},
            "teeth": {"jawOpen": 0.18, "mouthStretchLeft": 0.38, "mouthStretchRight": 0.37, "mouthUpperUpLeft": 0.13, "mouthUpperUpRight": 0.12},
            "round": {"jawOpen": 0.28, "mouthFunnel": 0.42, "mouthPucker": 0.34, "mouthStretchLeft": 0.1, "mouthStretchRight": 0.1},
            "roundSoft": {"jawOpen": 0.2, "mouthFunnel": 0.28, "mouthPucker": 0.2, "mouthStretchLeft": 0.14, "mouthStretchRight": 0.14},
            "open": {"jawOpen": 0.56, "mouthLowerDownLeft": 0.32, "mouthLowerDownRight": 0.31, "mouthUpperUpLeft": 0.12, "mouthUpperUpRight": 0.12, "mouthStretchLeft": 0.26, "mouthStretchRight": 0.25},
            "wide": {"jawOpen": 0.24, "mouthStretchLeft": 0.5, "mouthStretchRight": 0.48, "mouthSmileLeft": 0.11, "mouthSmileRight": 0.1},
            "narrow": {"jawOpen": 0.15, "mouthStretchLeft": 0.28, "mouthStretchRight": 0.27, "tongueOut": 0.035},
            "mid": {"jawOpen": 0.24, "mouthStretchLeft": 0.24, "mouthStretchRight": 0.23},
        }
        base.update(variants.get(viseme, {}))
        return base

    def _mixShapes(self, left: dict[str, float], right: dict[str, float], amount: float) -> dict[str, float]:
        keys = set(left) | set(right)
        return {key: left.get(key, 0.0) + (right.get(key, 0.0) - left.get(key, 0.0)) * amount for key in keys}

    def _energyScaledBlendShapes(self, shape: dict[str, float], energy: float, microMotion: float) -> dict[str, float]:
        speech = max(0.0, min(1.0, energy))
        output: dict[str, float] = {}
        for key, value in shape.items():
            if key in {"mouthClose", "mouthPressLeft", "mouthPressRight"}:
                scaled = value * (0.45 + speech * 0.9)
            else:
                scaled = value * (0.18 + speech * 0.95)
            output[key] = max(0.0, min(1.0, scaled))
        output["jawOpen"] = max(0.018, min(0.68, output.get("jawOpen", 0.0) + speech * 0.032 + microMotion * 0.01 * speech))
        output["mouthSmileLeft"] = max(0.02, min(0.18, output.get("mouthSmileLeft", 0.0) + 0.018))
        output["mouthSmileRight"] = max(0.02, min(0.18, output.get("mouthSmileRight", 0.0) + 0.016))
        return output

    def _audioDurationSeconds(self, audioPath: Path) -> float:
        try:
            with wave.open(str(audioPath), "rb") as wavFile:
                frameRate = wavFile.getframerate()
                if frameRate <= 0:
                    return 1.5
                return max(0.5, wavFile.getnframes() / frameRate)
        except wave.Error:
            return 1.5


class NvidiaAudio2FaceClient(Audio2FaceClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path, text: str = "") -> Path:
        if self.settings.a2fTransport == "http":
            return self._processAudioHttp(audioPath, profile, outputMode, resultPath)
        return asyncio.run(self._processAudioGrpc(audioPath, profile, outputMode, resultPath))

    def _processAudioHttp(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path) -> Path:
        baseUrl = f"http://{self.settings.a2fHost}:{self.settings.a2fPort}"
        payload = {
            "audioPath": str(audioPath.resolve()),
            "profile": profile,
            "outputMode": outputMode,
        }
        with httpx.Client(timeout=self.settings.a2fTimeoutSeconds) as client:
            response = client.post(f"{baseUrl}{self.settings.a2fProcessPath}", json=payload)
            response.raise_for_status()
            data = response.json()

        resultPath.parent.mkdir(parents=True, exist_ok=True)
        resultPath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return resultPath

    async def _processAudioGrpc(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path) -> Path:
        try:
            import grpc
            from nvidia_ace.a2f.v1_pb2 import (
                AudioWithEmotion,
                BlendShapeParameters,
                EmotionParameters,
                EmotionPostProcessingParameters,
                FaceParameters,
            )
            from nvidia_ace.audio.v1_pb2 import AudioHeader
            from nvidia_ace.controller.v1_pb2 import AudioStream, AudioStreamHeader
            from nvidia_ace.services.a2f_controller.v1_pb2_grpc import A2FControllerServiceStub
        except ImportError as exc:
            raise RuntimeError(
                "A2F gRPC dependencies are missing. Install backend requirements, including NVIDIA's nvidia_ace wheel."
            ) from exc

        audioInfo = self._readPcm16MonoWav(audioPath)
        if audioInfo["durationSeconds"] > self.settings.a2fGrpcMaxAudioSeconds:
            raise ValueError(f"A2F audio exceeds {self.settings.a2fGrpcMaxAudioSeconds:.0f}s limit")

        target = f"{self.settings.a2fHost}:{self.settings.a2fPort}"
        channel = grpc.aio.insecure_channel(target)
        frames: list[dict] = []
        blendShapeNames: list[str] = []
        statusMessages: list[dict[str, str | int]] = []

        async with channel as activeChannel:
            stub = A2FControllerServiceStub(activeChannel)
            stream = stub.ProcessAudioStream()

            readTask = asyncio.create_task(self._readA2fStream(stream, frames, blendShapeNames, statusMessages))

            await stream.write(
                AudioStream(
                    audio_stream_header=AudioStreamHeader(
                        audio_header=AudioHeader(
                            samples_per_second=audioInfo["sampleRate"],
                            bits_per_sample=16,
                            channel_count=1,
                            audio_format=AudioHeader.AUDIO_FORMAT_PCM,
                        ),
                        emotion_post_processing_params=EmotionPostProcessingParameters(
                            emotion_contrast=1.0,
                            live_blend_coef=0.7,
                            enable_preferred_emotion=False,
                            preferred_emotion_strength=0.5,
                            emotion_strength=0.6,
                            max_emotions=3,
                        ),
                        face_params=FaceParameters(float_params=self._defaultFaceParameters(profile)),
                        blendshape_params=BlendShapeParameters(enable_clamping_bs_weight=True),
                        emotion_params=EmotionParameters(
                            live_transition_time=0.0001,
                            beginning_emotion={"joy": 0.2},
                        ),
                    )
                )
            )

            chunkFrameCount = max(1, int(audioInfo["sampleRate"] * self.settings.a2fGrpcChunkSeconds))
            bytesPerFrame = 2
            chunkSize = chunkFrameCount * bytesPerFrame
            for offset in range(0, len(audioInfo["audioBytes"]), chunkSize):
                await stream.write(
                    AudioStream(
                        audio_with_emotion=AudioWithEmotion(
                            audio_buffer=audioInfo["audioBytes"][offset : offset + chunkSize],
                        )
                    )
                )
            await stream.write(AudioStream(end_of_audio=AudioStream.EndOfAudio()))
            await readTask

        timeline = self._buildTimeline(profile, outputMode, target, blendShapeNames, frames, statusMessages)
        resultPath.parent.mkdir(parents=True, exist_ok=True)
        resultPath.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
        return resultPath

    async def _readA2fStream(self, stream, frames: list[dict], blendShapeNames: list[str], statusMessages: list[dict]) -> None:
        import grpc

        while True:
            message = await asyncio.wait_for(stream.read(), timeout=self.settings.a2fTimeoutSeconds)
            if message == grpc.aio.EOF:
                return
            if message.HasField("animation_data_stream_header"):
                blendShapeNames[:] = list(message.animation_data_stream_header.skel_animation_header.blend_shapes)
                continue
            if message.HasField("animation_data") and message.animation_data.HasField("skel_animation"):
                for blendShapes in message.animation_data.skel_animation.blend_shape_weights:
                    values = dict(zip(blendShapeNames, blendShapes.values))
                    frames.append({"t": round(blendShapes.time_code, 3), "blendShapes": values})
                continue
            if message.HasField("status"):
                statusMessages.append({"code": int(message.status.code), "message": message.status.message})
                if int(message.status.code) == 3:
                    raise RuntimeError(message.status.message or "Audio2Face-3D returned ERROR")

    def _readPcm16MonoWav(self, audioPath: Path) -> dict[str, int | float | bytes]:
        with wave.open(str(audioPath), "rb") as wavFile:
            channels = wavFile.getnchannels()
            sampleWidth = wavFile.getsampwidth()
            sampleRate = wavFile.getframerate()
            frameCount = wavFile.getnframes()
            if channels != 1 or sampleWidth != 2:
                raise ValueError("Audio2Face-3D requires mono PCM-16 WAV input")
            return {
                "sampleRate": sampleRate,
                "audioBytes": wavFile.readframes(frameCount),
                "durationSeconds": frameCount / sampleRate if sampleRate else 0,
            }

    def _defaultFaceParameters(self, profile: str) -> dict[str, float]:
        lowerFaceStrength = 1.2 if profile in {"default", "james"} else 1.0
        return {
            "upperFaceStrength": 1.0,
            "upperFaceSmoothing": 0.001,
            "lowerFaceStrength": lowerFaceStrength,
            "lowerFaceSmoothing": 0.006,
            "faceMaskLevel": 0.6,
            "faceMaskSoftness": 0.0085,
            "skinStrength": 1.0,
            "eyelidOpenOffset": 0.06,
            "lipOpenOffset": -0.02,
            "tongueStrength": 1.3,
            "tongueHeightOffset": 0.0,
            "tongueDepthOffset": 0.0,
        }

    def _buildTimeline(
        self,
        profile: str,
        outputMode: str,
        target: str,
        blendShapeNames: list[str],
        frames: list[dict],
        statusMessages: list[dict],
    ) -> dict:
        browserFrames = []
        for frame in sorted(frames, key=lambda item: item["t"]):
            blendShapes = frame["blendShapes"]
            jawOpen = float(blendShapes.get("JawOpen", blendShapes.get("jawOpen", 0.0)))
            mouthSmile = (
                float(blendShapes.get("MouthSmileLeft", 0.0)) + float(blendShapes.get("MouthSmileRight", 0.0))
            ) / 2
            mouthWide = (
                float(blendShapes.get("MouthStretchLeft", 0.0)) + float(blendShapes.get("MouthStretchRight", 0.0))
            ) / 2
            browserFrames.append(
                {
                    "t": frame["t"],
                    "jawOpen": round(max(0.0, min(1.0, jawOpen)), 3),
                    "mouthWide": round(max(0.0, min(1.0, mouthWide)), 3),
                    "mouthSmile": round(max(0.0, min(1.0, mouthSmile)), 3),
                    "blendShapes": {key: round(float(value), 5) for key, value in blendShapes.items()},
                }
            )

        return {
            "engine": "nvidia-audio2face-3d-v1",
            "status": "completed",
            "profile": profile,
            "outputMode": outputMode,
            "grpcTarget": target,
            "fps": 30,
            "channels": blendShapeNames,
            "frames": browserFrames,
            "statusMessages": statusMessages,
        }
