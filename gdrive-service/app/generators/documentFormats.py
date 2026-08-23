"""PDF and e-book style generators."""
import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.generators.models import FileFormatSpec


def generatePdf(index: int, targetSizeBytes: int) -> bytes:
    buffer = io.BytesIO()
    pdfCanvas = canvas.Canvas(buffer, pagesize=letter)
    pageCount = 0
    while True:
        pdfCanvas.drawString(100, 750, f"PDF file {index} - page {pageCount}")
        pdfCanvas.drawString(100, 720, "Generated content " * 5)
        pdfCanvas.showPage()
        pageCount += 1
        currentSize = len(buffer.getvalue())
        if currentSize >= targetSizeBytes or pageCount > 500:
            pdfCanvas.save()
            return buffer.getvalue()


def generateEpub(index: int, targetSizeBytes: int) -> bytes:
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr(
            "content.opf",
            f"<?xml version=\"1.0\"?><package><metadata><title>Book {index}</title></metadata></package>",
        )
        contentText = f"<html><body><h1>Chapter {index}</h1><p>Generated ebook content.</p></body></html>"
        archive.writestr("chapter1.xhtml", contentText)
        currentSize = len(buffer.getvalue())
        if currentSize < targetSizeBytes:
            archive.writestr("padding.txt", "x" * (targetSizeBytes - currentSize))
    return buffer.getvalue()


def buildDocumentFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("pdf", "application/pdf", generatePdf, "document"),
        FileFormatSpec("epub", "application/epub+zip", generateEpub, "document"),
    ]
