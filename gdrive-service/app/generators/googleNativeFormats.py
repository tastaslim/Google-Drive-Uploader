"""Google Workspace native file specs. These have no binary payload to stream —
Drive creates the native file directly from a mimeType on files().create, so
their generator returns empty bytes and driveClient.createFile passes
googleNativeMimeType through instead of uploading media."""
from app.generators.models import FileFormatSpec


def generateEmptyPayload(index: int, targetSizeBytes: int) -> bytes:
    return b""


def buildGoogleNativeFormatSpecs() -> list[FileFormatSpec]:
    nativeMimeTypes = {
        "gdoc": "application/vnd.google-apps.document",
        "gsheet": "application/vnd.google-apps.spreadsheet",
        "gslides": "application/vnd.google-apps.presentation",
        "gvid": "application/vnd.google-apps.vid",
        "gform": "application/vnd.google-apps.form",
        "gdraw": "application/vnd.google-apps.drawing",
        "gsite": "application/vnd.google-apps.site",
        "gscript": "application/vnd.google-apps.script",
    }
    return [
        FileFormatSpec(
            extension=extension,
            mimeType=nativeMimeType,
            generator=generateEmptyPayload,
            category="google_native",
            googleNativeMimeType=nativeMimeType,
        )
        for extension, nativeMimeType in nativeMimeTypes.items()
    ]
