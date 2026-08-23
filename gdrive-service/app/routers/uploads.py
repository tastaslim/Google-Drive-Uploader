"""Bulk file upload endpoints backed by background jobs."""
from fastapi import APIRouter, HTTPException

from app.generators.registry import FORMAT_EXTENSIONS
from app.jobs.uploadJobManager import uploadJobManager
from app.schemas import SupportedFormatsResponse, UploadFilesRequest, UploadJobResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/formats", response_model=SupportedFormatsResponse)
def listSupportedFormats() -> SupportedFormatsResponse:
    return SupportedFormatsResponse(extensions=FORMAT_EXTENSIONS)


@router.post("", response_model=UploadJobResponse, status_code=202)
def createUploadJob(request: UploadFilesRequest) -> UploadJobResponse:
    job = uploadJobManager.submitUploadJob(
        sharedDriveId=request.sharedDriveIdOrUrl,
        destinationFolderId=request.folderId or request.sharedDriveIdOrUrl,
        count=request.count,
        averageFileSizeBytes=request.averageFileSizeBytes,
        excludedExtensions=request.excludedExtensions,
    )
    return UploadJobResponse(**job.toResponseDict())


@router.get("/{jobId}", response_model=UploadJobResponse)
def getUploadJob(jobId: str) -> UploadJobResponse:
    job = uploadJobManager.getJob(jobId)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {jobId} not found")
    return UploadJobResponse(**job.toResponseDict())


@router.get("", response_model=list[UploadJobResponse])
def listUploadJobs() -> list[UploadJobResponse]:
    return [UploadJobResponse(**job.toResponseDict()) for job in uploadJobManager.listJobs()]


@router.post("/{jobId}/cancel", response_model=UploadJobResponse)
def cancelUploadJob(jobId: str) -> UploadJobResponse:
    job = uploadJobManager.getJob(jobId)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {jobId} not found")
    cancelled = uploadJobManager.cancelJob(jobId)
    if not cancelled:
        raise HTTPException(status_code=409, detail=f"Job {jobId} cannot be cancelled in its current state")
    return UploadJobResponse(**job.toResponseDict())
