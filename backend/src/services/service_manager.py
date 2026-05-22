from pathlib import Path
import shutil
import subprocess

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
        self._containerNames: dict[ServiceName, str] = {
            ServiceName.riva: settings.rivaContainerName,
            ServiceName.audio2face: settings.a2fContainerName,
        }

    def listServices(self) -> list[ServiceStatus]:
        return [self.getStatus(serviceName) for serviceName in ServiceName]

    def getStatus(self, serviceName: ServiceName) -> ServiceStatus:
        state = self._states.get(serviceName, ServiceState.unknown)
        container = self._getDockerContainer(serviceName)
        if self.settings.serviceManagerMode == "docker" and container is not None:
            state = self._serviceStateFromContainerState(container["state"])
        return ServiceStatus(
            name=serviceName,
            state=state,
            healthy=state == ServiceState.running,
            detail=self._statusDetail(serviceName, state, container),
            managerMode=self.settings.serviceManagerMode,
            containerName=container["name"] if container is not None else self._containerNames.get(serviceName),
            containerState=container["state"] if container is not None else None,
            containerStatus=container["status"] if container is not None else None,
            containerImage=container["image"] if container is not None else None,
        )

    def runAction(self, serviceName: ServiceName, action: ServiceAction) -> ServiceStatus:
        if self.settings.serviceManagerMode == "docker" and serviceName in self._containerNames:
            self._runDockerAction(serviceName, action)
            return self.getStatus(serviceName)

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

    def _statusDetail(
        self,
        serviceName: ServiceName,
        state: ServiceState,
        container: dict[str, str] | None,
    ) -> str:
        if container is None:
            return f"{serviceName.value} is {state.value}; no project-labeled container is registered"
        return f"{serviceName.value} container {container['name']} is {container['status']}"

    def _getDockerContainer(self, serviceName: ServiceName) -> dict[str, str] | None:
        containerName = self._containerNames.get(serviceName)
        dockerPath = shutil.which("docker")
        if containerName is None or dockerPath is None:
            return None

        command = [
            dockerPath,
            "ps",
            "-a",
            "--filter",
            f"name=^/{containerName}$",
            "--filter",
            f"label={self.settings.projectDockerLabel}",
            "--format",
            "{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.State}}",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.settings.dockerCommandTimeoutSeconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None

        if result.returncode != 0:
            return None
        line = result.stdout.strip().splitlines()
        if not line:
            return None
        parts = line[0].split("\t", 3)
        if len(parts) != 4:
            return None
        return {"name": parts[0], "image": parts[1], "status": parts[2], "state": parts[3]}

    def _runDockerAction(self, serviceName: ServiceName, action: ServiceAction) -> None:
        container = self._getDockerContainer(serviceName)
        dockerPath = shutil.which("docker")
        if dockerPath is None:
            raise RuntimeError("docker CLI is not available")
        if container is None:
            raise RuntimeError(f"project-labeled container for {serviceName.value} was not found")
        if action == ServiceAction.stop and container["state"] != "running":
            appendLog(
                self._logPaths[serviceName],
                serviceName.value,
                "info",
                f"container {container['name']} already {container['state']}; stop treated as no-op",
            )
            return

        command = [dockerPath, action.value, container["name"]]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.settings.dockerCommandTimeoutSeconds,
            check=False,
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "docker command failed"
            appendLog(self._logPaths[serviceName], serviceName.value, "error", message)
            raise RuntimeError(message)

        appendLog(
            self._logPaths[serviceName],
            serviceName.value,
            "info",
            f"docker {action.value} completed for project container {container['name']}",
        )

    def _serviceStateFromContainerState(self, containerState: str) -> ServiceState:
        if containerState == "running":
            return ServiceState.running
        if containerState in {"created", "exited", "dead", "paused"}:
            return ServiceState.stopped
        return ServiceState.unknown
