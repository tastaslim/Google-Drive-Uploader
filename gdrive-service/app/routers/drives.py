"""Shared Drive discovery: list all Shared Drives visible to the authenticated identity."""
from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.driveClient import listSharedDrives
from app.schemas import PaginatedSharedDrivesResponse, SharedDriveResource

router = APIRouter(prefix="/drives", tags=["drives"])

# The Drive API's drives.list endpoint caps pageSize at 100 regardless of
# this service's general maxPageSize (used by files/folders list endpoints,
# which support up to 1000) — see
# https://developers.google.com/drive/api/reference/rest/v3/drives/list
DRIVES_LIST_MAX_PAGE_SIZE = 100


@router.get("", response_model=PaginatedSharedDrivesResponse)
def listDrives(
    pageSize: int = Query(default=settings.defaultPageSize, ge=1, le=settings.maxPageSize),
    pageToken: str | None = Query(default=None),
) -> PaginatedSharedDrivesResponse:
    try:
        result = listSharedDrives(
            pageSize=min(pageSize, DRIVES_LIST_MAX_PAGE_SIZE), pageToken=pageToken,
        )
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Failed to list Shared Drives: {error}")
    return PaginatedSharedDrivesResponse(
        drives=[SharedDriveResource(**d) for d in result.get("drives", [])],
        nextPageToken=result.get("nextPageToken"),
    )
