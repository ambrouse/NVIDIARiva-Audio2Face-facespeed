from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    backendHost: str = "127.0.0.1"
    backendPort: int = 8000
    rivaHost: str = "127.0.0.1"
    rivaPort: int = 50051
    a2fHost: str = "127.0.0.1"
    a2fPort: int = 8011
    logDir: Path = Path("logs")
    outputDir: Path = Path("outputs")
    serviceManagerMode: str = "mock"
    pipelineMode: str = "mock"
    rivaSampleRateHz: int = 22050
    a2fProcessPath: str = "/api/process-audio"
    a2fTimeoutSeconds: float = 120.0
    allowedOrigins: str = "http://127.0.0.1:5173,http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file="../.env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowedOriginList(self) -> list[str]:
        return [origin.strip() for origin in self.allowedOrigins.split(",") if origin.strip()]


@lru_cache
def getSettings() -> Settings:
    settings = Settings()
    settings.logDir.mkdir(parents=True, exist_ok=True)
    settings.outputDir.mkdir(parents=True, exist_ok=True)
    return settings
