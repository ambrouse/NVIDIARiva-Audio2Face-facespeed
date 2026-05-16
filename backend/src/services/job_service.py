from pathlib import Path

from src.config import Settings
from src.models.job import CreateJobRequest, Job, JobState
from src.services.audio2face_client import Audio2FaceClient
from src.services.riva_client import RivaTtsClient
from src.utils.logging import appendLog, readTail


class JobService:
    def __init__(self, settings: Settings, rivaClient: RivaTtsClient, audio2FaceClient: Audio2FaceClient) -> None:
        self.settings = settings
        self.rivaClient = rivaClient
        self.audio2FaceClient = audio2FaceClient
        self.jobs: dict[str, Job] = {}

    def createJob(self, request: CreateJobRequest) -> Job:
        job = Job(
            text=request.text,
            voice=request.voice,
            language=request.language,
            a2fProfile=request.a2fProfile,
            outputMode=request.outputMode,
        )
        self.jobs[job.id] = job
        self._runPipeline(job)
        return job

    def getJob(self, jobId: str) -> Job | None:
        return self.jobs.get(jobId)

    def readJobLogs(self, jobId: str, maxLines: int = 200) -> list[str]:
        return readTail(self._jobLogPath(jobId), maxLines)

    def _runPipeline(self, job: Job) -> None:
        try:
            self._setState(job, JobState.validatingText)
            normalizedText = " ".join(job.text.split())
            if not normalizedText:
                raise ValueError("text cannot be empty")

            self._setState(job, JobState.generatingSpeech)
            audioPath = self.settings.outputDir / "audio" / f"{job.id}.wav"
            self.rivaClient.synthesize(normalizedText, job.voice, job.language, audioPath)
            job.audioPath = str(audioPath)
            self._setState(job, JobState.speechReady)

            self._setState(job, JobState.sendingToA2f)
            resultPath = self.settings.outputDir / "a2f" / f"{job.id}.json"
            self.audio2FaceClient.processAudio(audioPath, job.a2fProfile, job.outputMode.value, resultPath)
            job.resultPath = str(resultPath)

            self._setState(job, JobState.animatingFace)
            self._setState(job, JobState.completed)
        except Exception as exc:
            job.state = JobState.failed
            job.error = str(exc)
            self._log(job, "error", str(exc))

    def _setState(self, job: Job, state: JobState) -> None:
        job.state = state
        self._log(job, "info", f"job state changed to {state.value}")

    def _log(self, job: Job, level: str, message: str) -> None:
        appendLog(self._jobLogPath(job.id), "job", level, message, job.id)

    def _jobLogPath(self, jobId: str) -> Path:
        return self.settings.logDir / "jobs" / f"{jobId}.log"
