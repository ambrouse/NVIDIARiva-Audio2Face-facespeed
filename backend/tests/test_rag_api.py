from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.dependencies import getRagService
from src.main import app
from src.config import Settings, getSettings
from src.services.audio2face_client import MockAudio2FaceClient
from src.services.docling_client import ParsedPdf
from src.services.embedding_client import RerankHit
from src.services.job_service import JobService
from src.services.rag_service import RagService
from src.services.riva_client import MockRivaTtsClient


def makeSettings(**kwargs) -> Settings:
    return Settings(_env_file=None, **kwargs)


class FakeDoclingClient:
    def parsePdf(self, payload: bytes, filename: str) -> ParsedPdf:
        return ParsedPdf(
            filename=filename,
            markdown=(
                "# Production Voice RAG Runbook\n\n"
                "The answer pipeline retrieves PDF chunks, reviews grounding, returns page citations, "
                "generates answer audio, and drives the 3D avatar mouth timeline.\n\n"
                "Operators should enable Riva ASR before real microphone transcription."
            ),
        )


class FailingDoclingClient:
    def parsePdf(self, payload: bytes, filename: str) -> ParsedPdf:
        raise RuntimeError("Docling parse failed")


class FakeEmbeddingClient:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def rerank(self, query: str, documents: list[str]) -> list[RerankHit]:
        queryVector = self._vector(query)
        scored = [(index, self._cosine(queryVector, self._vector(document))) for index, document in enumerate(documents)]
        return [RerankHit(index=index, score=score) for index, score in sorted(scored, key=lambda item: item[1], reverse=True)]

    def _vector(self, text: str) -> list[float]:
        lowered = text.lower()
        return [
            1.0 if "avatar" in lowered else 0.0,
            1.0 if "pipeline" in lowered else 0.0,
            1.0 if "audio" in lowered else 0.0,
            1.0 if "price" in lowered or "orion" in lowered else 0.0,
        ]

    def _cosine(self, left: list[float], right: list[float]) -> float:
        leftNorm = sum(value * value for value in left) ** 0.5
        rightNorm = sum(value * value for value in right) ** 0.5
        if leftNorm == 0 or rightNorm == 0:
            return 0.0
        return sum(a * b for a, b in zip(left, right)) / (leftNorm * rightNorm)


@pytest.fixture()
def client(tmp_path: Path):
    settings = makeSettings(
        outputDir=tmp_path / "outputs",
        logDir=tmp_path / "logs",
        ragStorageDir=tmp_path / "rag-storage",
        ragMinVectorScore=0.2,
        ragMinConfidence=0.45,
    )
    service = RagService(
        settings,
        JobService(settings, MockRivaTtsClient(), MockAudio2FaceClient()),
        FakeDoclingClient(),
        FakeEmbeddingClient(),
    )
    app.dependency_overrides[getRagService] = lambda: service
    app.dependency_overrides[getSettings] = lambda: settings
    with TestClient(app) as testClient:
        yield testClient
    app.dependency_overrides.clear()


@pytest.fixture()
def failingDoclingClient(tmp_path: Path):
    settings = makeSettings(outputDir=tmp_path / "outputs", logDir=tmp_path / "logs", ragStorageDir=tmp_path / "rag-storage")
    service = RagService(
        settings,
        JobService(settings, MockRivaTtsClient(), MockAudio2FaceClient()),
        FailingDoclingClient(),
        FakeEmbeddingClient(),
    )
    app.dependency_overrides[getRagService] = lambda: service
    app.dependency_overrides[getSettings] = lambda: settings
    with TestClient(app) as testClient:
        yield testClient
    app.dependency_overrides.clear()


def testRagStatusExposesAsrBlockedState(client: TestClient) -> None:
    response = client.get("/api/rag/status")
    assert response.status_code == 200
    body = response.json()
    assert body["asrAvailable"] is False
    assert "blocked" in body["asrDetail"]
    assert body["documentCount"] >= 0
    assert body["chunkCount"] >= 0
    assert "en-US" in body["languages"]
    assert "vi-VN" in body["languages"]


def testDocumentIngestionRejectsUnsafeInputs(client: TestClient) -> None:
    response = client.post(
        "/api/documents?filename=notes.txt&language=en-US",
        content=b"%PDF-1.4\nnot a txt\n%%EOF",
        headers={"content-type": "application/pdf"},
    )
    assert response.status_code == 400
    assert "only PDF" in response.json()["detail"]

    response = client.post(
        "/api/documents?filename=empty.pdf&language=en-US",
        content=b"not actually a pdf",
        headers={"content-type": "application/pdf"},
    )
    assert response.status_code == 400
    assert "signature" in response.json()["detail"]


def testIngestSearchAndVoiceChatReturnCitationsAndAvatarArtifacts(client: TestClient) -> None:
    payload = (
        b"%PDF-1.4\n"
        b"Production Voice RAG Runbook. The answer pipeline retrieves PDF chunks, reviews grounding, "
        b"returns page citations, generates answer audio, and drives the 3D avatar mouth timeline. "
        b"Operators should enable Riva ASR before real microphone transcription.\n%%EOF"
    )
    ingest = client.post(
        "/api/documents?filename=production-voice-rag-runbook.pdf&language=en-US",
        content=payload,
        headers={"content-type": "application/pdf"},
    )
    assert ingest.status_code == 200
    document = ingest.json()
    assert document["filename"] == "production-voice-rag-runbook.pdf"
    assert document["status"] == "indexed"
    assert document["chunkCount"] >= 1
    assert document["chunks"][0]["page"] == 1
    assert document["chunks"][0]["titlePath"]

    search = client.post("/api/rag/search", json={"query": "How does the answer pipeline drive the avatar?", "language": "en-US"})
    assert search.status_code == 200
    searchBody = search.json()
    assert searchBody["found"] is True
    assert searchBody["answerability"] == "pass"
    assert searchBody["citations"]
    assert searchBody["citations"][0]["source"] == "production-voice-rag-runbook.pdf"
    assert searchBody["trace"][1]["agent"] == "search"

    turnResponse = client.post(
        "/api/voice/chat",
        json={
            "message": "How does the answer pipeline drive the avatar?",
            "language": "en-US",
            "voice": "English-US.Female-1",
            "outputMode": "preview",
        },
    )
    assert turnResponse.status_code == 200
    turn = turnResponse.json()
    assert turn["transcript"]["text"] == "How does the answer pipeline drive the avatar?"
    assert turn["answer"]["reviewStatus"] == "pass"
    assert turn["answer"]["citations"]
    assert turn["audioUrl"].endswith(".wav")
    assert turn["animationUrl"].endswith(".json")
    assert [trace["agent"] for trace in turn["agentTrace"]] == ["lead", "search", "review", "teacher"]

    audio = client.get(turn["audioUrl"])
    assert audio.status_code == 200
    assert audio.content[:4] == b"RIFF"

    animation = client.get(turn["animationUrl"])
    assert animation.status_code == 200
    assert animation.json()["frames"]


def testVoiceChatNotFoundDoesNotHallucinate(client: TestClient) -> None:
    response = client.post("/api/voice/chat", json={"message": "What is the launch price of the imaginary Orion Nova?", "language": "en-US"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]["reviewStatus"] == "not_found"
    assert "could not find" in body["answer"]["text"].lower()
    assert body["answer"]["citations"] == []


def testDoclingFailureReportsErrorWithoutFallback(failingDoclingClient: TestClient) -> None:
    response = failingDoclingClient.post(
        "/api/documents?filename=production-voice-rag-runbook.pdf&language=en-US",
        content=b"%PDF-1.4\nvalid signature only\n%%EOF",
        headers={"content-type": "application/pdf"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Docling parse failed"


def testRealAsrEndpointReportsUnavailableUntilRivaAsrIsEnabled(client: TestClient) -> None:
    response = client.post("/api/voice/transcribe", content=b"RIFF....", headers={"content-type": "application/octet-stream"})
    assert response.status_code == 503
    assert "Riva ASR is disabled by config" in response.json()["detail"]
