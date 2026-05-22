from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from src.config import Settings, getSettings

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("/audio/{jobId}.wav")
def getAudioArtifact(jobId: str, settings: Settings = Depends(getSettings)) -> FileResponse:
    _validateJobId(jobId)
    return _artifactResponse(settings.outputDir / "audio" / f"{jobId}.wav", settings.outputDir, "audio/wav")


@router.get("/animation/{jobId}.json")
def getAnimationArtifact(jobId: str, settings: Settings = Depends(getSettings)) -> FileResponse:
    _validateJobId(jobId)
    return _artifactResponse(settings.outputDir / "animation" / f"{jobId}.json", settings.outputDir, "application/json")


def _validateJobId(jobId: str) -> None:
    try:
        UUID(jobId)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="artifact not found") from exc


def _artifactResponse(path: Path, outputDir: Path, mediaType: str) -> FileResponse:
    root = outputDir.resolve()
    resolved = path.resolve()
    if root not in resolved.parents:
        raise HTTPException(status_code=404, detail="artifact not found")
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="artifact not found")
    return FileResponse(resolved, media_type=mediaType)
