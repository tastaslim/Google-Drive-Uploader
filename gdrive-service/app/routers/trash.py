"""Drive-wide Trash: list trashed files/folders, restore, and permanently delete."""
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.dependencies import buildDriveClientForSharedDrive
from app.driveClient import extractIdFromUrlOrId
from app.schemas import DeleteResult, FileResource, PaginatedFilesResponse

router = APIRouter(prefix="/trash", tags=["trash"])


@router.get("", response_model=PaginatedFilesResponse)
def listTrash(
    sharedDriveIdOrUrl: str = Query(...),
    pageSize: int = Query(default=settings.defaultPageSize, ge=1, le=settings.maxPageSize),
    pageToken: str | None = Query(default=None),
) -> PaginatedFilesResponse:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    result = client.listTrashedItems(pageSize=pageSize, pageToken=pageToken)
    return PaginatedFilesResponse(
        files=[FileResource(**f) for f in result.get("files", [])],
        nextPageToken=result.get("nextPageToken"),
    )


@router.post("/{fileId}/restore", response_model=FileResource)
def restoreItem(fileId: str, sharedDriveIdOrUrl: str = Query(...)) -> FileResource:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        restored = client.restoreFile(fileId)
        return FileResource(**restored)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to restore {fileId}: {error}")


@router.delete("/{fileId}", response_model=DeleteResult)
def permanentlyDeleteItem(fileId: str, sharedDriveIdOrUrl: str = Query(...)) -> DeleteResult:
    client = buildDriveClientForSharedDrive(extractIdFromUrlOrId(sharedDriveIdOrUrl))
    try:
        client.permanentlyDeleteFile(fileId)
        return DeleteResult(fileId=fileId, success=True)
    except Exception as error:
        raise HTTPException(status_code=400, detail=f"Failed to permanently delete {fileId}: {error}")
