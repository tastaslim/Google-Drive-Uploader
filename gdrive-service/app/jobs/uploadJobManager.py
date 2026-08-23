"""32-thread background upload job engine backed by a bounded thread pool."""
import logging
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.driveClient import DriveClient
from app.generators.largeFileStream import LARGE_FILE_EXTENSION, LARGE_FILE_MIME_TYPE, SyntheticByteStream
from app.generators.registry import buildActiveRegistry, generateFileForIndex
from app.generators.sizeDistribution import buildSizeAssignments, planSizeDistribution
from app.jobs.models import JobStatus, UploadJob, UploadJobError, UploadJobEvent

logger = logging.getLogger("gdrive_service.uploadJobManager")


class UploadJobManager:
    """Runs all file uploads for all jobs through a single shared, bounded
    thread pool (default 32 workers) so concurrent jobs share the same
    upload concurrency budget instead of each spawning their own pool."""

    def __init__(self, maxWorkers: int = settings.maxWorkers):
        self._jobs: dict[str, UploadJob] = {}
        self._jobsLock = threading.Lock()
        self._jobDispatchExecutor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gdrive-job-dispatch")
        self._uploadExecutor = ThreadPoolExecutor(max_workers=maxWorkers, thread_name_prefix="gdrive-upload")

    def submitUploadJob(
        self, sharedDriveId: str, destinationFolderId: str, count: int, averageFileSizeBytes: int,
        excludedExtensions: list[str] | None = None,
    ) -> UploadJob:
        plan = planSizeDistribution(count, averageFileSizeBytes)
        job = UploadJob(
            sharedDriveId=sharedDriveId,
            destinationFolderId=destinationFolderId,
            requestedCount=count,
            averageFileSizeBytes=averageFileSizeBytes,
            excludedExtensions=excludedExtensions or [],
            smallFileCount=plan.smallFileCount,
            largeFileCountsByBucket=plan.largeFileCountsByBucket,
        )
        with self._jobsLock:
            self._jobs[job.jobId] = job
        self._jobDispatchExecutor.submit(self._runJob, job, plan)
        return job

    def getJob(self, jobId: str) -> UploadJob | None:
        with self._jobsLock:
            return self._jobs.get(jobId)

    def listJobs(self) -> list[UploadJob]:
        with self._jobsLock:
            return list(self._jobs.values())

    def cancelJob(self, jobId: str) -> bool:
        job = self.getJob(jobId)
        if job is None:
            return False
        with job.lock:
            if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.COMPLETED_WITH_ERRORS):
                return False
            job.cancelRequested = True
        return True

    def _runJob(self, job: UploadJob, plan) -> None:
        with job.lock:
            job.status = JobStatus.RUNNING
            job.startedAt = time.time()

        driveClient = DriveClient(job.sharedDriveId)
        uploadLock = threading.Lock()
        sizeAssignments = buildSizeAssignments(plan, seed=job.jobId)
        activeRegistry = buildActiveRegistry(job.excludedExtensions)

        def _uploadOne(index: int) -> None:
            with job.lock:
                if job.cancelRequested:
                    return
            rng = random.Random(f"{job.jobId}-{index}")
            bucketLabel, largeSizeBytes = sizeAssignments[index]
            try:
                if bucketLabel == "small":
                    fileName, formatSpec, content = generateFileForIndex(index, rng, registry=activeRegistry)
                    extension = formatSpec.extension
                    sizeBytes = len(content)
                    job.recordEvent(UploadJobEvent(
                        fileIndex=index, fileName=fileName, extension=extension,
                        sizeBytes=sizeBytes, status="uploading",
                    ))
                    createdFile = driveClient.createFile(
                        name=fileName,
                        parentFolderId=job.destinationFolderId,
                        mimeType=formatSpec.mimeType,
                        content=content,
                        googleNativeMimeType=formatSpec.googleNativeMimeType,
                    )
                else:
                    extension = LARGE_FILE_EXTENSION
                    fileName = f"file_{index}_{bucketLabel}_{rng.randint(1000, 9999)}.{extension}"
                    sizeBytes = largeSizeBytes
                    job.recordEvent(UploadJobEvent(
                        fileIndex=index, fileName=fileName, extension=extension,
                        sizeBytes=sizeBytes, status="uploading",
                    ))
                    stream = SyntheticByteStream(totalSizeBytes=largeSizeBytes, seed=hash(f"{job.jobId}-{index}"))
                    createdFile = driveClient.createFileFromStream(
                        name=fileName,
                        parentFolderId=job.destinationFolderId,
                        mimeType=LARGE_FILE_MIME_TYPE,
                        stream=stream,
                        resumableChunkSizeBytes=settings.resumableChunkSizeBytes,
                    )
                with uploadLock, job.lock:
                    job.uploadedCount += 1
                    job.uploadedFileIds.append(createdFile["id"])
                job.recordEvent(UploadJobEvent(
                    fileIndex=index, fileName=fileName, extension=extension,
                    sizeBytes=sizeBytes, status="uploaded",
                ))
            except Exception as uploadError:
                logger.exception("Failed to upload file at index %d for job %s", index, job.jobId)
                with uploadLock, job.lock:
                    job.failedCount += 1
                    job.errors.append(
                        UploadJobError(fileIndex=index, fileName=f"file_{index}", errorMessage=str(uploadError))
                    )
                job.recordEvent(UploadJobEvent(
                    fileIndex=index, fileName=f"file_{index}", extension="", sizeBytes=None, status="failed",
                ))

        futures = [self._uploadExecutor.submit(_uploadOne, i) for i in range(job.requestedCount)]
        for future in futures:
            future.result()

        with job.lock:
            job.finishedAt = time.time()
            if job.cancelRequested:
                job.status = JobStatus.CANCELLED
            elif job.failedCount == 0:
                job.status = JobStatus.COMPLETED
            elif job.uploadedCount > 0:
                job.status = JobStatus.COMPLETED_WITH_ERRORS
            else:
                job.status = JobStatus.FAILED


uploadJobManager = UploadJobManager()
