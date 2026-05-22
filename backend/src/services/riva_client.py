import math
from pathlib import Path
import wave

from src.config import Settings


class RivaTtsClient:
    def synthesize(self, text: str, voice: str, language: str, outputPath: Path) -> Path:
        raise NotImplementedError


class MockRivaTtsClient(RivaTtsClient):
    def synthesize(self, text: str, voice: str, language: str, outputPath: Path) -> Path:
        sampleRateHz = 22050
        durationSeconds = max(8.0, min(30.0, len(text) * 0.18))
        frameCount = int(sampleRateHz * durationSeconds)
        frames = bytearray()
        for index in range(frameCount):
            timeSeconds = index / sampleRateHz
            syllablePulse = 0.25 + 0.75 * max(0, math.sin(2 * math.pi * 3.2 * timeSeconds))
            fadeIn = min(1.0, timeSeconds / 0.08)
            fadeOut = min(1.0, (durationSeconds - timeSeconds) / 0.12)
            envelope = syllablePulse * fadeIn * fadeOut
            carrier = math.sin(2 * math.pi * 190 * timeSeconds) + 0.35 * math.sin(2 * math.pi * 380 * timeSeconds)
            sample = int(carrier * 7500 * envelope)
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))
        _writeMonoPcmWav(outputPath, sampleRateHz, bytes(frames))
        return outputPath


class NvidiaRivaTtsClient(RivaTtsClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def synthesize(self, text: str, voice: str, language: str, outputPath: Path) -> Path:
        try:
            import grpc
            import riva.client
        except ImportError as exc:
            raise RuntimeError("Riva client packages are missing. Install nvidia-riva-client and grpcio on the target host.") from exc

        auth = riva.client.Auth(uri=f"{self.settings.rivaHost}:{self.settings.rivaPort}")
        service = riva.client.SpeechSynthesisService(auth)
        sampleRateHz = self.settings.rivaSampleRateHz
        voiceName = self.settings.rivaDefaultVoice if voice == "default" else voice
        response = service.synthesize(
            text=text,
            voice_name=voiceName,
            language_code=language,
            sample_rate_hz=sampleRateHz,
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
        )
        if not response.audio:
            raise RuntimeError("Riva returned an empty audio payload.")
        _writeMonoPcmWav(outputPath, sampleRateHz, response.audio)
        return outputPath


def _writeMonoPcmWav(outputPath: Path, sampleRateHz: int, audio: bytes) -> None:
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(outputPath), "wb") as wavFile:
        wavFile.setnchannels(1)
        wavFile.setsampwidth(2)
        wavFile.setframerate(sampleRateHz)
        wavFile.writeframes(audio)
