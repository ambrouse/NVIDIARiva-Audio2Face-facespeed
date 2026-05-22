import re

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def testHealthReturnsOk() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def testServicesAreAllowlisted() -> None:
    response = client.get("/api/services")
    assert response.status_code == 200
    names = {service["name"] for service in response.json()}
    assert names == {"riva", "audio2face", "backend-worker"}


def testServicesExposeContainerManagementMetadata() -> None:
    response = client.get("/api/services")
    assert response.status_code == 200
    services = {service["name"]: service for service in response.json()}
    assert services["riva"]["managerMode"] == "mock"
    assert services["riva"]["containerName"] == "facespeed-riva"
    assert services["audio2face"]["containerName"] == "facespeed-audio2face-3d"


def testRejectsUnknownServiceName() -> None:
    response = client.post("/api/services/not-allowed/start")
    assert response.status_code == 422


def testServiceActionChangesState() -> None:
    response = client.post("/api/services/riva/start")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "riva"
    assert body["state"] == "running"
    assert body["healthy"] is True


def testCreateJobCompletesMockPipeline() -> None:
    response = client.post(
        "/api/jobs",
        json={
            "text": "Xin chào",
            "voice": "default",
            "language": "vi-VN",
            "a2fProfile": "default",
            "outputMode": "preview",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["state"] == "completed"
    assert body["audioPath"]
    assert body["resultPath"]
    assert body["audioUrl"] == f"/api/artifacts/audio/{body['id']}.wav"
    assert body["animationUrl"] == f"/api/artifacts/animation/{body['id']}.json"

    audioResponse = client.get(body["audioUrl"])
    assert audioResponse.status_code == 200
    assert audioResponse.content[:4] == b"RIFF"

    animationResponse = client.get(body["animationUrl"])
    assert animationResponse.status_code == 200
    animation = animationResponse.json()
    assert animation["engine"] == "browser-viseme-v2"
    assert animation["frames"]
    assert all(0 <= frame["jawOpen"] <= 1 for frame in animation["frames"])
    assert [frame["t"] for frame in animation["frames"]] == sorted(frame["t"] for frame in animation["frames"])

    jobResponse = client.get(f"/api/jobs/{body['id']}")
    assert jobResponse.status_code == 200
    assert jobResponse.json()["id"] == body["id"]


def testArtifactRouteRejectsInvalidJobId() -> None:
    response = client.get("/api/artifacts/audio/../../secret.wav")
    assert response.status_code == 404


def testArtifactRouteRejectsNonUuidJobId() -> None:
    response = client.get("/api/artifacts/animation/not-a-uuid.json")
    assert response.status_code == 404


def testArtifactUrlsUseUuidFilenames() -> None:
    response = client.post("/api/jobs", json={"text": "hello"})
    body = response.json()
    assert re.fullmatch(r"/api/artifacts/audio/[0-9a-f-]{36}\.wav", body["audioUrl"])
    assert re.fullmatch(r"/api/artifacts/animation/[0-9a-f-]{36}\.json", body["animationUrl"])


def testRejectsEmptyJobText() -> None:
    response = client.post("/api/jobs", json={"text": ""})
    assert response.status_code == 422


def testRejectsWhitespaceOnlyJobText() -> None:
    response = client.post("/api/jobs", json={"text": "   \n\t   "})
    assert response.status_code == 422


def testRejectsUnsafeVoiceName() -> None:
    response = client.post("/api/jobs", json={"text": "hello", "voice": "default;rm"})
    assert response.status_code == 422


def testRejectsTooLongJobText() -> None:
    response = client.post("/api/jobs", json={"text": "x" * 1001})
    assert response.status_code == 422
