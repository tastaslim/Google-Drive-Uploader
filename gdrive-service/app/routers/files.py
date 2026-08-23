"""File CRUD endpoints: list (paginated), get, update, delete (single/bulk), real upload."""
import logging
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Query, Response, UploadFile

from app.config import settings
from app.dependencies import buildDriveClientForSharedDrive
from app.driveClient import extractIdFromUrlOrId
from app.schemas import (
    BulkDeleteResponse,
    CreateNativeFileRequest,
    DeleteFilesRequest,
    DeleteResult,
    FileResource,
    PaginatedFilesResponse,
    UpdateFileRequest,
)

logger = logging.getLogger("gdrive_service.routers.files")

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=PaginatedFilesResponse)
def listFiles(
    sharedDriveId: str = Query(default=None),
    sharedDriveIdOrUrl: str = Query(default=None, description="Alternative to sharedDriveId; accepts a Drive URL"),
    folderId: str | None = Query(default=None, description="Defaults to the Shared Drive root"),
    pageSize: int = Query(default=settings.defaultPageSize, ge=1, le=settings.maxPageSize),
    pageToken: str | None = Query(default=None),
    includeFolders: bool = Query(default=False),
) -> PaginatedFilesResponse:
    resolvedDriveId = _resolveDriveIdOrRaise(sharedDriveId, sharedDriveIdOrUrl)
    client = buildDriveClientForSharedDrive(resolvedDriveId)
    result = client.listFiles(
        parentFolderId=folderId, pageSize=pageSize, pageToken=pageToken, includeFolders=includeFolders,
    )
    return PaginatedFilesResponse(
        files=[FileResource(**f) for f in result.get("files", [])],
        nextPageToken=result.get("nextPageToken"),
    )


@router.post("/upload", response_model=FileResource, status_code=201)
def uploadFile(
    sharedDriveIdOrUrl: str = Form(...),
    folderId: str | None = Form(default=None),
    file: UploadFile = ...,
) -> FileResource:
    """Uploads a real file from the caller's machine, as-is — the browser
    "File upload" action, distinct from the synthetic bulk generator under
    /uploads. Streams from the incoming multipart body straight to Drive via
    the underlying SpooledTemporaryFile, so large real uploads don't need to
    be fully buffered in application memory."""
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    fileName = file.filename or "untitled"
    mimeType = file.content_type or "application/octet-stream"
    try:
        created = client.createFileFromStream(
            name=fileName,
            parentFolderId=folderId,
            mimeType=mimeType,
            stream=file.file,
            resumableChunkSizeBytes=settings.resumableChunkSizeBytes,
        )
        return FileResource(**created)
    except Exception as error:
        logger.exception("Failed to upload real file %r", fileName)
        raise HTTPException(status_code=400, detail=f"Failed to upload {fileName}: {error}")


@router.post("/native", response_model=FileResource, status_code=201)
def createNativeFile(request: CreateNativeFileRequest) -> FileResource:
    """Creates one empty native Google Workspace file (Doc/Sheet/Slide/Vid/
    Form/Drawing/Site/Apps Script) immediately — the browser right-click
    "Google Docs" etc. action. Has no binary content; Drive creates the file
    directly from the google-apps mimeType."""
    client = buildDriveClientForSharedDrive(request.sharedDriveIdOrUrl)
    nativeMimeType = f"application/vnd.google-apps.{request.appType}"
    try:
        created = client.createFile(
            name=request.name,
            parentFolderId=request.folderId,
            mimeType=nativeMimeType,
            content=b"",
            googleNativeMimeType=nativeMimeType,
        )
        return FileResource(**created)
    except Exception as error:
        logger.exception("Failed to create native file appType=%r", request.appType)
        raise HTTPException(status_code=400, detail=f"Failed to create {request.appType}: {error}")


@router.get("/{fileId}", response_model=FileResource)
def getFile(fileId: str, sharedDriveIdOrUrl: str = Query(...)) -> FileResource:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        return FileResource(**client.getFile(fileId))
    except Exception as error:
        raise HTTPException(status_code=404, detail=f"File {fileId} not found: {error}")


@router.get("/{fileId}/download")
def downloadFile(fileId: str, sharedDriveIdOrUrl: str = Query(...)) -> Response:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        fileMetadata = client.getFile(fileId)
        content = client.downloadFile(fileId)
    except Exception as error:
        raise HTTPException(status_code=404, detail=f"File {fileId} not found: {error}")
    mimeType = fileMetadata.get("mimeType", "application/octet-stream")
    fileName = fileMetadata.get("name", fileId)
    return Response(
        content=content,
        media_type=mimeType,
        headers={"Content-Disposition": buildContentDisposition(fileName)},
    )


def buildContentDisposition(fileName: str) -> str:
    """HTTP header values must be Latin-1; Drive file names routinely contain
    characters outside that range (smart quotes, narrow no-break spaces from
    Google-generated names, emoji, non-Latin scripts). Provide both a
    sanitized ASCII fallback (filename=) for older clients and the exact
    name UTF-8/percent-encoded (filename*=) per RFC 5987/6266, which is what
    modern browsers actually use to name the saved file."""
    asciiFallback = fileName.encode("ascii", errors="replace").decode("ascii").replace('"', "_")
    encodedName = quote(fileName, safe="")
    return f'attachment; filename="{asciiFallback}"; filename*=UTF-8\'\'{encodedName}'


@router.patch("/{fileId}", response_model=FileResource)
def updateFile(fileId: str, request: UpdateFileRequest) -> FileResource:
    client = buildDriveClientForSharedDrive(request.sharedDriveIdOrUrl)
    try:
        updated = client.updateFile(
            fileId=fileId,
            name=request.name,
            newParentFolderId=request.newParentFolderId,
            description=request.description,
            starred=request.starred,
            content=None,
            mimeType=None,
        )
        return FileResource(**updated)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to update file {fileId}: {error}")


@router.delete("/{fileId}", response_model=DeleteResult)
def deleteFile(
    fileId: str, sharedDriveIdOrUrl: str = Query(...), permanent: bool = Query(default=False),
) -> DeleteResult:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        if permanent:
            client.permanentlyDeleteFile(fileId)
        else:
            client.deleteFile(fileId)
        return DeleteResult(fileId=fileId, success=True)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to delete file {fileId}: {error}")


@router.post("/delete-batch", response_model=BulkDeleteResponse)
def deleteFilesBatch(request: DeleteFilesRequest) -> BulkDeleteResponse:
    client = buildDriveClientForSharedDrive(request.sharedDriveIdOrUrl)
    results: list[DeleteResult] = []
    for fileId in request.fileIds:
        try:
            if request.permanent:
                client.permanentlyDeleteFile(fileId)
            else:
                client.deleteFile(fileId)
            results.append(DeleteResult(fileId=fileId, success=True))
        except Exception as error:
            results.append(DeleteResult(fileId=fileId, success=False, errorMessage=str(error)))
    return BulkDeleteResponse(results=results)


def _resolveDriveIdOrRaise(sharedDriveId: str | None, sharedDriveIdOrUrl: str | None) -> str:
    if sharedDriveIdOrUrl:
        return extractIdFromUrlOrId(sharedDriveIdOrUrl)
    if sharedDriveId:
        return extractIdFromUrlOrId(sharedDriveId)
    raise HTTPException(status_code=422, detail="Provide either sharedDriveId or sharedDriveIdOrUrl")
