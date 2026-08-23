"""Microsoft Office and OpenDocument generators using real authoring libraries."""
import io
import random

from docx import Document
from openpyxl import Workbook
from pptx import Presentation
from pptx.util import Inches

from app.generators.models import FileFormatSpec


_DOCX_MAX_PARAGRAPHS = 20000
_DOCX_TARGET_PARAGRAPH_TEXT_BYTES = 20000
_BASE32_ALPHABET = "abcdefghijklmnopqrstuvwxyz234567"


def _paddingParagraphText(index: int, paragraphIndex: int, approxBytes: int) -> str:
    # High-entropy content via a seeded PRNG — a docx is a DEFLATE-compressed
    # zip, and low-entropy text (repeating character patterns) can compress
    # 50-100x, making byte-per-paragraph estimates wildly wrong. Random
    # base32-alphabet text compresses close to 1:1, keeping size predictable.
    # Each add_paragraph() call also has real per-call overhead that grows
    # with document size (lxml tree operations), so we favor a small, bounded
    # NUMBER of paragraphs with large text bodies over many small ones.
    rng = random.Random(f"{index}-{paragraphIndex}")
    body = "".join(rng.choices(_BASE32_ALPHABET, k=approxBytes))
    return f"p{paragraphIndex}: {body}"


def generateDocx(index: int, targetSizeBytes: int) -> bytes:
    """Saving re-serializes the whole zip/XML tree and add_paragraph() itself
    gets slower as the document grows, so total cost scales with paragraph
    COUNT more than paragraph size. Grow via a bounded number of large
    paragraphs (measuring bytes-per-paragraph after a small warm-up and
    extrapolating) rather than many small ones."""
    document = Document()
    document.add_heading(f"Document {index}", level=1)
    document.add_paragraph(f"Generated content for file {index}.")

    paragraphCount = 0
    warmupBatch = 5
    for _ in range(warmupBatch):
        document.add_paragraph(_paddingParagraphText(index, paragraphCount, _DOCX_TARGET_PARAGRAPH_TEXT_BYTES))
        paragraphCount += 1

    buffer = io.BytesIO()
    document.save(buffer)
    warmupSizeBytes = len(buffer.getvalue())
    if warmupSizeBytes >= targetSizeBytes:
        return buffer.getvalue()

    bytesPerParagraph = max(1, warmupSizeBytes // paragraphCount)
    estimatedRemaining = min(
        (targetSizeBytes - warmupSizeBytes) // bytesPerParagraph + 1,
        _DOCX_MAX_PARAGRAPHS - paragraphCount,
    )
    for _ in range(max(0, estimatedRemaining)):
        document.add_paragraph(_paddingParagraphText(index, paragraphCount, _DOCX_TARGET_PARAGRAPH_TEXT_BYTES))
        paragraphCount += 1

    buffer = io.BytesIO()
    document.save(buffer)
    if len(buffer.getvalue()) >= targetSizeBytes or paragraphCount >= _DOCX_MAX_PARAGRAPHS:
        return buffer.getvalue()

    # Estimate was short (compression ratio isn't exactly 1:1) — top up once more.
    bytesPerParagraph = max(1, len(buffer.getvalue()) // paragraphCount)
    shortfall = min(
        (targetSizeBytes - len(buffer.getvalue())) // bytesPerParagraph + 1,
        _DOCX_MAX_PARAGRAPHS - paragraphCount,
    )
    for _ in range(max(0, shortfall)):
        document.add_paragraph(_paddingParagraphText(index, paragraphCount, _DOCX_TARGET_PARAGRAPH_TEXT_BYTES))
        paragraphCount += 1

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


_XLSX_MAX_ROWS = 300000
_XLSX_WARMUP_ROWS = 500


def generateXlsx(index: int, targetSizeBytes: int) -> bytes:
    """workbook.save() re-serializes the whole sheet from scratch, so its cost
    grows with row count — re-checking size every N rows is still O(n^2)
    overall once N is small relative to the total needed. Instead, save once
    after a small warm-up batch to measure bytes-per-row, extrapolate the
    row count needed to hit the target, add the remaining rows in one shot,
    and save once more."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(["id", "name", "value"])

    row = 0
    for _ in range(_XLSX_WARMUP_ROWS):
        sheet.append([index, f"row-{row}", row * index])
        row += 1

    buffer = io.BytesIO()
    workbook.save(buffer)
    warmupSizeBytes = len(buffer.getvalue())
    if warmupSizeBytes >= targetSizeBytes:
        return buffer.getvalue()

    bytesPerRow = max(1, warmupSizeBytes // row)
    estimatedRemainingRows = min((targetSizeBytes - warmupSizeBytes) // bytesPerRow + 1, _XLSX_MAX_ROWS - row)

    for _ in range(max(0, estimatedRemainingRows)):
        sheet.append([index, f"row-{row}", row * index])
        row += 1

    buffer = io.BytesIO()
    workbook.save(buffer)
    if len(buffer.getvalue()) >= targetSizeBytes or row >= _XLSX_MAX_ROWS:
        return buffer.getvalue()

    # Estimate was short (compression/overhead varies) — top up once more.
    bytesPerRow = max(1, len(buffer.getvalue()) // row)
    shortfallRows = min((targetSizeBytes - len(buffer.getvalue())) // bytesPerRow + 1, _XLSX_MAX_ROWS - row)
    for _ in range(max(0, shortfallRows)):
        sheet.append([index, f"row-{row}", row * index])
        row += 1

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def generatePptx(index: int, targetSizeBytes: int) -> bytes:
    presentation = Presentation()
    slideLayout = presentation.slide_layouts[1]
    slide = presentation.slides.add_slide(slideLayout)
    slide.shapes.title.text = f"Slide {index}"
    body = slide.placeholders[1].text_frame
    body.text = f"Generated presentation content for file {index}."
    while True:
        buffer = io.BytesIO()
        presentation.save(buffer)
        if len(buffer.getvalue()) >= targetSizeBytes or len(presentation.slides) > 200:
            return buffer.getvalue()
        extraSlide = presentation.slides.add_slide(presentation.slide_layouts[1])
        extraSlide.shapes.title.text = f"Slide {index}-{len(presentation.slides)}"


def generateMsg(index: int, targetSizeBytes: int) -> bytes:
    header = (
        f"From: sender{index}@example.com\r\n"
        f"To: recipient{index}@example.com\r\n"
        f"Subject: Sample message {index}\r\n"
        "Content-Type: text/plain\r\n\r\n"
    )
    body = f"This is a generated Outlook-style message body for file {index}.\r\n"
    content = (header + body).encode("utf-8")
    if len(content) < targetSizeBytes:
        content += b"\r\n" + b"padding " * ((targetSizeBytes - len(content)) // 8 + 1)
    return content[:max(targetSizeBytes, len(header) + len(body))]


def generateOdt(index: int, targetSizeBytes: int) -> bytes:
    return _buildMinimalZipDocument(
        mimeTypeContent="application/vnd.oasis.opendocument.text",
        contentXml=(
            "<?xml version=\"1.0\"?><office:document-content "
            "xmlns:office=\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\" "
            "xmlns:text=\"urn:oasis:names:tc:opendocument:xmlns:text:1.0\">"
            f"<office:body><office:text><text:p>Document {index}</text:p></office:text></office:body>"
            "</office:document-content>"
        ),
        targetSizeBytes=targetSizeBytes,
    )


def generateOds(index: int, targetSizeBytes: int) -> bytes:
    return _buildMinimalZipDocument(
        mimeTypeContent="application/vnd.oasis.opendocument.spreadsheet",
        contentXml=(
            "<?xml version=\"1.0\"?><office:document-content "
            "xmlns:office=\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\">"
            f"<office:body><office:spreadsheet>Sheet {index}</office:spreadsheet></office:body>"
            "</office:document-content>"
        ),
        targetSizeBytes=targetSizeBytes,
    )


def generateOdp(index: int, targetSizeBytes: int) -> bytes:
    return _buildMinimalZipDocument(
        mimeTypeContent="application/vnd.oasis.opendocument.presentation",
        contentXml=(
            "<?xml version=\"1.0\"?><office:document-content "
            "xmlns:office=\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\">"
            f"<office:body><office:presentation>Slide {index}</office:presentation></office:body>"
            "</office:document-content>"
        ),
        targetSizeBytes=targetSizeBytes,
    )


def _buildMinimalZipDocument(mimeTypeContent: str, contentXml: str, targetSizeBytes: int) -> bytes:
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", mimeTypeContent)
        archive.writestr("content.xml", contentXml)
        padding = "x" * max(0, targetSizeBytes - len(contentXml) - len(mimeTypeContent))
        if padding:
            archive.writestr("padding.txt", padding)
    return buffer.getvalue()


def buildOfficeFormatSpecs() -> list[FileFormatSpec]:
    docxMime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    xlsxMime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    pptxMime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    return [
        FileFormatSpec("docx", docxMime, generateDocx, "office"),
        FileFormatSpec("xlsx", xlsxMime, generateXlsx, "office"),
        FileFormatSpec("pptx", pptxMime, generatePptx, "office"),
        FileFormatSpec("msg", "application/vnd.ms-outlook", generateMsg, "office"),
        FileFormatSpec("odt", "application/vnd.oasis.opendocument.text", generateOdt, "office"),
        FileFormatSpec("ods", "application/vnd.oasis.opendocument.spreadsheet", generateOds, "office"),
        FileFormatSpec("odp", "application/vnd.oasis.opendocument.presentation", generateOdp, "office"),
    ]
