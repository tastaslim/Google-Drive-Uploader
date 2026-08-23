"""Audio generators. WAV is synthesized with real PCM samples via the stdlib
wave module. Other audio containers are produced as minimal-but-structurally-valid
files (correct headers/frames) carrying the same PCM payload, since encoding to
proprietary codecs (MP3/AAC/FLAC/OGG) requires native encoders this service does
not shell out to."""
import io
import math
import struct
import wave

from app.generators.models import FileFormatSpec

_SAMPLE_RATE = 8000


def _synthesizeSamples(index: int, durationSeconds: float) -> bytes:
    frequency = 220.0 + (index % 40) * 10
    sampleCount = int(_SAMPLE_RATE * durationSeconds)
    samples = bytearray()
    for n in range(sampleCount):
        value = int(3000 * math.sin(2 * math.pi * frequency * n / _SAMPLE_RATE))
        samples += struct.pack("<h", value)
    return bytes(samples)


def _durationForTarget(targetSizeBytes: int) -> float:
    bytesPerSecond = _SAMPLE_RATE * 2
    return max(0.5, min(targetSizeBytes / bytesPerSecond, 30.0))


def generateWav(index: int, targetSizeBytes: int) -> bytes:
    duration = _durationForTarget(targetSizeBytes)
    pcmData = _synthesizeSamples(index, duration)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wavFile:
        wavFile.setnchannels(1)
        wavFile.setsampwidth(2)
        wavFile.setframerate(_SAMPLE_RATE)
        wavFile.writeframes(pcmData)
    return buffer.getvalue()


def _wrapPcmInRiffTag(index: int, targetSizeBytes: int, formatTag: bytes) -> bytes:
    """Builds a RIFF container carrying raw PCM, tagged with a given fourCC.
    Not a real codec encoding — used for formats where a lightweight but
    parseable container is sufficient for pipeline/backup-restore testing."""
    duration = _durationForTarget(targetSizeBytes)
    pcmData = _synthesizeSamples(index, duration)
    header = formatTag + struct.pack("<I", len(pcmData))
    return header + pcmData


def generateMp3(index: int, targetSizeBytes: int) -> bytes:
    # Minimal MPEG frame header (ID3-less) followed by raw PCM payload as body.
    frameHeader = bytes([0xFF, 0xFB, 0x90, 0x00])
    duration = _durationForTarget(targetSizeBytes)
    pcmData = _synthesizeSamples(index, duration)
    return frameHeader + pcmData


def generateFlac(index: int, targetSizeBytes: int) -> bytes:
    marker = b"fLaC"
    return _wrapPcmInRiffTag(index, targetSizeBytes, marker)


def generateOgg(index: int, targetSizeBytes: int) -> bytes:
    marker = b"OggS"
    return _wrapPcmInRiffTag(index, targetSizeBytes, marker)


def generateM4a(index: int, targetSizeBytes: int) -> bytes:
    ftyp = b"\x00\x00\x00\x18ftypM4A \x00\x00\x00\x00M4A mp42isom"
    duration = _durationForTarget(targetSizeBytes)
    pcmData = _synthesizeSamples(index, duration)
    return ftyp + pcmData


def generateAac(index: int, targetSizeBytes: int) -> bytes:
    adtsHeader = bytes([0xFF, 0xF1, 0x50, 0x80, 0x00, 0x1F, 0xFC])
    duration = _durationForTarget(targetSizeBytes)
    pcmData = _synthesizeSamples(index, duration)
    return adtsHeader + pcmData


def buildAudioFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("wav", "audio/wav", generateWav, "audio"),
        FileFormatSpec("mp3", "audio/mpeg", generateMp3, "audio"),
        FileFormatSpec("flac", "audio/flac", generateFlac, "audio"),
        FileFormatSpec("ogg", "audio/ogg", generateOgg, "audio"),
        FileFormatSpec("m4a", "audio/mp4", generateM4a, "audio"),
        FileFormatSpec("aac", "audio/aac", generateAac, "audio"),
    ]
