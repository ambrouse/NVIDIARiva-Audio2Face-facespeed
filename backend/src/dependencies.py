from functools import lru_cache

from src.config import getSettings
from src.services.audio2face_client import MockAudio2FaceClient, NvidiaAudio2FaceClient
from src.services.docling_client import DoclingClient
from src.services.embedding_client import EmbeddingRerankClient
from src.services.job_service import JobService
from src.services.llm_client import LlmClient
from src.services.rag_service import RagService
from src.services.riva_client import NvidiaRivaAsrClient, MockRivaTtsClient, NvidiaRivaTtsClient, RivaAsrClient
from src.services.service_manager import ServiceManager
from src.services.system_check import SystemCheckService


@lru_cache
def getServiceManager() -> ServiceManager:
    return ServiceManager(getSettings())


@lru_cache
def getJobService() -> JobService:
    settings = getSettings()
    if settings.pipelineMode == "nvidia":
        rivaClient = NvidiaRivaTtsClient(settings)
        audio2FaceClient = NvidiaAudio2FaceClient(settings)
    elif settings.pipelineMode == "riva":
        rivaClient = NvidiaRivaTtsClient(settings)
        audio2FaceClient = MockAudio2FaceClient()
    else:
        rivaClient = MockRivaTtsClient()
        audio2FaceClient = MockAudio2FaceClient()
    return JobService(settings, rivaClient, audio2FaceClient)


@lru_cache
def getSystemCheckService() -> SystemCheckService:
    return SystemCheckService()


@lru_cache
def getRagService() -> RagService:
    settings = getSettings()
    return RagService(settings, getJobService(), DoclingClient(settings), EmbeddingRerankClient(settings), LlmClient(settings))


@lru_cache
def getRivaAsrClient() -> RivaAsrClient:
    return NvidiaRivaAsrClient(getSettings())
