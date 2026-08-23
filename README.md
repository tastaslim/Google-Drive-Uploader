# Google Shared Drive Service

FastAPI service for bulk-streaming synthetic test files (60+ formats) into a
Google Shared Drive, and performing CRUD operations on files and folders.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then fill in credentials
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

`.env` is loaded automatically at startup (via `python-dotenv`); real
environment variables still take precedence if both are set.

Interactive API docs are served at `http://localhost:8000/docs`.

## Authentication

Two auth modes, selected via `GDRIVE_AUTH_MODE`:

### `service_account` (default)

```bash
GDRIVE_AUTH_MODE=service_account
GDRIVE_SERVICE_ACCOUNT_FILE=/path/to/service_account.json
```

The service account must be added as a member of the target Shared Drive
with Content Manager (or higher) access.

### `oauth`

Uses a long-lived refresh token to mint short-lived access tokens on demand —
needed when the service should act as a real user identity rather than a
service account.

```bash
GDRIVE_AUTH_MODE=oauth
GDRIVE_OAUTH_CLIENT_ID=...
GDRIVE_OAUTH_CLIENT_SECRET=...
GDRIVE_OAUTH_REFRESH_TOKEN=...
GDRIVE_OAUTH_TOKEN_URI=https://oauth2.googleapis.com/token   # default, rarely needs changing
```

To obtain the client ID/secret and refresh token: create an OAuth 2.0 Client
ID (Desktop app or Web application type) in Google Cloud Console, then run
through the standard authorization-code consent flow once for scope
`https://www.googleapis.com/auth/drive` and capture the refresh token from
the token exchange response (e.g. via `google-auth-oauthlib`'s
`InstalledAppFlow`, or any OAuth playground pointed at your own client). The
refresh token doesn't expire unless revoked or unused for 6 months, so this
is a one-time setup per identity.

## Configuration (environment variables)

| Variable | Default | Description |
| --- | --- | --- |
| `GDRIVE_AUTH_MODE` | `service_account` | `service_account` or `oauth` |
| `GDRIVE_SERVICE_ACCOUNT_FILE` | `service_account.json` | Path to the service account key (service_account mode) |
| `GDRIVE_OAUTH_CLIENT_ID` | _(empty)_ | OAuth client ID (oauth mode) |
| `GDRIVE_OAUTH_CLIENT_SECRET` | _(empty)_ | OAuth client secret (oauth mode) |
| `GDRIVE_OAUTH_REFRESH_TOKEN` | _(empty)_ | OAuth refresh token used to mint access tokens (oauth mode) |
| `GDRIVE_OAUTH_TOKEN_URI` | `https://oauth2.googleapis.com/token` | Token endpoint used to redeem the refresh token |
| `GDRIVE_MAX_WORKERS` | `32` | Shared thread pool size for concurrent uploads |
| `GDRIVE_MIN_FILE_SIZE` | `1024` | Minimum generated file size (bytes) |
| `GDRIVE_MAX_FILE_SIZE` | `2097152` | Maximum generated file size (bytes) |
| `GDRIVE_MAX_RETRIES` | `8` | Retry attempts for retryable Drive API errors |
| `GDRIVE_DEFAULT_PAGE_SIZE` | `100` | Default page size for list endpoints |
| `GDRIVE_MAX_PAGE_SIZE` | `1000` | Max page size clients may request |
| `GDRIVE_CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated browser origins allowed to call this API (add the [gdrive-ui](../gdrive-ui) deployment URL) |

## Endpoints

### Uploads (background generate-and-upload jobs)
- `GET /uploads/formats` — list every generatable format extension (for exclusion checkboxes).
- `POST /uploads` — body: `{ "count": 50000, "sharedDriveIdOrUrl": "...", "folderId": null, "averageFileSizeBytes": 5242880, "excludedExtensions": ["pdf", "mp4"] }`.
  Returns a `jobId` immediately (202 Accepted); `folderId` defaults to the
  Shared Drive root when omitted, `averageFileSizeBytes` defaults to 5MB,
  `excludedExtensions` defaults to none.
- `GET /uploads/{jobId}` — job status: uploaded/failed/remaining counts, errors,
  the resolved `smallFileCount` / `largeFileCountsByBucket` split, and
  `recentEvents` — a live feed (last 50) of per-file generate/upload activity
  (`generated` → `uploading` → `uploaded`/`failed`, each with file name,
  extension, and size) for real-time progress display.
- `GET /uploads` — list all jobs known to this process (in-memory).
- `POST /uploads/{jobId}/cancel` — request cancellation of an in-flight job.

### Files
- `GET /files?sharedDriveIdOrUrl=...&folderId=...&pageSize=100&pageToken=...` — paginated listing.
- `POST /files/upload` — multipart form (`sharedDriveIdOrUrl`, `folderId`, `file`) — uploads
  a real file from the caller's machine as-is (the browser "File upload" action), streamed
  directly to Drive without buffering the whole file in memory.
- `POST /files/native` — body: `{ "sharedDriveIdOrUrl": "...", "appType": "document", "name": "...", "folderId": null }`.
  Creates one empty native Google Workspace file immediately (`appType` one of: `document`,
  `spreadsheet`, `presentation`, `vid`, `form`, `drawing`, `site`, `script`) — the right-click
  "Google Docs" etc. action.
- `GET /files/{fileId}?sharedDriveIdOrUrl=...` — get metadata for one file.
- `GET /files/{fileId}/download?sharedDriveIdOrUrl=...` — download raw content.
- `PATCH /files/{fileId}` — rename / move / update description / star.
- `DELETE /files/{fileId}?sharedDriveIdOrUrl=...&permanent=false` — trash or permanently delete one file.
- `POST /files/delete-batch` — body: `{ "sharedDriveIdOrUrl": "...", "fileIds": [...], "permanent": false }`.

### Folders
- `POST /folders` — create a folder (defaults to Shared Drive root as parent).
- `POST /folders/upload-batch` — multipart form (`sharedDriveIdOrUrl`, `parentFolderId`,
  repeated `relativePaths` + `files` pairs) — uploads a real local folder tree (the browser
  "Folder upload" action), recreating its subfolder structure in the Shared Drive. Subfolders
  are created once per path and reused across files that share an ancestor.
- `GET /folders?sharedDriveIdOrUrl=...&parentFolderId=...` — paginated listing of subfolders.
- `GET /folders/{folderId}?sharedDriveIdOrUrl=...` — get one folder.
- `GET /folders/{folderId}/download?sharedDriveIdOrUrl=...` — download the folder tree as a streamed zip (memory-bounded regardless of member file size; not a native Drive API feature, reconstructed server-side).
- `PATCH /folders/{folderId}` — rename / move / update description / star.
- `DELETE /folders/{folderId}?sharedDriveIdOrUrl=...&permanent=false` — trash or permanently delete.

### Trash
- `GET /trash?sharedDriveIdOrUrl=...` — paginated, drive-wide listing of trashed files and folders (matches Google Drive's own Trash view — not scoped to any particular folder).
- `POST /trash/{fileId}/restore?sharedDriveIdOrUrl=...` — restore an item to its original location.
- `DELETE /trash/{fileId}?sharedDriveIdOrUrl=...` — permanently delete a trashed item (irreversible).

## Format coverage

Text/code (`txt md rtf log ini cfg json csv tsv xml html yaml toml py go java
cpp c cs js ts php rb swift kt rs sh sql`), Office (`docx xlsx pptx msg odt ods
odp`), documents (`pdf epub`), images (`png jpg gif bmp tiff webp ico svg`),
audio (`wav mp3 flac ogg m4a aac`), video (`mp4 mov webm avi mkv`), email/
calendar (`eml mbox ics vcf`), archives (`zip tar tar.gz tar.bz2 gz bz2 xz`),
data (`sqlite db pickle npy parquet`), fonts/certs (`ttf otf woff woff2 pem
crt key pfx`), and Google-native files (`gdoc gsheet gslides gform gdraw
gscript`, created via the API with no binary upload).

Audio/video generators are pure Python (no `ffmpeg` dependency): WAV is real
PCM audio via the stdlib `wave` module; other audio/video formats use
structurally valid container headers padded to size — sufficient for
exercising upload/MIME-detection/restore pipelines, not for playback.

## File size distribution (small vs. large files)

`POST /uploads` accepts `averageFileSizeBytes`. Based on which band it falls
into, a **static** number of large files are mixed into the batch (each
randomized ±20% around its bucket's nominal size); every remaining file is a
small file (<10MB, one of the 86 generated formats above, sized 1KB-2MB in
memory as before):

| Requested average | Large files added |
| --- | --- |
| ≤1MB | none — all small |
| ≤10MB | one 50MB file |
| ≤50MB | three 50MB + one 100MB |
| ≤150MB | two 50MB + three 100MB + one 500MB |
| ≤500MB | two 100MB + three 500MB + one 1GB |
| ≤1GB | two 500MB + three 1GB + one 5GB |
| ≤5GB | two 1GB + three 5GB |
| >5GB | two 1GB + five 5GB (capped) |

If the batch's `count` is smaller than the band's large-file total, large
files are taken largest-bucket-first until `count` is filled (small file
count then drops to 0). This is a static lookup table, not a solve for the
exact numeric average — see `app/generators/sizeDistribution.py`.

**Large files (≥50MB) are never held fully in memory.** They're synthesized
by `app/generators/largeFileStream.py`'s `SyntheticByteStream` — a seekable
file-like object that computes any byte range on demand from a single
reused 1MB random block, so a 5GB file costs the same handful of MB of RAM
as a 50MB one. `MediaIoBaseUpload` reads it in chunks
(`GDRIVE_CHUNK_SIZE`, default 4MB) directly against the resumable upload,
so peak memory per large upload is bounded by the chunk size, not the file
size, even with 32 of them in flight concurrently.

## Logging

Every successful file create/upload (synthetic generator, real file upload,
real folder upload, native file creation) logs one structured `INFO` line
from `gdrive_service.driveClient`:

```
file_uploaded name='report.pdf' extension='pdf' mimeType='application/pdf' sizeBytes=204800 sharedDriveId=0AEYm... folderId=0AEYm... fileId=1Wot... elapsedSeconds=1.23
```

This is the single choke point for all upload paths, so grepping
`file_uploaded` shows exactly which file (name, extension, size), which
Shared Drive, which destination folder, and how long each upload took —
regardless of whether it came from the bulk generator, a real drag-and-drop
upload, or native Google file creation.

## Notes

- Job state is in-memory and process-local; it resets on restart and won't
  work correctly behind multiple uvicorn worker processes. For production
  durability, back it with a shared store (Redis/DB) instead.
- All Drive API calls set `supportsAllDrives=true` and target the given
  Shared Drive via `driveId` + `corpora=drive` for listing.
