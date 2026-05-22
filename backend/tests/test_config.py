from src.config import Settings


def testSettingsReadEnvExampleNames(monkeypatch) -> None:
    monkeypatch.setenv("SERVICE_MANAGER_MODE", "docker")
    monkeypatch.setenv("PIPELINE_MODE", "riva")
    monkeypatch.setenv("RIVA_HOST", "riva.local")
    monkeypatch.setenv("RIVA_PORT", "50052")
    monkeypatch.setenv("RIVA_ASR_HOST", "asr.local")
    monkeypatch.setenv("RIVA_ASR_PORT", "50152")
    monkeypatch.setenv("RIVA_DEFAULT_VOICE", "English-US.Male-1")
    monkeypatch.setenv("A2F_PROCESS_PATH", "/api/a2f")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://127.0.0.1:6200")

    settings = Settings()

    assert settings.serviceManagerMode == "docker"
    assert settings.pipelineMode == "riva"
    assert settings.rivaHost == "riva.local"
    assert settings.rivaPort == 50052
    assert settings.rivaAsrHost == "asr.local"
    assert settings.rivaAsrPort == 50152
    assert settings.rivaDefaultVoice == "English-US.Male-1"
    assert settings.a2fProcessPath == "/api/a2f"
    assert settings.allowedOriginList == ["http://127.0.0.1:6200"]


def testSettingsDefaultToProviderMainPathAndSafeLocalPorts(monkeypatch) -> None:
    for name in [
        "BACKEND_HOST",
        "BACKEND_PORT",
        "FRONTEND_HOST",
        "FRONTEND_PORT",
        "RIVA_PORT",
        "RIVA_ASR_PORT",
        "A2F_PORT",
        "ALLOWED_ORIGINS",
        "SERVICE_MANAGER_MODE",
        "PIPELINE_MODE",
        "RESOURCE_RESERVE_PERCENT",
        "GPU_MIN_FREE_VRAM_PERCENT",
        "RAM_MIN_FREE_PERCENT",
        "DISK_MIN_FREE_PERCENT",
    ]:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.backendHost == "127.0.0.1"
    assert settings.backendPort == 8020
    assert settings.frontendPort == 6310
    assert settings.rivaPort == 50051
    assert settings.rivaAsrPort == 50151
    assert settings.a2fPort == 8040
    assert settings.serviceManagerMode == "docker"
    assert settings.pipelineMode == "riva"
    assert settings.allowedOriginList == ["http://127.0.0.1:6310", "http://localhost:6310"]
    assert settings.resourceReservePercent == 10
    assert settings.gpuMinFreeVramPercent == 10
    assert settings.ramMinFreePercent == 10
    assert settings.diskMinFreePercent == 10
