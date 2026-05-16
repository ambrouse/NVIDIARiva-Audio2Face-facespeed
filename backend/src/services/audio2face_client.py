import json
from pathlib import Path

import httpx

from src.config import Settings


class Audio2FaceClient:
    def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path) -> Path:
        raise NotImplementedError


class MockAudio2FaceClient(Audio2FaceClient):
    def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path) -> Path:
        resultPath.parent.mkdir(parents=True, exist_ok=True)
        resultPath.write_text('{"status":"mock_completed"}', encoding="utf-8")
        return resultPath


class NvidiaAudio2FaceClient(Audio2FaceClient):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path) -> Path:
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
