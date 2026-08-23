"""Shared types for the file-content generator registry."""
from dataclasses import dataclass
from typing import Callable

GeneratorFunction = Callable[[int, int], bytes]
"""A generator takes (index, targetSizeBytes) and returns file content bytes."""


@dataclass(frozen=True)
class FileFormatSpec:
    extension: str
    mimeType: str
    generator: GeneratorFunction
    category: str
    googleNativeMimeType: str | None = None
