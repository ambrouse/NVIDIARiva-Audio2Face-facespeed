from pathlib import Path
import json
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
    assert job.audioUrl == f"/api/artifacts/audio/{job.id}.wav"
    assert job.animationUrl == f"/api/artifacts/animation/{job.id}.json"
    with wave.open(job.audioPath, "rb") as wavFile:
        assert wavFile.getnframes() > 0
    animation = json.loads(Path(job.resultPath).read_text())
    assert animation["engine"] == "browser-viseme-v2"
    assert animation["frames"]


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
        def processAudio(self, audioPath: Path, profile: str, outputMode: str, resultPath: Path, text: str = "") -> Path:
            raise RuntimeError("audio2face timeout")

    settings = Settings(outputDir=tmp_path / "outputs", logDir=tmp_path / "logs")
    service = JobService(settings, MockRivaTtsClient(), FailingAudio2FaceClient())

    job = service.createJob(CreateJobRequest(text="hello"))

    assert job.state == JobState.failed
    assert job.error == "audio2face timeout"
    assert Path(job.audioPath).exists()
    assert job.resultPath is None


def testMockAudio2FaceBuildsSmoothAudioDrivenBlendShapes(tmp_path: Path) -> None:
    audioPath = tmp_path / "speech.wav"
    sampleRate = 22050
    with wave.open(str(audioPath), "wb") as wavFile:
        wavFile.setnchannels(1)
        wavFile.setsampwidth(2)
        wavFile.setframerate(sampleRate)
        frames = bytearray()
        for index in range(sampleRate):
            envelope = 0.15 + 0.75 * (index / sampleRate)
            sample = int(9000 * envelope)
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))
        wavFile.writeframes(bytes(frames))

    resultPath = tmp_path / "animation.json"
    MockAudio2FaceClient().processAudio(audioPath, "james", "preview", resultPath, "map five around wide vowels")

    timeline = json.loads(resultPath.read_text())
    frames = timeline["frames"]
    jawValues = [frame["jawOpen"] for frame in frames]
    maxStep = max(abs(nextValue - value) for value, nextValue in zip(jawValues, jawValues[1:]))

    assert timeline["channels"] == ["jawOpen", "mouthWide", "mouthSmile", "blendShapes"]
    assert abs(frames[0]["blendShapes"]["jawOpen"] - frames[0]["jawOpen"]) <= 0.005
    assert all("mouthFunnel" in frame["blendShapes"] for frame in frames)
    assert any(frame["blendShapes"]["mouthClose"] > 0.2 for frame in frames)
    assert any(frame["blendShapes"]["mouthPucker"] > 0.1 for frame in frames)
    assert maxStep < 0.18


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
    settings = Settings(a2fTransport="http", a2fHost="a2f.local", a2fPort=8011, a2fProcessPath="/api/process", a2fTimeoutSeconds=12)
    audioPath = tmp_path / "audio.wav"
    audioPath.write_bytes(b"audio")
    resultPath = tmp_path / "result.json"

    NvidiaAudio2FaceClient(settings).processAudio(audioPath, "default", "preview", resultPath, "hello")

    assert captured["url"] == "http://a2f.local:8011/api/process"
    assert captured["json"]["profile"] == "default"
    assert captured["json"]["outputMode"] == "preview"
    assert resultPath.exists()


def testAudio2FaceGrpcTimelineMapsBlendShapes() -> None:
    settings = Settings(a2fTransport="grpc")
    client = NvidiaAudio2FaceClient(settings)

    timeline = client._buildTimeline(
        "james",
        "preview",
        "127.0.0.1:8040",
        ["JawOpen", "MouthSmileLeft", "MouthSmileRight", "MouthStretchLeft", "MouthStretchRight"],
        [
            {
                "t": 0.033,
                "blendShapes": {
                    "JawOpen": 0.7,
                    "MouthSmileLeft": 0.2,
                    "MouthSmileRight": 0.4,
                    "MouthStretchLeft": 0.1,
                    "MouthStretchRight": 0.3,
                },
            }
        ],
        [{"code": 0, "message": "ok"}],
    )

    assert timeline["engine"] == "nvidia-audio2face-3d-v1"
    assert timeline["frames"][0]["jawOpen"] == 0.7
    assert timeline["frames"][0]["mouthSmile"] == 0.3
    assert timeline["frames"][0]["mouthWide"] == 0.2
    assert timeline["frames"][0]["blendShapes"]["JawOpen"] == 0.7


def testAudio2FaceGrpcRejectsNonMonoWav(tmp_path: Path) -> None:
    settings = Settings(a2fTransport="grpc")
    audioPath = tmp_path / "stereo.wav"
    with wave.open(str(audioPath), "wb") as wavFile:
        wavFile.setnchannels(2)
        wavFile.setsampwidth(2)
        wavFile.setframerate(16000)
        wavFile.writeframes(b"\x00\x00\x00\x00")

    client = NvidiaAudio2FaceClient(settings)

    try:
        client._readPcm16MonoWav(audioPath)
    except ValueError as error:
        assert "mono PCM-16" in str(error)
    else:
        raise AssertionError("expected non-mono wav to be rejected")


def testRivaClientWritesLinearPcmAsWav(tmp_path: Path, monkeypatch) -> None:
    captured = {}

    class FakeAuth:
        def __init__(self, uri: str) -> None:
            self.uri = uri

    class FakeSpeechSynthesisService:
        def __init__(self, auth: FakeAuth) -> None:
            self.auth = auth

        def synthesize(self, **kwargs):
            captured.update(kwargs)
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
    assert captured["voice_name"] == "English-US.Female-1"
    assert captured["language_code"] == "en-US"


def testRivaClientRejectsEmptyAudioPayload(tmp_path: Path, monkeypatch) -> None:
    class FakeAuth:
        def __init__(self, uri: str) -> None:
            self.uri = uri

    class FakeSpeechSynthesisService:
        def __init__(self, auth: FakeAuth) -> None:
            self.auth = auth

        def synthesize(self, **kwargs):
            return types.SimpleNamespace(audio=b"")

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

    try:
        NvidiaRivaTtsClient(Settings()).synthesize("hello", "English-US.Female-1", "en-US", outputPath)
    except RuntimeError as error:
        assert "empty audio" in str(error)
    else:
        raise AssertionError("expected empty Riva audio to fail")
