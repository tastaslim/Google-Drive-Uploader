"""Database and data-science format generators using stdlib sqlite3 and pickle."""
import io
import pickle
import sqlite3
import tempfile
from pathlib import Path

from app.generators.models import FileFormatSpec


def generateSqlite(index: int, targetSizeBytes: int) -> bytes:
    with tempfile.TemporaryDirectory() as tempDir:
        dbPath = Path(tempDir) / f"file_{index}.sqlite"
        connection = sqlite3.connect(dbPath)
        try:
            connection.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, name TEXT, value INTEGER)")
            rowIndex = 0
            while dbPath.stat().st_size < targetSizeBytes and rowIndex < 50000:
                connection.execute(
                    "INSERT INTO records (name, value) VALUES (?, ?)",
                    (f"row-{rowIndex}", index + rowIndex),
                )
                if rowIndex % 500 == 0:
                    connection.commit()
                rowIndex += 1
            connection.commit()
        finally:
            connection.close()
        return dbPath.read_bytes()


def generateDb(index: int, targetSizeBytes: int) -> bytes:
    return generateSqlite(index, targetSizeBytes)


_PICKLE_MAX_RECORDS = 500000
_PICKLE_SIZE_CHECK_INTERVAL = 1000


def generatePickle(index: int, targetSizeBytes: int) -> bytes:
    """pickle.dumps() re-serializes the whole records list each call, so
    re-checking size after every single append is O(n^2). Batch appends
    between size checks instead."""
    records = []
    recordIndex = 0
    while recordIndex < _PICKLE_MAX_RECORDS:
        for _ in range(_PICKLE_SIZE_CHECK_INTERVAL):
            records.append({"id": index, "row": recordIndex, "value": recordIndex * index})
            recordIndex += 1
        serialized = pickle.dumps(records)
        if len(serialized) >= targetSizeBytes:
            return serialized
    return pickle.dumps(records)


def generateNpy(index: int, targetSizeBytes: int) -> bytes:
    try:
        import numpy
    except ImportError:
        return _fallbackBinaryPayload(b"NUMPY_UNAVAILABLE", index, targetSizeBytes)
    elementCount = max(1, targetSizeBytes // 8)
    array = numpy.arange(elementCount, dtype=numpy.float64) + index
    buffer = io.BytesIO()
    numpy.save(buffer, array)
    return buffer.getvalue()


def generateParquet(index: int, targetSizeBytes: int) -> bytes:
    try:
        import pyarrow as arrow
        import pyarrow.parquet as parquet
    except ImportError:
        return _fallbackBinaryPayload(b"PARQUET_UNAVAILABLE", index, targetSizeBytes)
    rowCount = max(1, targetSizeBytes // 16)
    table = arrow.table({"id": list(range(rowCount)), "value": [index] * rowCount})
    buffer = io.BytesIO()
    parquet.write_table(table, buffer)
    return buffer.getvalue()


def _fallbackBinaryPayload(marker: bytes, index: int, targetSizeBytes: int) -> bytes:
    filler = bytes(((index + i) % 256 for i in range(min(targetSizeBytes, 65536))))
    return marker + filler


def buildDataFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("sqlite", "application/vnd.sqlite3", generateSqlite, "data"),
        FileFormatSpec("db", "application/vnd.sqlite3", generateDb, "data"),
        FileFormatSpec("pickle", "application/octet-stream", generatePickle, "data"),
        FileFormatSpec("npy", "application/octet-stream", generateNpy, "data"),
        FileFormatSpec("parquet", "application/vnd.apache.parquet", generateParquet, "data"),
    ]
