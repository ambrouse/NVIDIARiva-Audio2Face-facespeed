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
    frontendPort: int = Field(6310, validation_alias=AliasChoices("FRONTEND_PORT", "frontendPort"))
    rivaHost: str = Field("127.0.0.1", validation_alias=AliasChoices("RIVA_HOST", "rivaHost"))
    rivaPort: int = Field(50051, validation_alias=AliasChoices("RIVA_PORT", "rivaPort"))
    a2fHost: str = Field("127.0.0.1", validation_alias=AliasChoices("A2F_HOST", "a2fHost"))
    a2fPort: int = Field(8040, validation_alias=AliasChoices("A2F_PORT", "a2fPort"))
    a2fHttpPort: int = Field(8041, validation_alias=AliasChoices("A2F_HTTP_PORT", "a2fHttpPort"))
    logDir: Path = Field(Path("logs"), validation_alias=AliasChoices("LOG_DIR", "logDir"))
    outputDir: Path = Field(Path("outputs"), validation_alias=AliasChoices("OUTPUT_DIR", "outputDir"))
    serviceManagerMode: Literal["mock", "docker"] = Field("docker", validation_alias=AliasChoices("SERVICE_MANAGER_MODE", "serviceManagerMode"))
    pipelineMode: Literal["mock", "riva", "nvidia"] = Field(
        "riva",
        validation_alias=AliasChoices("PIPELINE_MODE", "pipelineMode"),
    )
    rivaDefaultVoice: str = Field(
        "English-US.Female-1",
        validation_alias=AliasChoices("RIVA_DEFAULT_VOICE", "rivaDefaultVoice"),
    )
    rivaSampleRateHz: int = Field(22050, validation_alias=AliasChoices("RIVA_SAMPLE_RATE_HZ", "rivaSampleRateHz"))
    a2fTransport: Literal["grpc", "http"] = Field("grpc", validation_alias=AliasChoices("A2F_TRANSPORT", "a2fTransport"))
    a2fProcessPath: str = Field("/api/process-audio", validation_alias=AliasChoices("A2F_PROCESS_PATH", "a2fProcessPath"))
    a2fTimeoutSeconds: float = Field(120.0, validation_alias=AliasChoices("A2F_TIMEOUT_SECONDS", "a2fTimeoutSeconds"))
    a2fGrpcChunkSeconds: float = Field(1.0, validation_alias=AliasChoices("A2F_GRPC_CHUNK_SECONDS", "a2fGrpcChunkSeconds"))
    a2fGrpcMaxAudioSeconds: float = Field(300.0, validation_alias=AliasChoices("A2F_GRPC_MAX_AUDIO_SECONDS", "a2fGrpcMaxAudioSeconds"))
    allowedOrigins: str = Field(
        "http://127.0.0.1:6310,http://localhost:6310",
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "allowedOrigins"),
    )
    resourceReservePercent: int = Field(10, validation_alias=AliasChoices("RESOURCE_RESERVE_PERCENT", "resourceReservePercent"))
    gpuMinFreeVramPercent: int = Field(10, validation_alias=AliasChoices("GPU_MIN_FREE_VRAM_PERCENT", "gpuMinFreeVramPercent"))
    ramMinFreePercent: int = Field(10, validation_alias=AliasChoices("RAM_MIN_FREE_PERCENT", "ramMinFreePercent"))
    diskMinFreePercent: int = Field(10, validation_alias=AliasChoices("DISK_MIN_FREE_PERCENT", "diskMinFreePercent"))
    projectDockerLabel: str = Field(
        "com.facespeed.project=NVIDIARiva-Audio2Face-facespeed",
        validation_alias=AliasChoices("PROJECT_DOCKER_LABEL", "projectDockerLabel"),
    )
    rivaContainerName: str = Field("facespeed-riva", validation_alias=AliasChoices("RIVA_CONTAINER_NAME", "rivaContainerName"))
    a2fContainerName: str = Field(
        "facespeed-audio2face-3d",
        validation_alias=AliasChoices("A2F_CONTAINER_NAME", "a2fContainerName"),
    )
    a2fContainerGrpcPort: int = Field(
        52000,
        validation_alias=AliasChoices("A2F_CONTAINER_GRPC_PORT", "a2fContainerGrpcPort"),
    )
    a2fContainerHttpPort: int = Field(
        8000,
        validation_alias=AliasChoices("A2F_CONTAINER_HTTP_PORT", "a2fContainerHttpPort"),
    )
    dockerCommandTimeoutSeconds: float = Field(
        30.0,
        validation_alias=AliasChoices("DOCKER_COMMAND_TIMEOUT_SECONDS", "dockerCommandTimeoutSeconds"),
    )
    rivaAsrEnabled: bool = Field(False, validation_alias=AliasChoices("RIVA_ASR_ENABLED", "rivaAsrEnabled"))
    rivaAsrHost: str = Field("127.0.0.1", validation_alias=AliasChoices("RIVA_ASR_HOST", "rivaAsrHost"))
    rivaAsrPort: int = Field(50151, validation_alias=AliasChoices("RIVA_ASR_PORT", "rivaAsrPort"))
    rivaAsrTimeoutSeconds: float = Field(30.0, validation_alias=AliasChoices("RIVA_ASR_TIMEOUT_SECONDS", "rivaAsrTimeoutSeconds"))
    rivaAsrLanguage: str = Field("en-US", validation_alias=AliasChoices("RIVA_ASR_LANGUAGE", "rivaAsrLanguage"))
    rivaAsrSampleRateHz: int = Field(16000, validation_alias=AliasChoices("RIVA_ASR_SAMPLE_RATE_HZ", "rivaAsrSampleRateHz"))
    doclingApiBaseUrl: str = Field(
        "http://127.0.0.1:8005",
        validation_alias=AliasChoices("DOCLING_API_BASE_URL", "doclingApiBaseUrl"),
    )
    embeddingApiBaseUrl: str = Field(
        "http://127.0.0.1:8006",
        validation_alias=AliasChoices("EMBEDDING_API_BASE_URL", "embeddingApiBaseUrl"),
    )
    doclingTimeoutSeconds: float = Field(
        60.0,
        validation_alias=AliasChoices("DOCLING_TIMEOUT_SECONDS", "doclingTimeoutSeconds"),
    )
    embeddingTimeoutSeconds: float = Field(
        30.0,
        validation_alias=AliasChoices("EMBEDDING_TIMEOUT_SECONDS", "embeddingTimeoutSeconds"),
    )
    rerankTimeoutSeconds: float = Field(
        30.0,
        validation_alias=AliasChoices("RERANK_TIMEOUT_SECONDS", "rerankTimeoutSeconds"),
    )
    ragStorageDir: Path = Field(Path("storage/rag"), validation_alias=AliasChoices("RAG_STORAGE_DIR", "ragStorageDir"))
    ragMinVectorScore: float = Field(0.2, validation_alias=AliasChoices("RAG_MIN_VECTOR_SCORE", "ragMinVectorScore"))
    ragMinConfidence: float = Field(0.45, validation_alias=AliasChoices("RAG_MIN_CONFIDENCE", "ragMinConfidence"))
    voiceChatMaxAudioSeconds: int = Field(
        45,
        validation_alias=AliasChoices("VOICE_CHAT_MAX_AUDIO_SECONDS", "voiceChatMaxAudioSeconds"),
    )
    pdfMaxUploadMb: int = Field(20, validation_alias=AliasChoices("PDF_MAX_UPLOAD_MB", "pdfMaxUploadMb"))

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
    settings.ragStorageDir.mkdir(parents=True, exist_ok=True)
    return settings
