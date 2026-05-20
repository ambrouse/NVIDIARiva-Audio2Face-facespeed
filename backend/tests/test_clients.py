from pathlib import Path
import sys
import types
import wave

import httpx

from src.config import Settings
from src.models.job import CreateJobRequest, JobState
from src.services.audio2face_client import NvidiaAudio2FaceClient
from src.services.job_service import JobService
from src.services.audio2face_client import MockAudio2FaceClient
from src.services.riva_client import MockRivaTtsClient, NvidiaRivaTtsClient


def testJobServiceUsesInjectedPipelineClients(tmp_path: Path) -> None:
    settings = Settings(outputDir=tmp_path / "outputs", logDir=tmp_path / "logs")
    service = JobService(settings, MockRivaTtsClient(), MockAudio2FaceClient())

    job = service.createJob(CreateJobRequest(text="hello", voice="default", language="en-US", a2fProfile="default", outputMode="preview"))

    assert job.state == "completed"
    assert Path(job.audioPath).exists()
    assert Path(job.resultPath).exists()


def testJobServiceMarksRivaFailureAsFailed(tmp_path: Path) -> None:
    class FailingRivaClient(MockRivaTtsClient):
        def synthesize(self, text: str, voice: str, language: str, outputPath: Path) -> Path:
            raise RuntimeError("riva unavailable")

    settings = Settings(outputDir=tmp_path / "outputs", logDir=tmp_path / "logs")
    service = JobService(settings, FailingRivaClient(), MockAudio2FaceClient())

    job = service.createJob(CreateJobRequest(text="hello"))

    assert job.state == JobState.failed
    assert job.error == "riva unavailable"
    assert service.readJobLogs(job.id)


def testJobServiceMarksAudio2FaceFailureAsFailed(tmp_path: Path) -> None:
    class FailingAudio2FaceClient(MockAudio2FaceClient):
        def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path) -> Path:
            raise RuntimeError("audio2face timeout")

    settings = Settings(outputDir=tmp_path / "outputs", logDir=tmp_path / "logs")
    service = JobService(settings, MockRivaTtsClient(), FailingAudio2FaceClient())

    job = service.createJob(CreateJobRequest(text="hello"))

    assert job.state == JobState.failed
    assert job.error == "audio2face timeout"
    assert Path(job.audioPath).exists()
    assert job.resultPath is None


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


def testRivaClientWritesLinearPcmAsWav(tmp_path: Path, monkeypatch) -> None:
    class FakeAuth:
        def __init__(self, uri: str) -> None:
            self.uri = uri

    class FakeSpeechSynthesisService:
        def __init__(self, auth: FakeAuth) -> None:
            self.auth = auth

        def synthesize(self, **kwargs):
            return types.SimpleNamespace(audio=b"\x00\x00\xff\x7f")

    fakeClient = types.SimpleNamespace(
        Auth=FakeAuth,
        SpeechSynthesisService=FakeSpeechSynthesisService,
        AudioEncoding=types.SimpleNamespace(LINEAR_PCM="linear_pcm"),
    )
    fakeRiva = types.SimpleNamespace(client=fakeClient)
    monkeypatch.setitem(sys.modules, "grpc", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "riva", fakeRiva)
    monkeypatch.setitem(sys.modules, "riva.client", fakeClient)

    outputPath = tmp_path / "audio.wav"
    settings = Settings(rivaSampleRateHz=22050)

    NvidiaRivaTtsClient(settings).synthesize("hello", "default", "en-US", outputPath)

    with wave.open(str(outputPath), "rb") as wavFile:
        assert wavFile.getnchannels() == 1
        assert wavFile.getsampwidth() == 2
        assert wavFile.getframerate() == 22050
        assert wavFile.readframes(2) == b"\x00\x00\xff\x7f"
