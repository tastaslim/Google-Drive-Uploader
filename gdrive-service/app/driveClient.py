"""Thread-safe Google Drive v3 client wrapper for Shared Drive operations."""
import io
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuthCredentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from app.config import DEFAULT_FILE_FIELDS, DEFAULT_LIST_FIELDS, GOOGLE_NATIVE_MIME_PREFIX, SCOPES, settings
from app.retry import callWithRetry, computeBackoffSeconds, isRetryableHttpError

logger = logging.getLogger("gdrive_service.driveClient")

_threadLocal = threading.local()

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

_DRIVE_URL_PATTERNS = [
    re.compile(r"/drive/folders/([a-zA-Z0-9_-]+)"),
    re.compile(r"/drive/u/\d+/folders/([a-zA-Z0-9_-]+)"),
    re.compile(r"[?&]id=([a-zA-Z0-9_-]+)"),
]


def extractIdFromUrlOrId(value: str) -> str:
    """Accepts a raw Drive/Shared-Drive ID or a Drive URL and returns the bare ID."""
    candidate = value.strip()
    if not candidate.startswith("http"):
        return candidate
    for pattern in _DRIVE_URL_PATTERNS:
        match = pattern.search(candidate)
        if match:
            return match.group(1)
    trimmed = candidate.rstrip("/").split("/")[-1]
    return trimmed.split("?")[0]


def _extractExtension(fileName: str) -> str:
    if "." not in fileName:
        return ""
    return fileName.rsplit(".", 1)[-1].lower()


def _logFileUpload(
    name: str, extension: str, mimeType: str, sizeBytes: int | None,
    sharedDriveId: str, folderId: str, fileId: str | None, elapsedSeconds: float,
) -> None:
    """Single structured log line per successfully uploaded/created file —
    covers every upload path (synthetic generator, real file/folder upload,
    native file creation) since they all funnel through createFile /
    createFileFromStream. Lets an operator grep logs for exactly which file,
    extension, size, drive, and folder a given upload landed in."""
    logger.info(
        "file_uploaded name=%r extension=%r mimeType=%r sizeBytes=%s "
        "sharedDriveId=%s folderId=%s fileId=%s elapsedSeconds=%.2f",
        name, extension, mimeType, sizeBytes if sizeBytes is not None else "unknown",
        sharedDriveId, folderId, fileId, elapsedSeconds,
    )


def _buildCredentials():
    """Builds Drive API credentials per GDRIVE_AUTH_MODE.

    - "service_account" (default): a service-account key file, scoped for Drive.
    - "oauth": a refresh token exchanged for short-lived access tokens on demand
      (google-auth transparently refreshes it via the token endpoint), used when
      acting as a real user identity rather than a service account.
    """
    if settings.authMode == "oauth":
        missing = [
            name for name, value in (
                ("GDRIVE_OAUTH_CLIENT_ID", settings.oauthClientId),
                ("GDRIVE_OAUTH_CLIENT_SECRET", settings.oauthClientSecret),
                ("GDRIVE_OAUTH_REFRESH_TOKEN", settings.oauthRefreshToken),
            ) if not value
        ]
        if missing:
            raise RuntimeError(
                f"GDRIVE_AUTH_MODE=oauth requires env vars: {', '.join(missing)}"
            )
        return OAuthCredentials(
            token=None,
            refresh_token=settings.oauthRefreshToken,
            token_uri=settings.oauthTokenUri,
            client_id=settings.oauthClientId,
            client_secret=settings.oauthClientSecret,
            scopes=SCOPES,
        )
    return service_account.Credentials.from_service_account_file(
        settings.serviceAccountFile, scopes=SCOPES,
    )


def getDriveService() -> Resource:
    """Returns a per-thread Drive service instance (googleapiclient Resource objects are not thread-safe)."""
    service = getattr(_threadLocal, "driveService", None)
    if service is not None:
        return service
    credentials = _buildCredentials()
    service = build("drive", "v3", credentials=credentials, cache_discovery=False)
    _threadLocal.driveService = service
    return service


def listSharedDrives(pageSize: int, pageToken: str | None) -> dict[str, Any]:
    """Lists Shared Drives visible to the authenticated identity. Not scoped to
    a particular drive, so this lives at module level rather than on DriveClient."""

    def _list():
        return getDriveService().drives().list(
            pageSize=pageSize,
            pageToken=pageToken,
            fields="nextPageToken,drives(id,name,createdTime,capabilities,restrictions)",
        ).execute()

    return callWithRetry(_list, "listSharedDrives")


class DriveClient:
    """High-level operations against a specific Shared Drive."""

    def __init__(self, sharedDriveId: str):
        self.sharedDriveId = sharedDriveId
        self._cachedDriveName: str | None = None

    def _service(self) -> Resource:
        return getDriveService()

    def resolveRootFolderId(self) -> str:
        return self.sharedDriveId

    def createFolder(self, name: str, parentFolderId: str | None, description: str | None = None) -> dict[str, Any]:
        parent = parentFolderId or self.resolveRootFolderId()
        body: dict[str, Any] = {
            "name": name,
            "mimeType": FOLDER_MIME_TYPE,
            "parents": [parent],
        }
        if description:
            body["description"] = description

        def _create():
            return self._service().files().create(
                body=body,
                supportsAllDrives=True,
                fields=DEFAULT_FILE_FIELDS,
            ).execute()

        return callWithRetry(_create, "createFolder")

    def getOrCreateFolderByName(self, name: str, parentFolderId: str | None) -> dict[str, Any]:
        """Idempotent folder creation used by real folder-upload: looks for an
        existing non-trashed subfolder with this exact name under the parent
        first, reusing it if found, so uploading the same local folder twice
        (or a folder-upload retry) doesn't create duplicate subfolders."""
        parent = parentFolderId or self.resolveRootFolderId()
        query = (
            f"'{parent}' in parents and mimeType='{FOLDER_MIME_TYPE}' and "
            f"trashed=false and name='{name.replace(chr(39), chr(92) + chr(39))}'"
        )
        existing = self._listFiles(query=query, pageSize=1, pageToken=None)
        matches = existing.get("files", [])
        if matches:
            return matches[0]
        return self.createFolder(name=name, parentFolderId=parent)

    def getFolder(self, folderId: str) -> dict[str, Any]:
        def _get():
            return self._service().files().get(
                fileId=folderId,
                supportsAllDrives=True,
                fields=DEFAULT_FILE_FIELDS,
            ).execute()

        result = callWithRetry(_get, "getFolder")
        if result.get("mimeType") != FOLDER_MIME_TYPE:
            raise ValueError(f"{folderId} is not a folder")
        return result

    def listFolders(
        self, parentFolderId: str | None, pageSize: int, pageToken: str | None,
    ) -> dict[str, Any]:
        parent = parentFolderId or self.resolveRootFolderId()
        query = f"'{parent}' in parents and mimeType='{FOLDER_MIME_TYPE}' and trashed=false"
        return self._listFiles(query=query, pageSize=pageSize, pageToken=pageToken)

    def searchFolders(
        self, nameContains: str, pageSize: int, pageToken: str | None,
    ) -> dict[str, Any]:
        """Drive-wide (not parent-scoped) folder search by name substring."""
        escaped = nameContains.replace("\\", "\\\\").replace("'", "\\'")
        query = f"mimeType='{FOLDER_MIME_TYPE}' and trashed=false and name contains '{escaped}'"
        return self._listFiles(query=query, pageSize=pageSize, pageToken=pageToken)

    def resolveFolderPath(
        self, folderId: str, name: str, parents: list[str] | None,
        _cache: dict[str, dict[str, Any]] | None = None,
    ) -> str:
        """Walks the parent chain up to the Shared Drive root to build a
        breadcrumb-style path for a folder, e.g. "Shared Drive / A / B".
        Accepts an optional cache dict (folderId -> metadata) so callers
        resolving many folders in one batch can reuse shared ancestors."""
        cache = _cache if _cache is not None else {}
        segments = [name]
        currentParents = parents
        visited = {folderId}
        for _ in range(25):  # bounded depth guard against unexpected cycles
            if not currentParents:
                break
            parentId = currentParents[0]
            if parentId == self.sharedDriveId or parentId in visited:
                break
            visited.add(parentId)
            if parentId in cache:
                parentFolder = cache[parentId]
            else:
                try:
                    parentFolder = self.getFolder(parentId)
                except Exception:
                    break
                cache[parentId] = parentFolder
            segments.append(parentFolder.get("name", "?"))
            currentParents = parentFolder.get("parents")
        segments.append(self._driveDisplayName())
        return " / ".join(reversed(segments))

    def _driveDisplayName(self) -> str:
        if self._cachedDriveName is not None:
            return self._cachedDriveName
        try:
            drive = self._service().drives().get(driveId=self.sharedDriveId, fields="name").execute()
            self._cachedDriveName = drive.get("name", "Shared Drive")
        except Exception:
            self._cachedDriveName = "Shared Drive"
        return self._cachedDriveName

    def updateFolder(
        self, folderId: str, name: str | None, newParentFolderId: str | None,
        description: str | None, starred: bool | None,
    ) -> dict[str, Any]:
        return self._updateFileMetadata(folderId, name, newParentFolderId, description, starred)

    def deleteFolder(self, folderId: str) -> None:
        self._trashFile(folderId)

    def createFile(
        self, name: str, parentFolderId: str | None, mimeType: str,
        content: bytes, googleNativeMimeType: str | None = None,
    ) -> dict[str, Any]:
        parent = parentFolderId or self.resolveRootFolderId()
        body: dict[str, Any] = {"name": name, "parents": [parent]}

        if googleNativeMimeType:
            # Native Google Workspace files (Docs/Sheets/Slides/etc) have no
            # binary content — Drive creates them purely from the mimeType.
            # Attaching a media_body (even empty bytes) makes the API reject
            # the request with a 400, so this must be a metadata-only create.
            body["mimeType"] = googleNativeMimeType

            def _createNative():
                return self._service().files().create(
                    body=body,
                    supportsAllDrives=True,
                    fields=DEFAULT_FILE_FIELDS,
                ).execute()

            startTime = time.monotonic()
            result = callWithRetry(_createNative, "createNativeFile")
            _logFileUpload(
                name=name, extension=_extractExtension(name), mimeType=googleNativeMimeType,
                sizeBytes=0, sharedDriveId=self.sharedDriveId, folderId=parent,
                fileId=result.get("id"), elapsedSeconds=time.monotonic() - startTime,
            )
            return result

        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype=mimeType,
            resumable=True,
            chunksize=settings.resumableChunkSizeBytes,
        )

        def _create():
            request = self._service().files().create(
                body=body,
                media_body=media,
                supportsAllDrives=True,
                fields=DEFAULT_FILE_FIELDS,
            )
            return self._executeResumable(request)

        startTime = time.monotonic()
        result = callWithRetry(_create, "createFile")
        _logFileUpload(
            name=name, extension=_extractExtension(name), mimeType=mimeType,
            sizeBytes=len(content), sharedDriveId=self.sharedDriveId, folderId=parent,
            fileId=result.get("id"), elapsedSeconds=time.monotonic() - startTime,
        )
        return result

    def createFileFromStream(
        self, name: str, parentFolderId: str | None, mimeType: str, stream, resumableChunkSizeBytes: int,
    ) -> dict[str, Any]:
        """Same as createFile, but takes a seekable file-like object directly
        instead of in-memory bytes — used for large synthetic files so the
        full content is never held in memory (see generators/largeFileStream.py).

        Uses a single resumable-upload session for the whole file: if a chunk
        fails on a retryable error (e.g. throttling), only that chunk is
        retried against the same upload URI, resuming from Drive's reported
        byte offset — not restarting the whole (possibly multi-GB) upload
        from byte 0."""
        parent = parentFolderId or self.resolveRootFolderId()
        body: dict[str, Any] = {"name": name, "parents": [parent]}

        media = MediaIoBaseUpload(
            stream,
            mimetype=mimeType,
            resumable=True,
            chunksize=resumableChunkSizeBytes,
        )

        stream.seek(0)
        request = self._service().files().create(
            body=body,
            media_body=media,
            supportsAllDrives=True,
            fields=DEFAULT_FILE_FIELDS,
        )

        startTime = time.monotonic()
        result = self._executeResumable(request, "createFileFromStream")
        streamSizeBytes = stream.seek(0, 2) if hasattr(stream, "seek") else None
        _logFileUpload(
            name=name, extension=_extractExtension(name), mimeType=mimeType,
            sizeBytes=streamSizeBytes, sharedDriveId=self.sharedDriveId, folderId=parent,
            fileId=result.get("id"), elapsedSeconds=time.monotonic() - startTime,
        )
        return result

    def _executeResumable(self, request, operationName: str = "resumable_upload") -> dict[str, Any]:
        response = None
        attempt = 0
        while response is None:
            try:
                _, response = request.next_chunk()
                attempt = 0  # reset backoff counter after a successful chunk
            except HttpError as httpError:
                if not isRetryableHttpError(httpError) or attempt >= settings.maxRetries - 1:
                    raise
                sleepSeconds = computeBackoffSeconds(attempt)
                logger.warning(
                    "Retryable error on chunk for %s (attempt %d/%d): %s. Resuming from last byte offset in %.2fs",
                    operationName, attempt + 1, settings.maxRetries, httpError, sleepSeconds,
                )
                time.sleep(sleepSeconds)
                attempt += 1
            except (ConnectionError, TimeoutError) as transientError:
                if attempt >= settings.maxRetries - 1:
                    raise
                sleepSeconds = computeBackoffSeconds(attempt)
                logger.warning(
                    "Transient error on chunk for %s (attempt %d/%d): %s. Resuming from last byte offset in %.2fs",
                    operationName, attempt + 1, settings.maxRetries, transientError, sleepSeconds,
                )
                time.sleep(sleepSeconds)
                attempt += 1
        return response

    def getFile(self, fileId: str) -> dict[str, Any]:
        def _get():
            return self._service().files().get(
                fileId=fileId,
                supportsAllDrives=True,
                fields=DEFAULT_FILE_FIELDS,
            ).execute()

        return callWithRetry(_get, "getFile")

    def downloadFile(self, fileId: str) -> bytes:
        def _download():
            return self._service().files().get_media(
                fileId=fileId, supportsAllDrives=True,
            ).execute()

        return callWithRetry(_download, "downloadFile")

    def downloadFileInChunks(self, fileId: str, chunkSizeBytes: int = 4 * 1024 * 1024):
        """Streams a file's bytes in bounded chunks instead of loading the
        whole file into memory at once (what downloadFile()/get_media().execute()
        does) — required for folder-zip downloads where any single member file
        could be GB-scale."""
        request = self._service().files().get_media(fileId=fileId, supportsAllDrives=True)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request, chunksize=chunkSizeBytes)

        done = False
        lastPosition = 0
        while not done:
            def _nextChunk():
                return downloader.next_chunk()

            _, done = callWithRetry(_nextChunk, "downloadFileChunk")
            buffer.seek(lastPosition)
            chunk = buffer.read()
            lastPosition = buffer.tell()
            if chunk:
                yield chunk

    def walkFolderRecursively(self, folderId: str, pathPrefix: str = ""):
        """Yields (archivePath, fileId, mimeType) for every non-folder file
        nested under folderId, at any depth, depth-first. archivePath mirrors
        the folder structure so a zip built from these entries matches what
        Google Drive's own "Download as zip" produces."""
        pageToken: str | None = None
        while True:
            page = self.listFiles(parentFolderId=folderId, pageSize=1000, pageToken=pageToken, includeFolders=True)
            for entry in page.get("files", []):
                entryPath = f"{pathPrefix}{entry['name']}"
                if entry.get("mimeType") == FOLDER_MIME_TYPE:
                    yield from self.walkFolderRecursively(entry["id"], pathPrefix=f"{entryPath}/")
                elif not entry.get("mimeType", "").startswith(GOOGLE_NATIVE_MIME_PREFIX):
                    # Google-native files (Docs/Sheets/Slides) have no raw binary
                    # content to download via get_media; real Drive exports them
                    # to a format like docx/xlsx on zip download, which is out of
                    # scope here, so they're skipped rather than silently 500ing.
                    yield entryPath, entry["id"], entry.get("mimeType", "application/octet-stream")
            pageToken = page.get("nextPageToken")
            if not pageToken:
                break

    def listFiles(
        self, parentFolderId: str | None, pageSize: int, pageToken: str | None,
        includeFolders: bool = False,
    ) -> dict[str, Any]:
        parent = parentFolderId or self.resolveRootFolderId()
        query = f"'{parent}' in parents and trashed=false"
        if not includeFolders:
            query += f" and mimeType != '{FOLDER_MIME_TYPE}'"
        return self._listFiles(query=query, pageSize=pageSize, pageToken=pageToken)

    def computeFolderStats(self, folderId: str, _depth: int = 0) -> dict[str, int]:
        """Recursively walks a folder's contents to aggregate direct+nested
        file count, direct+nested subfolder count, and total size in bytes —
        Drive doesn't track this natively (a folder's own `size` field is
        always null), so it has to be computed by listing every descendant.
        Sibling subfolders are recursed into concurrently to keep this fast
        for wide trees; depth is bounded as a guard against pathological
        cycles (Drive folder structures are a DAG in theory, not expected in
        practice, but this keeps a bug elsewhere from causing infinite work)."""
        fileCount = 0
        folderCount = 0
        totalSizeBytes = 0
        subfolderIds: list[str] = []

        pageToken: str | None = None
        while True:
            page = self.listFiles(parentFolderId=folderId, pageSize=1000, pageToken=pageToken, includeFolders=True)
            for entry in page.get("files", []):
                if entry.get("mimeType") == FOLDER_MIME_TYPE:
                    folderCount += 1
                    subfolderIds.append(entry["id"])
                else:
                    fileCount += 1
                    sizeStr = entry.get("size")
                    if sizeStr:
                        totalSizeBytes += int(sizeStr)
            pageToken = page.get("nextPageToken")
            if not pageToken:
                break

        if subfolderIds and _depth < 50:
            with ThreadPoolExecutor(
                max_workers=min(len(subfolderIds), 10), thread_name_prefix="gdrive-folder-stats",
            ) as pool:
                childStats = list(pool.map(lambda childId: self.computeFolderStats(childId, _depth + 1), subfolderIds))
            for stats in childStats:
                fileCount += stats["fileCount"]
                folderCount += stats["folderCount"]
                totalSizeBytes += stats["totalSizeBytes"]

        return {"fileCount": fileCount, "folderCount": folderCount, "totalSizeBytes": totalSizeBytes}

    def listTrashedItems(self, pageSize: int, pageToken: str | None) -> dict[str, Any]:
        """Drive-wide trash listing for this Shared Drive — matches real Drive's
        Trash view, which is not scoped to any particular folder, since a
        trashed item's original parent folder is no longer where it "lives"."""
        query = "trashed=true"
        return self._listFiles(query=query, pageSize=pageSize, pageToken=pageToken)

    def _listFiles(self, query: str, pageSize: int, pageToken: str | None) -> dict[str, Any]:
        def _list():
            return self._service().files().list(
                q=query,
                corpora="drive",
                driveId=self.sharedDriveId,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                pageSize=pageSize,
                pageToken=pageToken,
                fields=DEFAULT_LIST_FIELDS,
                orderBy="name",
            ).execute()

        return callWithRetry(_list, "listFiles")

    def updateFile(
        self, fileId: str, name: str | None, newParentFolderId: str | None,
        description: str | None, starred: bool | None, content: bytes | None,
        mimeType: str | None,
    ) -> dict[str, Any]:
        return self._updateFileMetadata(
            fileId, name, newParentFolderId, description, starred, content, mimeType,
        )

    def _updateFileMetadata(
        self, fileId: str, name: str | None, newParentFolderId: str | None,
        description: str | None, starred: bool | None,
        content: bytes | None = None, mimeType: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if starred is not None:
            body["starred"] = starred

        addParents = None
        removeParents = None
        if newParentFolderId is not None:
            currentFile = self.getFile(fileId)
            existingParents = currentFile.get("parents", [])
            addParents = newParentFolderId
            removeParents = ",".join(existingParents) if existingParents else None

        media = None
        if content is not None:
            media = MediaIoBaseUpload(
                io.BytesIO(content),
                mimetype=mimeType or "application/octet-stream",
                resumable=True,
                chunksize=settings.resumableChunkSizeBytes,
            )

        def _update():
            request = self._service().files().update(
                fileId=fileId,
                body=body,
                addParents=addParents,
                removeParents=removeParents,
                media_body=media,
                supportsAllDrives=True,
                fields=DEFAULT_FILE_FIELDS,
            )
            if media is not None:
                return self._executeResumable(request)
            return request.execute()

        return callWithRetry(_update, "updateFile")

    def deleteFile(self, fileId: str) -> None:
        self._trashFile(fileId)

    def _trashFile(self, fileId: str) -> None:
        def _trash():
            self._service().files().update(
                fileId=fileId,
                body={"trashed": True},
                supportsAllDrives=True,
                fields="id",
            ).execute()

        callWithRetry(_trash, "trashFile")

    def permanentlyDeleteFile(self, fileId: str) -> None:
        def _delete():
            self._service().files().delete(
                fileId=fileId, supportsAllDrives=True,
            ).execute()

        callWithRetry(_delete, "permanentlyDeleteFile")

    def restoreFile(self, fileId: str) -> dict[str, Any]:
        def _restore():
            return self._service().files().update(
                fileId=fileId,
                body={"trashed": False},
                supportsAllDrives=True,
                fields=DEFAULT_FILE_FIELDS,
            ).execute()

        return callWithRetry(_restore, "restoreFile")
