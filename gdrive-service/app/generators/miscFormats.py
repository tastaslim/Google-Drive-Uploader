"""Fonts, certificates, and other binary miscellany.
Certificates are generated as real self-signed X.509/PEM material via the
`cryptography` library when available; fonts/executables use structurally
valid magic-byte headers padded to size, since authoring real TTF/OTF glyph
tables or native binaries is out of scope for synthetic test data."""
import datetime

from app.generators.models import FileFormatSpec


def _paddedWithHeader(header: bytes, index: int, targetSizeBytes: int) -> bytes:
    remaining = max(0, targetSizeBytes - len(header))
    filler = bytes(((index + i) % 256 for i in range(min(remaining, 65536) or 1)))
    body = (filler * (remaining // max(len(filler), 1) + 1))[:remaining]
    return header + body


def generateTtf(index: int, targetSizeBytes: int) -> bytes:
    sfntHeader = bytes([0x00, 0x01, 0x00, 0x00])
    return _paddedWithHeader(sfntHeader, index, targetSizeBytes)


def generateOtf(index: int, targetSizeBytes: int) -> bytes:
    return _paddedWithHeader(b"OTTO", index, targetSizeBytes)


def generateWoff(index: int, targetSizeBytes: int) -> bytes:
    return _paddedWithHeader(b"wOFF", index, targetSizeBytes)


def generateWoff2(index: int, targetSizeBytes: int) -> bytes:
    return _paddedWithHeader(b"wOF2", index, targetSizeBytes)


def _generateSelfSignedCert(index: int):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    privateKey = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"file-{index}.example.com")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(privateKey.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .sign(privateKey, hashes.SHA256())
    )
    return privateKey, certificate


def generatePem(index: int, targetSizeBytes: int) -> bytes:
    from cryptography.hazmat.primitives import serialization

    _, certificate = _generateSelfSignedCert(index)
    return certificate.public_bytes(serialization.Encoding.PEM)


def generateCrt(index: int, targetSizeBytes: int) -> bytes:
    return generatePem(index, targetSizeBytes)


def generateKey(index: int, targetSizeBytes: int) -> bytes:
    from cryptography.hazmat.primitives import serialization

    privateKey, _ = _generateSelfSignedCert(index)
    return privateKey.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def generatePfx(index: int, targetSizeBytes: int) -> bytes:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12

    privateKey, certificate = _generateSelfSignedCert(index)
    return pkcs12.serialize_key_and_certificates(
        name=f"file-{index}".encode(),
        key=privateKey,
        cert=certificate,
        cas=None,
        encryption_algorithm=serialization.NoEncryption(),
    )


def buildMiscFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("ttf", "font/ttf", generateTtf, "font"),
        FileFormatSpec("otf", "font/otf", generateOtf, "font"),
        FileFormatSpec("woff", "font/woff", generateWoff, "font"),
        FileFormatSpec("woff2", "font/woff2", generateWoff2, "font"),
        FileFormatSpec("pem", "application/x-pem-file", generatePem, "certificate"),
        FileFormatSpec("crt", "application/x-x509-ca-cert", generateCrt, "certificate"),
        FileFormatSpec("key", "application/pkcs8", generateKey, "certificate"),
        FileFormatSpec("pfx", "application/x-pkcs12", generatePfx, "certificate"),
    ]
