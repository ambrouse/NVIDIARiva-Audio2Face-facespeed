from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


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
    text: str = Field(min_length=1, max_length=5000)
    voice: str = Field(default="default", min_length=1, max_length=64)
    language: str = Field(default="vi-VN", min_length=2, max_length=16)
    a2fProfile: str = Field(default="default", min_length=1, max_length=64)
    outputMode: OutputMode = OutputMode.preview


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
    error: str | None = None
