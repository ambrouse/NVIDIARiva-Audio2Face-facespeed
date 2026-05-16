from pathlib import Path

from src.config import Settings
from src.models.service import ServiceAction, ServiceName, ServiceState, ServiceStatus
from src.utils.logging import appendLog, readTail


class ServiceManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._states: dict[ServiceName, ServiceState] = {
            ServiceName.riva: ServiceState.stopped,
            ServiceName.audio2face: ServiceState.stopped,
            ServiceName.backendWorker: ServiceState.running,
        }
        self._logPaths: dict[ServiceName, Path] = {
            ServiceName.riva: settings.logDir / "riva" / "service.log",
            ServiceName.audio2face: settings.logDir / "audio2face" / "service.log",
            ServiceName.backendWorker: settings.logDir / "backend" / "worker.log",
        }

    def listServices(self) -> list[ServiceStatus]:
        return [self.getStatus(serviceName) for serviceName in ServiceName]

    def getStatus(self, serviceName: ServiceName) -> ServiceStatus:
        state = self._states.get(serviceName, ServiceState.unknown)
        return ServiceStatus(
            name=serviceName,
            state=state,
            healthy=state == ServiceState.running,
            detail=f"{serviceName.value} is {state.value}",
        )

    def runAction(self, serviceName: ServiceName, action: ServiceAction) -> ServiceStatus:
        if action == ServiceAction.start:
            self._states[serviceName] = ServiceState.running
        elif action == ServiceAction.stop:
            self._states[serviceName] = ServiceState.stopped
        elif action == ServiceAction.restart:
            self._states[serviceName] = ServiceState.running

        appendLog(
            self._logPaths[serviceName],
            serviceName.value,
            "info",
            f"service action {action.value} completed in {self.settings.serviceManagerMode} mode",
        )
        return self.getStatus(serviceName)

    def readLogs(self, serviceName: ServiceName, maxLines: int = 200) -> list[str]:
        return readTail(self._logPaths[serviceName], maxLines)

    def logPath(self, serviceName: ServiceName) -> Path:
        return self._logPaths[serviceName]
