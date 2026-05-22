import math
from io import BytesIO
from pathlib import Path
import wave

from src.config import Settings
from src.models.rag import LanguageCode, Transcript


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


class RivaAsrClient:
    def transcribe(self, audio: bytes, contentType: str | None, language: LanguageCode) -> Transcript:
        raise NotImplementedError


class NvidiaRivaAsrClient(RivaAsrClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def transcribe(self, audio: bytes, contentType: str | None, language: LanguageCode) -> Transcript:
        if not self.settings.rivaAsrEnabled:
            raise RuntimeError("Riva ASR is disabled by config. Set RIVA_ASR_ENABLED=true after ASR models are provisioned.")
        if not audio:
            raise ValueError("audio cannot be empty")

        try:
            import grpc
            import riva.client
        except ImportError as exc:
            raise RuntimeError("Riva client packages are missing. Install nvidia-riva-client and grpcio on the target host.") from exc

        encoding, sampleRateHz, payload = self._normalizeAudio(audio, contentType, riva.client)
        config = riva.client.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=sampleRateHz,
            language_code=language.value,
            max_alternatives=1,
            enable_automatic_punctuation=True,
        )
        auth = riva.client.Auth(uri=f"{self.settings.rivaAsrHost}:{self.settings.rivaAsrPort}")
        service = riva.client.ASRService(auth)
        try:
            response = service.offline_recognize(payload, config)
        except grpc.RpcError as exc:
            code = exc.code().name if exc.code() else "UNKNOWN"
            raise RuntimeError(f"Riva ASR request failed: {code} {exc.details()}") from exc

        if not response.results:
            raise RuntimeError("Riva ASR returned no transcript.")
        alternative = response.results[0].alternatives[0] if response.results[0].alternatives else None
        if alternative is None or not alternative.transcript.strip():
            raise RuntimeError("Riva ASR returned an empty transcript.")
        return Transcript(
            text=alternative.transcript,
            language=language,
            confidence=max(0.0, min(1.0, alternative.confidence or 0.0)),
            source="riva-asr",
        )

    def _normalizeAudio(self, audio: bytes, contentType: str | None, rivaClient) -> tuple[int, int, bytes]:
        normalizedType = (contentType or "").lower()
        if "ogg" in normalizedType or "opus" in normalizedType:
            return rivaClient.AudioEncoding.OGGOPUS, 48000, audio
        if "wav" in normalizedType or audio[:4] == b"RIFF":
            with wave.open(BytesIO(audio), "rb") as wavFile:
                channels = wavFile.getnchannels()
                sampleWidth = wavFile.getsampwidth()
                sampleRateHz = wavFile.getframerate()
                if channels != 1 or sampleWidth != 2:
                    raise ValueError("Riva ASR WAV input must be mono 16-bit PCM.")
                return rivaClient.AudioEncoding.LINEAR_PCM, sampleRateHz, wavFile.readframes(wavFile.getnframes())
        return rivaClient.AudioEncoding.LINEAR_PCM, self.settings.rivaAsrSampleRateHz, audio


def _writeMonoPcmWav(outputPath: Path, sampleRateHz: int, audio: bytes) -> None:
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(outputPath), "wb") as wavFile:
        wavFile.setnchannels(1)
        wavFile.setsampwidth(2)
        wavFile.setframerate(sampleRateHz)
        wavFile.writeframes(audio)
