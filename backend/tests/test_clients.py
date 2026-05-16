from pathlib import Path

import httpx

from src.config import Settings
from src.models.job import CreateJobRequest
from src.services.audio2face_client import NvidiaAudio2FaceClient
from src.services.job_service import JobService
from src.services.audio2face_client import MockAudio2FaceClient
from src.services.riva_client import MockRivaTtsClient


def testJobServiceUsesInjectedPipelineClients(tmp_path: Path) -> None:
    settings = Settings(outputDir=tmp_path / "outputs", logDir=tmp_path / "logs")
    service = JobService(settings, MockRivaTtsClient(), MockAudio2FaceClient())

    job = service.createJob(CreateJobRequest(text="hello", voice="default", language="en-US", a2fProfile="default", outputMode="preview"))

    assert job.state == "completed"
    assert Path(job.audioPath).exists()
    assert Path(job.resultPath).exists()


def testAudio2FaceClientPostsConfiguredPayload(tmp_path: Path, monkeypatch) -> None:
    captured = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"status": "ok"}

    class FakeClient:
        def __init__(self, timeout: float) -> None:
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def post(self, url: str, json: dict[str, str]):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    settings = Settings(a2fHost="a2f.local", a2fPort=8011, a2fProcessPath="/api/process", a2fTimeoutSeconds=12)
    audioPath = tmp_path / "audio.wav"
    audioPath.write_bytes(b"audio")
    resultPath = tmp_path / "result.json"

    NvidiaAudio2FaceClient(settings).processAudio(audioPath, "default", "preview", resultPath)

    assert captured["url"] == "http://a2f.local:8011/api/process"
    assert captured["json"]["profile"] == "default"
    assert captured["json"]["outputMode"] == "preview"
    assert resultPath.exists()
