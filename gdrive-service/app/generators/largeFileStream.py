"""Seekable, read-on-demand byte stream for large (50MB-5GB) synthetic files.

MediaIoBaseUpload requires a fully seekable file-like object (it calls
seek(0, SEEK_END) up front to determine size, then seek(begin)+read(length)
per chunk/retry) — so this cannot be a forward-only generator. Content is
never materialized in memory beyond a single reusable random block: any
byte at absolute offset `n` is deterministically `block[n % blockSize]`,
so seeking is just arithmetic and peak memory stays at O(blockSize)
regardless of whether the file is 50MB or 5GB.
"""
import io
import random


class SyntheticByteStream(io.RawIOBase):
    def __init__(self, totalSizeBytes: int, seed: int, blockSizeBytes: int = 1024 * 1024):
        self._totalSizeBytes = totalSizeBytes
        self._position = 0
        rng = random.Random(seed)
        self._blockSizeBytes = blockSizeBytes
        self._block = bytes(rng.getrandbits(8) for _ in range(blockSizeBytes))

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            newPosition = offset
        elif whence == io.SEEK_CUR:
            newPosition = self._position + offset
        elif whence == io.SEEK_END:
            newPosition = self._totalSizeBytes + offset
        else:
            raise ValueError(f"Unsupported whence: {whence}")
        self._position = max(0, newPosition)
        return self._position

    def tell(self) -> int:
        return self._position

    def readinto(self, buffer) -> int:
        remaining = self._totalSizeBytes - self._position
        if remaining <= 0:
            return 0
        chunkSize = min(len(buffer), remaining)
        blockOffset = self._position % self._blockSizeBytes
        written = 0
        while written < chunkSize:
            available = min(self._blockSizeBytes - blockOffset, chunkSize - written)
            buffer[written:written + available] = self._block[blockOffset:blockOffset + available]
            written += available
            blockOffset = 0
        self._position += written
        return written


LARGE_FILE_MIME_TYPE = "application/octet-stream"
LARGE_FILE_EXTENSION = "bin"
