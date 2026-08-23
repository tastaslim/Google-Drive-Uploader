"""Pydantic request/response models for the Shared Drive FastAPI service."""
from pydantic import BaseModel, Field, field_validator

from app.driveClient import extractIdFromUrlOrId
from app.generators.sizeDistribution import SMALL_FILE_MAX_BYTES


class UploadFilesRequest(BaseModel):
    count: int = Field(..., ge=1, le=200000, description="Number of files to generate and upload")
    sharedDriveIdOrUrl: str = Field(..., description="Shared Drive ID or its Drive URL")
    folderId: str | None = Field(
        default=None,
        description="Destination folder ID. Defaults to the Shared Drive root if omitted.",
    )
    averageFileSizeBytes: int = Field(
        default=SMALL_FILE_MAX_BYTES // 2,
        ge=1024,
        description=(
            "Target average file size across the batch. Based on this, a static number of large "
            "files (50MB/100MB/500MB/1GB/5GB buckets, streamed directly to the upload without ever "
            "being held fully in memory) are mixed in with small files (<10MB, the existing 86 "
            "generated formats) to approximate the requested average."
        ),
    )
    excludedExtensions: list[str] = Field(
        default_factory=list,
        description="Format extensions (e.g. 'pdf', 'mp4') to exclude from generation for this job.",
    )

    @field_validator("sharedDriveIdOrUrl")
    @classmethod
    def _resolveSharedDriveId(cls, value: str) -> str:
        return extractIdFromUrlOrId(value)


class UploadJobResponse(BaseModel):
    jobId: str
    sharedDriveId: str
    destinationFolderId: str
    requestedCount: int
    averageFileSizeBytes: int
    excludedExtensions: list[str]
    smallFileCount: int
    largeFileCountsByBucket: dict[str, int]
    status: str
    uploadedCount: int
    failedCount: int
    remainingCount: int
    createdAt: float
    startedAt: float | None
    finishedAt: float | None
    elapsedSeconds: float | None
    errors: list[dict]
    recentEvents: list[dict]


class SupportedFormatsResponse(BaseModel):
    extensions: list[str]


class FileResource(BaseModel):
    id: str
    name: str
    mimeType: str
    parents: list[str] | None = None
    driveId: str | None = None
    size: str | None = None
    createdTime: str | None = None
    modifiedTime: str | None = None
    trashed: bool | None = None
    md5Checksum: str | None = None
    webViewLink: str | None = None
    starred: bool | None = None
    description: str | None = None


class PaginatedFilesResponse(BaseModel):
    files: list[FileResource]
    nextPageToken: str | None = None


class FolderSearchResultItem(BaseModel):
    id: str
    name: str
    path: str
    createdTime: str | None = None
    modifiedTime: str | None = None


class FolderSearchResponse(BaseModel):
    folders: list[FolderSearchResultItem]
    nextPageToken: str | None = None


class FolderStatsResponse(BaseModel):
    folderId: str
    fileCount: int
    folderCount: int
    totalSizeBytes: int


class CreateFolderRequest(BaseModel):
    sharedDriveIdOrUrl: str
    name: str
    parentFolderId: str | None = None
    description: str | None = None

    @field_validator("sharedDriveIdOrUrl")
    @classmethod
    def _resolveSharedDriveId(cls, value: str) -> str:
        return extractIdFromUrlOrId(value)


class UpdateFolderRequest(BaseModel):
    sharedDriveIdOrUrl: str
    name: str | None = None
    newParentFolderId: str | None = None
    description: str | None = None
    starred: bool | None = None

    @field_validator("sharedDriveIdOrUrl")
    @classmethod
    def _resolveSharedDriveId(cls, value: str) -> str:
        return extractIdFromUrlOrId(value)


class UpdateFileRequest(BaseModel):
    sharedDriveIdOrUrl: str
    name: str | None = None
    newParentFolderId: str | None = None
    description: str | None = None
    starred: bool | None = None

    @field_validator("sharedDriveIdOrUrl")
    @classmethod
    def _resolveSharedDriveId(cls, value: str) -> str:
        return extractIdFromUrlOrId(value)


NATIVE_GOOGLE_APP_TYPES = {
    "document", "spreadsheet", "presentation", "vid", "form", "drawing", "site", "script",
}


class CreateNativeFileRequest(BaseModel):
    sharedDriveIdOrUrl: str
    appType: str = Field(..., description=f"One of: {', '.join(sorted(NATIVE_GOOGLE_APP_TYPES))}")
    name: str = Field(default="Untitled")
    folderId: str | None = Field(default=None, description="Defaults to the Shared Drive root.")

    @field_validator("sharedDriveIdOrUrl")
    @classmethod
    def _resolveSharedDriveId(cls, value: str) -> str:
        return extractIdFromUrlOrId(value)

    @field_validator("appType")
    @classmethod
    def _validateAppType(cls, value: str) -> str:
        if value not in NATIVE_GOOGLE_APP_TYPES:
            raise ValueError(f"appType must be one of: {', '.join(sorted(NATIVE_GOOGLE_APP_TYPES))}")
        return value


class DeleteFilesRequest(BaseModel):
    sharedDriveIdOrUrl: str
    fileIds: list[str] = Field(..., min_length=1, max_length=1000)
    permanent: bool = False

    @field_validator("sharedDriveIdOrUrl")
    @classmethod
    def _resolveSharedDriveId(cls, value: str) -> str:
        return extractIdFromUrlOrId(value)


class DeleteResult(BaseModel):
    fileId: str
    success: bool
    errorMessage: str | None = None


class BulkDeleteResponse(BaseModel):
    results: list[DeleteResult]


class SharedDriveResource(BaseModel):
    id: str
    name: str
    createdTime: str | None = None


class PaginatedSharedDrivesResponse(BaseModel):
    drives: list[SharedDriveResource]
    nextPageToken: str | None = None


class FolderUploadResultItem(BaseModel):
    relativePath: str
    success: bool
    fileId: str | None = None
    errorMessage: str | None = None


class FolderUploadResult(BaseModel):
    results: list[FolderUploadResultItem]
