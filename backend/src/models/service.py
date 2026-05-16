from enum import StrEnum

from pydantic import BaseModel


class ServiceName(StrEnum):
    riva = "riva"
    audio2face = "audio2face"
    backendWorker = "backend-worker"


class ServiceAction(StrEnum):
    start = "start"
    stop = "stop"
    restart = "restart"


class ServiceState(StrEnum):
    running = "running"
    stopped = "stopped"
    unknown = "unknown"


class ServiceStatus(BaseModel):
    name: ServiceName
    state: ServiceState
    healthy: bool
    detail: str
