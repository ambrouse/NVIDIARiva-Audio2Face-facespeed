from functools import lru_cache
from pathlib import Path

from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    backendHost: str = Field("127.0.0.1", validation_alias=AliasChoices("BACKEND_HOST", "backendHost"))
    backendPort: int = Field(8020, validation_alias=AliasChoices("BACKEND_PORT", "backendPort"))
    frontendHost: str = Field("127.0.0.1", validation_alias=AliasChoices("FRONTEND_HOST", "frontendHost"))
    frontendPort: int = Field(6210, validation_alias=AliasChoices("FRONTEND_PORT", "frontendPort"))
    rivaHost: str = Field("127.0.0.1", validation_alias=AliasChoices("RIVA_HOST", "rivaHost"))
    rivaPort: int = Field(50100, validation_alias=AliasChoices("RIVA_PORT", "rivaPort"))
    a2fHost: str = Field("127.0.0.1", validation_alias=AliasChoices("A2F_HOST", "a2fHost"))
    a2fPort: int = Field(8040, validation_alias=AliasChoices("A2F_PORT", "a2fPort"))
    logDir: Path = Field(Path("logs"), validation_alias=AliasChoices("LOG_DIR", "logDir"))
    outputDir: Path = Field(Path("outputs"), validation_alias=AliasChoices("OUTPUT_DIR", "outputDir"))
    serviceManagerMode: Literal["mock", "docker"] = Field("mock", validation_alias=AliasChoices("SERVICE_MANAGER_MODE", "serviceManagerMode"))
    pipelineMode: Literal["mock", "nvidia"] = Field("mock", validation_alias=AliasChoices("PIPELINE_MODE", "pipelineMode"))
    rivaSampleRateHz: int = Field(22050, validation_alias=AliasChoices("RIVA_SAMPLE_RATE_HZ", "rivaSampleRateHz"))
    a2fProcessPath: str = Field("/api/process-audio", validation_alias=AliasChoices("A2F_PROCESS_PATH", "a2fProcessPath"))
    a2fTimeoutSeconds: float = Field(120.0, validation_alias=AliasChoices("A2F_TIMEOUT_SECONDS", "a2fTimeoutSeconds"))
    allowedOrigins: str = Field(
        "http://127.0.0.1:6210,http://localhost:6210",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "allowedOrigins"),
    )
    resourceReservePercent: int = Field(10, validation_alias=AliasChoices("RESOURCE_RESERVE_PERCENT", "resourceReservePercent"))
    gpuMinFreeVramPercent: int = Field(10, validation_alias=AliasChoices("GPU_MIN_FREE_VRAM_PERCENT", "gpuMinFreeVramPercent"))
    ramMinFreePercent: int = Field(10, validation_alias=AliasChoices("RAM_MIN_FREE_PERCENT", "ramMinFreePercent"))
    diskMinFreePercent: int = Field(10, validation_alias=AliasChoices("DISK_MIN_FREE_PERCENT", "diskMinFreePercent"))

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
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
