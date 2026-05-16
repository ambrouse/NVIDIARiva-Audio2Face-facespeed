import shutil
import subprocess


class SystemCheckService:
    def getChecks(self) -> list[dict[str, str | bool]]:
        return [
            self._commandCheck("nvidia-smi", ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]),
            self._commandCheck("docker", ["docker", "--version"]),
            self._commandCheck("python", ["python", "--version"]),
            self._commandCheck("node", ["node", "--version"]),
        ]

    def _commandCheck(self, name: str, command: list[str]) -> dict[str, str | bool]:
        executable = shutil.which(command[0])
        if executable is None:
            return {"name": name, "ok": False, "detail": f"{command[0]} not found"}
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
            detail = result.stdout.strip() or result.stderr.strip() or "available"
            return {"name": name, "ok": result.returncode == 0, "detail": detail}
        except subprocess.TimeoutExpired:
            return {"name": name, "ok": False, "detail": "check timed out"}
