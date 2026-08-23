"""Shared FastAPI dependencies."""
from app.driveClient import DriveClient


def buildDriveClientForSharedDrive(sharedDriveId: str) -> DriveClient:
    return DriveClient(sharedDriveId)
