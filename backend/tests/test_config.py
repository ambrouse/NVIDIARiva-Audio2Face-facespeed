from src.config import Settings


def testSettingsReadEnvExampleNames(monkeypatch) -> None:
    monkeypatch.setenv("PIPELINE_MODE", "nvidia")
    monkeypatch.setenv("RIVA_HOST", "riva.local")
    monkeypatch.setenv("RIVA_PORT", "50052")
    monkeypatch.setenv("A2F_PROCESS_PATH", "/api/a2f")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://127.0.0.1:6200")

    settings = Settings()

    assert settings.pipelineMode == "nvidia"
    assert settings.rivaHost == "riva.local"
    assert settings.rivaPort == 50052
    assert settings.a2fProcessPath == "/api/a2f"
    assert settings.allowedOriginList == ["http://127.0.0.1:6200"]


def testSettingsDefaultToSafeLocalPortsAndThresholds() -> None:
    settings = Settings()

    assert settings.backendHost == "127.0.0.1"
    assert settings.backendPort == 8020
    assert settings.frontendPort == 6210
    assert settings.rivaPort == 50100
    assert settings.a2fPort == 8040
    assert settings.allowedOriginList == ["http://127.0.0.1:6210", "http://localhost:6210"]
    assert settings.resourceReservePercent == 10
    assert settings.gpuMinFreeVramPercent == 10
    assert settings.ramMinFreePercent == 10
    assert settings.diskMinFreePercent == 10
