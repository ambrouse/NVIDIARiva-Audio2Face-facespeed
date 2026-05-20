from pathlib import Path
import wave

from src.config import Settings


class RivaTtsClient:
    def synthesize(self, text: str, voice: str, language: str, outputPath: Path) -> Path:
        raise NotImplementedError


class MockRivaTtsClient(RivaTtsClient):
    def synthesize(self, text: str, voice: str, language: str, outputPath: Path) -> Path:
        outputPath.parent.mkdir(parents=True, exist_ok=True)
        outputPath.write_bytes(b"MOCK_RIVA_AUDIO")
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
        response = service.synthesize(
            text=text,
            voice_name=voice,
            language_code=language,
            sample_rate_hz=sampleRateHz,
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
        )
        outputPath.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(outputPath), "wb") as wavFile:
            wavFile.setnchannels(1)
            wavFile.setsampwidth(2)
            wavFile.setframerate(sampleRateHz)
            wavFile.writeframes(response.audio)
        return outputPath
