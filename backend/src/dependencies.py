from functools import lru_cache

from src.config import getSettings
from src.services.audio2face_client import MockAudio2FaceClient, NvidiaAudio2FaceClient
from src.services.job_service import JobService
from src.services.riva_client import MockRivaTtsClient, NvidiaRivaTtsClient
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
