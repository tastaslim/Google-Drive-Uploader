"""In-memory job state models for background upload jobs."""
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UploadJobError:
    fileIndex: int
    fileName: str
    errorMessage: str


@dataclass
class UploadJobEvent:
    """One line of the live per-file feed — generated, uploading, or uploaded/failed."""
    fileIndex: int
    fileName: str
    extension: str
    sizeBytes: int | None
    status: str  # "generated" | "uploading" | "uploaded" | "failed"
    timestamp: float = field(default_factory=time.time)


_MAX_RECENT_EVENTS = 200


@dataclass
class UploadJob:
    jobId: str = field(default_factory=lambda: str(uuid.uuid4()))
    sharedDriveId: str = ""
    destinationFolderId: str = ""
    requestedCount: int = 0
    averageFileSizeBytes: int = 0
    excludedExtensions: list[str] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    uploadedCount: int = 0
    failedCount: int = 0
    createdAt: float = field(default_factory=time.time)
    startedAt: float | None = None
    finishedAt: float | None = None
    errors: list[UploadJobError] = field(default_factory=list)
    uploadedFileIds: list[str] = field(default_factory=list)
    cancelRequested: bool = False
    smallFileCount: int = 0
    largeFileCountsByBucket: dict[str, int] = field(default_factory=dict)
    recentEvents: list[UploadJobEvent] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def recordEvent(self, event: UploadJobEvent) -> None:
        with self.lock:
            self.recentEvents.append(event)
            if len(self.recentEvents) > _MAX_RECENT_EVENTS:
                self.recentEvents = self.recentEvents[-_MAX_RECENT_EVENTS:]

    def toResponseDict(self) -> dict:
        with self.lock:
            elapsedSeconds = None
            if self.startedAt is not None:
                endTime = self.finishedAt or time.time()
                elapsedSeconds = round(endTime - self.startedAt, 2)
            return {
                "jobId": self.jobId,
                "sharedDriveId": self.sharedDriveId,
                "destinationFolderId": self.destinationFolderId,
                "requestedCount": self.requestedCount,
                "averageFileSizeBytes": self.averageFileSizeBytes,
                "excludedExtensions": self.excludedExtensions,
                "smallFileCount": self.smallFileCount,
                "largeFileCountsByBucket": self.largeFileCountsByBucket,
                "status": self.status.value,
                "uploadedCount": self.uploadedCount,
                "failedCount": self.failedCount,
                "remainingCount": max(0, self.requestedCount - self.uploadedCount - self.failedCount),
                "createdAt": self.createdAt,
                "startedAt": self.startedAt,
                "finishedAt": self.finishedAt,
                "elapsedSeconds": elapsedSeconds,
                "errors": [
                    {"fileIndex": e.fileIndex, "fileName": e.fileName, "errorMessage": e.errorMessage}
                    for e in self.errors[-50:]
                ],
                "recentEvents": [
                    {
                        "fileIndex": e.fileIndex, "fileName": e.fileName, "extension": e.extension,
                        "sizeBytes": e.sizeBytes, "status": e.status, "timestamp": e.timestamp,
                    }
                    for e in self.recentEvents[-50:]
                ],
            }
