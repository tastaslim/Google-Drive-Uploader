"""Raster and vector image generators."""
import io

from PIL import Image

from app.generators.models import FileFormatSpec


_MAX_IMAGE_SIDE_PIXELS = 2048

# Solid-color test images compress to nearly nothing under PNG/GIF/WebP (their
# encoders collapse a flat color to a handful of bytes regardless of pixel
# count), so pixel count is sized directly off targetSizeBytes assuming ~3
# source bytes/pixel for those. BMP/TIFF here are stored uncompressed, so
# their actual output is ~3 bytes/pixel and must be sized accordingly or the
# canvas balloons far past the target (previously up to 6x over).
_UNCOMPRESSED_FORMATS = {"BMP", "TIFF"}
_BYTES_PER_PIXEL_UNCOMPRESSED = 3


def _sizeForTarget(targetSizeBytes: int, fmt: str) -> tuple[int, int]:
    if fmt in _UNCOMPRESSED_FORMATS:
        approxPixels = max(64 * 64, min(targetSizeBytes // _BYTES_PER_PIXEL_UNCOMPRESSED, _MAX_IMAGE_SIDE_PIXELS ** 2))
    else:
        approxPixels = max(64 * 64, min(targetSizeBytes * 3, _MAX_IMAGE_SIDE_PIXELS ** 2))
    side = int(approxPixels ** 0.5)
    return side, side


def _makeImage(index: int, targetSizeBytes: int, fmt: str, mode: str = "RGB") -> bytes:
    width, height = _sizeForTarget(targetSizeBytes, fmt)
    color = (index % 255, (index * 3) % 255, (index * 7) % 255)
    image = Image.new(mode, (width, height), color)
    buffer = io.BytesIO()
    saveKwargs = {}
    if fmt == "JPEG":
        saveKwargs["quality"] = 90
    image.save(buffer, format=fmt, **saveKwargs)
    return buffer.getvalue()


def generatePng(index: int, targetSizeBytes: int) -> bytes:
    return _makeImage(index, targetSizeBytes, "PNG")


def generateJpeg(index: int, targetSizeBytes: int) -> bytes:
    return _makeImage(index, targetSizeBytes, "JPEG")


def generateGif(index: int, targetSizeBytes: int) -> bytes:
    return _makeImage(index, targetSizeBytes, "GIF", mode="P")


def generateBmp(index: int, targetSizeBytes: int) -> bytes:
    return _makeImage(index, targetSizeBytes, "BMP")


def generateTiff(index: int, targetSizeBytes: int) -> bytes:
    return _makeImage(index, targetSizeBytes, "TIFF")


def generateWebp(index: int, targetSizeBytes: int) -> bytes:
    return _makeImage(index, targetSizeBytes, "WEBP")


def generateIco(index: int, targetSizeBytes: int) -> bytes:
    image = Image.new("RGB", (64, 64), (index % 255, 100, 150))
    buffer = io.BytesIO()
    image.save(buffer, format="ICO")
    return buffer.getvalue()


def generateSvg(index: int, targetSizeBytes: int) -> bytes:
    circles = []
    circleIndex = 0
    currentSizeBytes = 0
    while currentSizeBytes < targetSizeBytes:
        circle = (
            f'<circle cx="{(circleIndex * 7) % 500}" cy="{(circleIndex * 13) % 500}" r="5" fill="#{(index + circleIndex) % 999:03d}" />'
        )
        circles.append(circle)
        currentSizeBytes += len(circle.encode("utf-8"))
        circleIndex += 1
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500"><title>Image {index}</title>' + "".join(circles) + "</svg>"
    return svg.encode("utf-8")


def buildImageFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("png", "image/png", generatePng, "image"),
        FileFormatSpec("jpg", "image/jpeg", generateJpeg, "image"),
        FileFormatSpec("gif", "image/gif", generateGif, "image"),
        FileFormatSpec("bmp", "image/bmp", generateBmp, "image"),
        FileFormatSpec("tiff", "image/tiff", generateTiff, "image"),
        FileFormatSpec("webp", "image/webp", generateWebp, "image"),
        FileFormatSpec("ico", "image/x-icon", generateIco, "image"),
        FileFormatSpec("svg", "image/svg+xml", generateSvg, "image"),
    ]
