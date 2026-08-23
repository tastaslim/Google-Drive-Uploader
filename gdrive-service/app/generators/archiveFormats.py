"""Archive container generators using the stdlib zipfile/tarfile modules."""
import bz2
import gzip
import io
import lzma
import tarfile
import zipfile

from app.generators.models import FileFormatSpec


def _sampleFilesContent(index: int, targetSizeBytes: int) -> list[tuple[str, bytes]]:
    fileCount = max(1, min(targetSizeBytes // 2048, 20))
    chunkSize = max(1, targetSizeBytes // fileCount)
    return [(f"sample_{index}_{i}.txt", (f"archive member {i} for file {index}\n" * (chunkSize // 32 + 1)).encode("utf-8")) for i in range(fileCount)]


def generateZip(index: int, targetSizeBytes: int) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in _sampleFilesContent(index, targetSizeBytes):
            archive.writestr(name, content)
    return buffer.getvalue()


def _generateTar(index: int, targetSizeBytes: int, mode: str) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode=mode) as archive:
        for name, content in _sampleFilesContent(index, targetSizeBytes):
            data = io.BytesIO(content)
            tarInfo = tarfile.TarInfo(name=name)
            tarInfo.size = len(content)
            archive.addfile(tarInfo, data)
    return buffer.getvalue()


def generateTar(index: int, targetSizeBytes: int) -> bytes:
    return _generateTar(index, targetSizeBytes, "w")


def generateTarGz(index: int, targetSizeBytes: int) -> bytes:
    return _generateTar(index, targetSizeBytes, "w:gz")


def generateTarBz2(index: int, targetSizeBytes: int) -> bytes:
    return _generateTar(index, targetSizeBytes, "w:bz2")


def generateGz(index: int, targetSizeBytes: int) -> bytes:
    content = (f"gzip content for file {index}\n" * (targetSizeBytes // 32 + 1)).encode("utf-8")
    return gzip.compress(content)


def generateBz2(index: int, targetSizeBytes: int) -> bytes:
    content = (f"bzip2 content for file {index}\n" * (targetSizeBytes // 32 + 1)).encode("utf-8")
    return bz2.compress(content)


def generateXz(index: int, targetSizeBytes: int) -> bytes:
    content = (f"xz content for file {index}\n" * (targetSizeBytes // 32 + 1)).encode("utf-8")
    return lzma.compress(content)


def buildArchiveFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("zip", "application/zip", generateZip, "archive"),
        FileFormatSpec("tar", "application/x-tar", generateTar, "archive"),
        FileFormatSpec("tar.gz", "application/gzip", generateTarGz, "archive"),
        FileFormatSpec("tar.bz2", "application/x-bzip2", generateTarBz2, "archive"),
        FileFormatSpec("gz", "application/gzip", generateGz, "archive"),
        FileFormatSpec("bz2", "application/x-bzip2", generateBz2, "archive"),
        FileFormatSpec("xz", "application/x-xz", generateXz, "archive"),
    ]
