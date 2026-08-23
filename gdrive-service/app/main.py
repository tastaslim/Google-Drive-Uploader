"""FastAPI application entry point for the Google Shared Drive service."""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import drives, files, folders, trash, uploads

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Google Shared Drive Service",
    description=(
        "REST API for bulk-streaming synthetic files of 60+ formats into a "
        "Google Shared Drive, plus CRUD operations for files and folders."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.corsAllowedOrigins),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drives.router)
app.include_router(uploads.router)
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(trash.router)


@app.get("/health", tags=["health"])
def healthCheck() -> dict:
    return {"status": "ok"}
