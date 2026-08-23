"""Folder CRUD endpoints: create, list (paginated), get, update, delete, download-as-zip, real folder upload."""
import logging
import zipfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.dependencies import buildDriveClientForSharedDrive
from app.driveClient import DriveClient, extractIdFromUrlOrId
from app.routers.files import buildContentDisposition
from app.schemas import (
    CreateFolderRequest,
    DeleteResult,
    FileResource,
    FolderSearchResponse,
    FolderSearchResultItem,
    FolderStatsResponse,
    FolderUploadResult,
    FolderUploadResultItem,
    PaginatedFilesResponse,
    UpdateFolderRequest,
)

logger = logging.getLogger("gdrive_service.routers.folders")

router = APIRouter(prefix="/folders", tags=["folders"])


@router.post("/upload-batch", response_model=FolderUploadResult, status_code=201)
def uploadFolderBatch(
    sharedDriveIdOrUrl: str = Form(...),
    parentFolderId: str | None = Form(default=None),
    relativePaths: list[str] = Form(...),
    files: list[UploadFile] = ...,
) -> FolderUploadResult:
    """Uploads a real local folder tree (the browser "Folder upload" action),
    recreating its subfolder structure in the Shared Drive. relativePaths[i]
    corresponds to files[i] and looks like "TopFolder/sub/file.txt" (a
    webkitdirectory-style relative path) — subfolders are created once and
    reused for every file that shares that ancestor, not once per file."""
    if len(relativePaths) != len(files):
        raise HTTPException(
            status_code=422,
            detail=f"relativePaths ({len(relativePaths)}) and files ({len(files)}) counts must match",
        )

    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    folderIdByPath: dict[str, str] = {}

    def _resolveParentFolderId(pathSegments: list[str]) -> str:
        if not pathSegments:
            return parentFolderId or client.resolveRootFolderId()
        pathKey = "/".join(pathSegments)
        if pathKey in folderIdByPath:
            return folderIdByPath[pathKey]
        grandParentId = _resolveParentFolderId(pathSegments[:-1])
        folder = client.getOrCreateFolderByName(name=pathSegments[-1], parentFolderId=grandParentId)
        folderIdByPath[pathKey] = folder["id"]
        return folder["id"]

    results: list[FolderUploadResultItem] = []
    for relativePath, uploadFile in zip(relativePaths, files):
        pathSegments = [segment for segment in relativePath.split("/") if segment]
        fileName = pathSegments[-1] if pathSegments else (uploadFile.filename or "untitled")
        subfolderSegments = pathSegments[:-1]
        try:
            destinationFolderId = _resolveParentFolderId(subfolderSegments)
            created = client.createFileFromStream(
                name=fileName,
                parentFolderId=destinationFolderId,
                mimeType=uploadFile.content_type or "application/octet-stream",
                stream=uploadFile.file,
                resumableChunkSizeBytes=settings.resumableChunkSizeBytes,
            )
            results.append(FolderUploadResultItem(relativePath=relativePath, success=True, fileId=created.get("id")))
        except Exception as error:
            logger.exception("Failed to upload %r during folder upload", relativePath)
            results.append(FolderUploadResultItem(relativePath=relativePath, success=False, errorMessage=str(error)))

    return FolderUploadResult(results=results)


@router.post("", response_model=FileResource, status_code=201)
def createFolder(request: CreateFolderRequest) -> FileResource:
    client = buildDriveClientForSharedDrive(request.sharedDriveIdOrUrl)
    try:
        created = client.createFolder(
            name=request.name,
            parentFolderId=request.parentFolderId,
            description=request.description,
        )
        return FileResource(**created)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to create folder: {error}")


@router.get("", response_model=PaginatedFilesResponse)
def listFolders(
    sharedDriveIdOrUrl: str = Query(...),
    parentFolderId: str | None = Query(default=None, description="Defaults to the Shared Drive root"),
    pageSize: int = Query(default=settings.defaultPageSize, ge=1, le=settings.maxPageSize),
    pageToken: str | None = Query(default=None),
) -> PaginatedFilesResponse:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    result = client.listFolders(parentFolderId=parentFolderId, pageSize=pageSize, pageToken=pageToken)
    return PaginatedFilesResponse(
        files=[FileResource(**f) for f in result.get("files", [])],
        nextPageToken=result.get("nextPageToken"),
    )


@router.get("/search", response_model=FolderSearchResponse)
def searchFolders(
    sharedDriveIdOrUrl: str = Query(...),
    query: str = Query(..., min_length=1, description="Substring to match against folder names, drive-wide"),
    pageSize: int = Query(default=settings.defaultPageSize, ge=1, le=settings.maxPageSize),
    pageToken: str | None = Query(default=None),
) -> FolderSearchResponse:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    result = client.searchFolders(nameContains=query, pageSize=pageSize, pageToken=pageToken)
    matches = result.get("files", [])

    def _resolveOne(match: dict) -> FolderSearchResultItem:
        return FolderSearchResultItem(
            id=match["id"],
            name=match["name"],
            path=client.resolveFolderPath(match["id"], match["name"], match.get("parents")),
            createdTime=match.get("createdTime"),
            modifiedTime=match.get("modifiedTime"),
        )

    if matches:
        with ThreadPoolExecutor(max_workers=min(len(matches), 10), thread_name_prefix="gdrive-folder-path") as pool:
            folders = list(pool.map(_resolveOne, matches))
    else:
        folders = []

    return FolderSearchResponse(folders=folders, nextPageToken=result.get("nextPageToken"))


@router.get("/{folderId}/stats", response_model=FolderStatsResponse)
def getFolderStats(folderId: str, sharedDriveIdOrUrl: str = Query(...)) -> FolderStatsResponse:
    """Recursively computes a folder's total nested file/subfolder count and
    size — expensive for large trees, so the UI calls this lazily per folder
    row rather than for every folder in a listing up front."""
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        stats = client.computeFolderStats(folderId)
    except Exception as error:
        raise HTTPException(status_code=404, detail=f"Failed to compute stats for folder {folderId}: {error}")
    return FolderStatsResponse(folderId=folderId, **stats)


@router.get("/{folderId}", response_model=FileResource)
def getFolder(folderId: str, sharedDriveIdOrUrl: str = Query(...)) -> FileResource:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        return FileResource(**client.getFolder(folderId))
    except Exception as error:
        raise HTTPException(status_code=404, detail=f"Folder {folderId} not found: {error}")


class _ChunkCollectingWriter:
    """A minimal writable file-like object that buffers bytes written to it
    and can be drained. zipfile.ZipFile writes through this instead of a
    real file/BytesIO, letting us yield each chunk to StreamingResponse as
    soon as it's produced rather than building the whole zip in memory."""

    def __init__(self):
        self._chunks: list[bytes] = []
        self._totalBytesWritten = 0

    def write(self, data: bytes) -> int:
        self._chunks.append(data)
        self._totalBytesWritten += len(data)
        return len(data)

    def flush(self) -> None:
        pass

    def tell(self) -> int:
        return self._totalBytesWritten

    def drain(self) -> bytes:
        combined = b"".join(self._chunks)
        self._chunks.clear()
        return combined


def _streamFolderAsZip(client: DriveClient, folderId: str) -> Iterator[bytes]:
    """Streams a folder tree as a zip with bounded memory regardless of how
    large any individual member file is: each file is pulled from Drive in
    chunksize-bounded reads (downloadFileInChunks) and written straight into
    the open zip entry (archive.open(..., "w")), which itself only buffers
    zipfile's own small internal write buffer — never a whole file, never
    the whole archive."""
    writer = _ChunkCollectingWriter()
    with zipfile.ZipFile(writer, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as archive:
        for archivePath, fileId, _mimeType in client.walkFolderRecursively(folderId):
            with archive.open(archivePath, mode="w") as zipEntry:
                for downloadChunk in client.downloadFileInChunks(fileId):
                    zipEntry.write(downloadChunk)
                    outgoing = writer.drain()
                    if outgoing:
                        yield outgoing
            outgoing = writer.drain()
            if outgoing:
                yield outgoing
    yield writer.drain()


@router.get("/{folderId}/download")
def downloadFolder(folderId: str, sharedDriveIdOrUrl: str = Query(...)) -> StreamingResponse:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        folderMetadata = client.getFolder(folderId)
    except Exception as error:
        raise HTTPException(status_code=404, detail=f"Folder {folderId} not found: {error}")

    folderName = folderMetadata.get("name", folderId)
    zipFileName = f"{folderName}.zip"
    return StreamingResponse(
        _streamFolderAsZip(client, folderId),
        media_type="application/zip",
        headers={"Content-Disposition": buildContentDisposition(zipFileName)},
    )


@router.patch("/{folderId}", response_model=FileResource)
def updateFolder(folderId: str, request: UpdateFolderRequest) -> FileResource:
    client = buildDriveClientForSharedDrive(request.sharedDriveIdOrUrl)
    try:
        updated = client.updateFolder(
            folderId=folderId,
            name=request.name,
            newParentFolderId=request.newParentFolderId,
            description=request.description,
            starred=request.starred,
        )
        return FileResource(**updated)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to update folder {folderId}: {error}")


@router.delete("/{folderId}", response_model=DeleteResult)
def deleteFolder(
    folderId: str, sharedDriveIdOrUrl: str = Query(...), permanent: bool = Query(default=False),
) -> DeleteResult:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        if permanent:
            client.permanentlyDeleteFile(folderId)
        else:
            client.deleteFolder(folderId)
        return DeleteResult(fileId=folderId, success=True)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to delete folder {folderId}: {error}")
