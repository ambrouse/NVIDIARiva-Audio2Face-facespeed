from datetime import datetime, timezone
from pathlib import Path


def appendLog(path: Path, service: str, level: str, message: str, jobId: str = "-") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    safeMessage = message.replace("\n", " ").replace("\r", " ")
    with path.open("a", encoding="utf-8") as logFile:
        logFile.write(f"{timestamp} {level.upper()} {service} {jobId} {safeMessage}\n")


def readTail(path: Path, maxLines: int = 200) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return lines[-max(1, min(maxLines, 1000)):]
