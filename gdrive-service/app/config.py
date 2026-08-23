"""Runtime configuration for the Shared Drive FastAPI service."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    authMode: str = os.environ.get("GDRIVE_AUTH_MODE", "service_account")
    serviceAccountFile: str = os.environ.get("GDRIVE_SERVICE_ACCOUNT_FILE", "service_account.json")
    oauthClientId: str = os.environ.get("GDRIVE_OAUTH_CLIENT_ID", "")
    oauthClientSecret: str = os.environ.get("GDRIVE_OAUTH_CLIENT_SECRET", "")
    oauthRefreshToken: str = os.environ.get("GDRIVE_OAUTH_REFRESH_TOKEN", "")
    oauthTokenUri: str = os.environ.get("GDRIVE_OAUTH_TOKEN_URI", "https://oauth2.googleapis.com/token")
    maxWorkers: int = int(os.environ.get("GDRIVE_MAX_WORKERS", "32"))
    minFileSizeBytes: int = int(os.environ.get("GDRIVE_MIN_FILE_SIZE", str(1 * 1024)))
    maxFileSizeBytes: int = int(os.environ.get("GDRIVE_MAX_FILE_SIZE", str(2 * 1024 * 1024)))
    resumableChunkSizeBytes: int = int(os.environ.get("GDRIVE_CHUNK_SIZE", str(4 * 1024 * 1024)))
    maxRetries: int = int(os.environ.get("GDRIVE_MAX_RETRIES", "8"))
    baseBackoffSeconds: float = float(os.environ.get("GDRIVE_BASE_BACKOFF", "1.0"))
    maxBackoffSeconds: float = float(os.environ.get("GDRIVE_MAX_BACKOFF", "60.0"))
    defaultPageSize: int = int(os.environ.get("GDRIVE_DEFAULT_PAGE_SIZE", "100"))
    maxPageSize: int = int(os.environ.get("GDRIVE_MAX_PAGE_SIZE", "1000"))
    jobRetentionSeconds: int = int(os.environ.get("GDRIVE_JOB_RETENTION_SECONDS", str(24 * 60 * 60)))
    corsAllowedOrigins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.environ.get("GDRIVE_CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    )


settings = Settings()

SCOPES = ["https://www.googleapis.com/auth/drive"]

GOOGLE_NATIVE_MIME_PREFIX = "application/vnd.google-apps."

RETRYABLE_HTTP_STATUS_CODES = {403, 429, 500, 502, 503, 504}

RETRYABLE_REASON_CODES = {
    "rateLimitExceeded",
    "userRateLimitExceeded",
    "backendError",
    "internalError",
    "quotaExceeded",
    "sharingRateLimitExceeded",
}

DEFAULT_FILE_FIELDS = (
    "id,name,mimeType,parents,driveId,size,createdTime,modifiedTime,"
    "trashed,md5Checksum,webViewLink,starred,description,capabilities"
)

DEFAULT_LIST_FIELDS = f"nextPageToken,files({DEFAULT_FILE_FIELDS})"
