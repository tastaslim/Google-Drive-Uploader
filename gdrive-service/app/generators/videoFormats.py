"""Video generators. No encoder dependency (ffmpeg) is used, so these produce
minimal-but-structurally-valid container files (correct box/header signatures)
padded to the target size. They are sufficient for exercising upload, MIME
detection, and restore pipelines, but are not decodable as real video streams."""
import struct

from app.generators.models import FileFormatSpec


def _padded(header: bytes, index: int, targetSizeBytes: int) -> bytes:
    remaining = max(0, targetSizeBytes - len(header))
    filler = bytes(((index + i) % 256 for i in range(min(remaining, 65536))))
    payload = header + (filler * (remaining // max(len(filler), 1) + 1))[:remaining]
    return payload


def generateMp4(index: int, targetSizeBytes: int) -> bytes:
    ftyp = struct.pack(">I", 0x18) + b"ftypisom" + struct.pack(">I", 0x200) + b"isomiso2avc1mp41"
    return _padded(ftyp, index, targetSizeBytes)


def generateMov(index: int, targetSizeBytes: int) -> bytes:
    ftyp = struct.pack(">I", 0x14) + b"ftypqt  " + struct.pack(">I", 0x20000000) + b"qt  "
    return _padded(ftyp, index, targetSizeBytes)


def generateWebm(index: int, targetSizeBytes: int) -> bytes:
    ebmlHeader = bytes([0x1A, 0x45, 0xDF, 0xA3])
    return _padded(ebmlHeader, index, targetSizeBytes)


def generateAvi(index: int, targetSizeBytes: int) -> bytes:
    riffHeader = b"RIFF" + struct.pack("<I", targetSizeBytes) + b"AVI LIST"
    return _padded(riffHeader, index, targetSizeBytes)


def generateMkv(index: int, targetSizeBytes: int) -> bytes:
    return generateWebm(index, targetSizeBytes)


def buildVideoFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("mp4", "video/mp4", generateMp4, "video"),
        FileFormatSpec("mov", "video/quicktime", generateMov, "video"),
        FileFormatSpec("webm", "video/webm", generateWebm, "video"),
        FileFormatSpec("avi", "video/x-msvideo", generateAvi, "video"),
        FileFormatSpec("mkv", "video/x-matroska", generateMkv, "video"),
    ]
