"""Central pluggable registry combining all format-category generators."""
import random

from app.config import settings
from app.generators.archiveFormats import buildArchiveFormatSpecs
from app.generators.audioFormats import buildAudioFormatSpecs
from app.generators.dataFormats import buildDataFormatSpecs
from app.generators.documentFormats import buildDocumentFormatSpecs
from app.generators.emailFormats import buildEmailFormatSpecs
from app.generators.googleNativeFormats import buildGoogleNativeFormatSpecs
from app.generators.imageFormats import buildImageFormatSpecs
from app.generators.miscFormats import buildMiscFormatSpecs
from app.generators.models import FileFormatSpec
from app.generators.officeFormats import buildOfficeFormatSpecs
from app.generators.textFormats import buildTextFormatSpecs
from app.generators.videoFormats import buildVideoFormatSpecs


def buildFormatRegistry() -> list[FileFormatSpec]:
    return [
        *buildTextFormatSpecs(),
        *buildOfficeFormatSpecs(),
        *buildDocumentFormatSpecs(),
        *buildImageFormatSpecs(),
        *buildAudioFormatSpecs(),
        *buildVideoFormatSpecs(),
        *buildEmailFormatSpecs(),
        *buildArchiveFormatSpecs(),
        *buildDataFormatSpecs(),
        *buildMiscFormatSpecs(),
        *buildGoogleNativeFormatSpecs(),
    ]


FORMAT_REGISTRY: list[FileFormatSpec] = buildFormatRegistry()

FORMAT_REGISTRY_BY_EXTENSION: dict[str, FileFormatSpec] = {spec.extension: spec for spec in FORMAT_REGISTRY}

FORMAT_EXTENSIONS: list[str] = [spec.extension for spec in FORMAT_REGISTRY]


def buildActiveRegistry(excludedExtensions: list[str] | None) -> list[FileFormatSpec]:
    """The full registry minus any caller-excluded extensions, used to pick
    formats for a given generate-and-upload job. Falls back to the full
    registry if the exclusion list would remove every format (an empty
    active registry has nothing to generate from)."""
    if not excludedExtensions:
        return FORMAT_REGISTRY
    excludedSet = {ext.lower().lstrip(".") for ext in excludedExtensions}
    active = [spec for spec in FORMAT_REGISTRY if spec.extension.lower() not in excludedSet]
    return active or FORMAT_REGISTRY


def pickFormatSpecForIndex(index: int, registry: list[FileFormatSpec] = FORMAT_REGISTRY) -> FileFormatSpec:
    return registry[index % len(registry)]


def pickRandomFileSizeBytes(rng: random.Random) -> int:
    return rng.randint(settings.minFileSizeBytes, settings.maxFileSizeBytes)


def generateFileForIndex(
    index: int, rng: random.Random, targetSizeBytes: int | None = None,
    registry: list[FileFormatSpec] = FORMAT_REGISTRY,
) -> tuple[str, FileFormatSpec, bytes]:
    formatSpec = pickFormatSpecForIndex(index, registry)
    sizeBytes = targetSizeBytes if targetSizeBytes is not None else pickRandomFileSizeBytes(rng)
    content = formatSpec.generator(index, sizeBytes)
    fileName = f"file_{index}_{rng.randint(1000, 9999)}.{formatSpec.extension}"
    return fileName, formatSpec, content
