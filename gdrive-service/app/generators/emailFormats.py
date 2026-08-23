"""Email and calendar generators using the stdlib email package for valid EML/MBOX."""
from email.message import EmailMessage

from app.generators.models import FileFormatSpec


def _buildEmailMessage(index: int, bodyPadding: str = "") -> EmailMessage:
    message = EmailMessage()
    message["From"] = f"sender{index}@example.com"
    message["To"] = f"recipient{index}@example.com"
    message["Subject"] = f"Generated message {index}"
    message.set_content(f"This is generated email body {index}.\n{bodyPadding}")
    return message


def generateEml(index: int, targetSizeBytes: int) -> bytes:
    message = _buildEmailMessage(index)
    content = bytes(message)
    if len(content) < targetSizeBytes:
        padding = "x" * (targetSizeBytes - len(content))
        message = _buildEmailMessage(index, padding)
        content = bytes(message)
    return content


def generateMbox(index: int, targetSizeBytes: int) -> bytes:
    entries = []
    entryIndex = 0
    currentSizeBytes = 0
    while currentSizeBytes < targetSizeBytes:
        message = _buildEmailMessage(index * 1000 + entryIndex)
        entry = f"From mailbox@example.com Mon Jan 01 00:00:00 2024\n{bytes(message).decode('utf-8')}\n"
        entries.append(entry)
        currentSizeBytes += len(entry.encode("utf-8"))
        entryIndex += 1
    return "".join(entries).encode("utf-8")


def generateIcs(index: int, targetSizeBytes: int) -> bytes:
    event = (
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\n"
        f"UID:{index}@example.com\r\nSUMMARY:Event {index}\r\n"
        "DTSTART:20240101T090000Z\r\nDTEND:20240101T100000Z\r\n"
        "END:VEVENT\r\nEND:VCALENDAR\r\n"
    )
    data = event.encode("utf-8")
    if len(data) < targetSizeBytes:
        data += b"\r\n" + b"# padding\r\n" * ((targetSizeBytes - len(data)) // 12 + 1)
    return data


def generateVcf(index: int, targetSizeBytes: int) -> bytes:
    card = (
        "BEGIN:VCARD\r\nVERSION:3.0\r\n"
        f"FN:Contact {index}\r\nEMAIL:contact{index}@example.com\r\n"
        "END:VCARD\r\n"
    )
    data = card.encode("utf-8")
    if len(data) < targetSizeBytes:
        data += b"\r\n" + b"# padding\r\n" * ((targetSizeBytes - len(data)) // 12 + 1)
    return data


def buildEmailFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("eml", "message/rfc822", generateEml, "email"),
        FileFormatSpec("mbox", "application/mbox", generateMbox, "email"),
        FileFormatSpec("ics", "text/calendar", generateIcs, "calendar"),
        FileFormatSpec("vcf", "text/vcard", generateVcf, "calendar"),
    ]
