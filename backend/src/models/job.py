from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class JobState(StrEnum):
    queued = "queued"
    validatingText = "validating_text"
    generatingSpeech = "generating_speech"
    speechReady = "speech_ready"
    sendingToA2f = "sending_to_a2f"
    animatingFace = "animating_face"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class OutputMode(StrEnum):
    preview = "preview"
    export = "export"
    stream = "stream"


class CreateJobRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    voice: str = Field(default="English-US.Female-1", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    language: str = Field(default="en-US", min_length=2, max_length=16, pattern=r"^[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})?$")
    a2fProfile: str = Field(default="default", min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    outputMode: OutputMode = OutputMode.preview

    @field_validator("text")
    @classmethod
    def textMustContainNonWhitespace(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("text cannot be empty")
        return normalized


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    state: JobState = JobState.queued
    text: str
    voice: str
    language: str
    a2fProfile: str
    outputMode: OutputMode
    audioPath: str | None = None
    resultPath: str | None = None
    audioUrl: str | None = None
    animationUrl: str | None = None
    error: str | None = None
