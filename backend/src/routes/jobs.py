from fastapi import APIRouter, Depends, HTTPException

from src.dependencies import getJobService
from src.models.job import CreateJobRequest, Job
from src.services.job_service import JobService

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=Job)
def createJob(request: CreateJobRequest, jobService: JobService = Depends(getJobService)) -> Job:
    return jobService.createJob(request)


@router.get("/{jobId}", response_model=Job)
def getJob(jobId: str, jobService: JobService = Depends(getJobService)) -> Job:
    job = jobService.getJob(jobId)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@router.get("/{jobId}/logs", response_model=list[str])
def getJobLogs(jobId: str, maxLines: int = 200, jobService: JobService = Depends(getJobService)) -> list[str]:
    if jobService.getJob(jobId) is None:
        raise HTTPException(status_code=404, detail="job not found")
    return jobService.readJobLogs(jobId, maxLines)
