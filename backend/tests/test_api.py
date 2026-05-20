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

    jobResponse = client.get(f"/api/jobs/{body['id']}")
    assert jobResponse.status_code == 200
    assert jobResponse.json()["id"] == body["id"]


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
