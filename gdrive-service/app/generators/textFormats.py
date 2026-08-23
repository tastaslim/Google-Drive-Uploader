"""Plain text, markup, code, and structured-data generators."""
import json
import random
import string

from app.generators.models import FileFormatSpec

_WORDS = [
    "alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel",
    "india", "juliet", "kilo", "lima", "mike", "november", "oscar", "papa",
]


def _randomSentence(rng: random.Random, wordCount: int = 12) -> str:
    return " ".join(rng.choice(_WORDS) for _ in range(wordCount))


def _padToSize(content: str, targetSizeBytes: int) -> bytes:
    data = content.encode("utf-8")
    if len(data) >= targetSizeBytes:
        return data
    padding = ("\n# " + "x" * 76) * ((targetSizeBytes - len(data)) // 80 + 1)
    return (content + "\n" + padding).encode("utf-8")[:max(targetSizeBytes, len(data))]


def generateTxt(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    lines = [f"Generated text file #{index}", f"Timestamp seed: {index}", ""]
    currentSizeBytes = len("\n".join(lines).encode("utf-8"))
    while currentSizeBytes < targetSizeBytes:
        line = _randomSentence(rng)
        lines.append(line)
        currentSizeBytes += len(line.encode("utf-8")) + 1
    return "\n".join(lines).encode("utf-8")


def generateMarkdown(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    body = [f"# Document {index}", "", f"Generated on seed {index}.", "", "## Section 1", ""]
    currentSizeBytes = len("\n".join(body).encode("utf-8"))
    while currentSizeBytes < targetSizeBytes:
        line = f"- {_randomSentence(rng, 8)}"
        body.append(line)
        currentSizeBytes += len(line.encode("utf-8")) + 1
    return "\n".join(body).encode("utf-8")


def generateRtf(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    text = _randomSentence(rng, 40)
    rtf = r"{\rtf1\ansi\deff0 {\fonttbl{\f0 Arial;}} \f0\fs24 " + f"File {index}. {text}" + r" }"
    return _padToSize(rtf, targetSizeBytes)


def generateLog(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    levels = ["INFO", "WARN", "ERROR", "DEBUG"]
    lines = []
    lineIndex = 0
    currentSizeBytes = 0
    while currentSizeBytes < targetSizeBytes:
        line = f"[{lineIndex:06d}] {rng.choice(levels)} seed={index} {_randomSentence(rng, 6)}"
        lines.append(line)
        currentSizeBytes += len(line.encode("utf-8")) + 1
        lineIndex += 1
    return "\n".join(lines).encode("utf-8")


def generateIni(index: int, targetSizeBytes: int) -> bytes:
    content = f"[general]\nid = {index}\nname = file-{index}\n\n[settings]\nenabled = true\nlevel = {index % 10}\n"
    return _padToSize(content, targetSizeBytes)


def generateCfg(index: int, targetSizeBytes: int) -> bytes:
    return generateIni(index, targetSizeBytes)


def generateJson(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    payload = {
        "id": index,
        "name": f"file-{index}",
        "status": "active",
        "tags": [rng.choice(_WORDS) for _ in range(5)],
        "metadata": {"generatedBy": "gdrive-service", "seed": index},
    }
    data = json.dumps(payload, indent=2)
    padded = data
    if len(padded.encode("utf-8")) < targetSizeBytes:
        payload["padding"] = "x" * (targetSizeBytes - len(data.encode("utf-8")))
        padded = json.dumps(payload, indent=2)
    return padded.encode("utf-8")


def generateCsv(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    rows = ["id,name,value,category"]
    rowIndex = 0
    currentSizeBytes = len(rows[0].encode("utf-8"))
    while currentSizeBytes < targetSizeBytes:
        row = f"{index}-{rowIndex},sample-{rowIndex},{rng.randint(0, 10000)},{rng.choice(_WORDS)}"
        rows.append(row)
        currentSizeBytes += len(row.encode("utf-8")) + 1
        rowIndex += 1
    return "\n".join(rows).encode("utf-8")


def generateTsv(index: int, targetSizeBytes: int) -> bytes:
    csvBytes = generateCsv(index, targetSizeBytes)
    return csvBytes.replace(b",", b"\t")


def generateXml(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    items = []
    itemIndex = 0
    currentSizeBytes = 0
    while currentSizeBytes < targetSizeBytes:
        item = f"  <item id=\"{itemIndex}\">{_randomSentence(rng, 4)}</item>"
        items.append(item)
        currentSizeBytes += len(item.encode("utf-8")) + 1
        itemIndex += 1
    body = f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<root fileId=\"{index}\">\n" + "\n".join(items) + "\n</root>"
    return body.encode("utf-8")


def generateHtml(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    paragraphs = [f"<p>{_randomSentence(rng, 15)}</p>" for _ in range(5)]
    currentSizeBytes = sum(len(p.encode("utf-8")) for p in paragraphs)
    while currentSizeBytes < targetSizeBytes:
        paragraph = f"<p>{_randomSentence(rng, 15)}</p>"
        paragraphs.append(paragraph)
        currentSizeBytes += len(paragraph.encode("utf-8"))
    body = f"<html><head><title>File {index}</title></head><body><h1>File {index}</h1>" + "".join(paragraphs) + "</body></html>"
    return body.encode("utf-8")


def generateYaml(index: int, targetSizeBytes: int) -> bytes:
    rng = random.Random(index)
    lines = [f"id: {index}", f"name: file-{index}", "tags:"]
    currentSizeBytes = len("\n".join(lines).encode("utf-8"))
    while currentSizeBytes < targetSizeBytes:
        line = f"  - {rng.choice(_WORDS)}"
        lines.append(line)
        currentSizeBytes += len(line.encode("utf-8")) + 1
    return "\n".join(lines).encode("utf-8")


def generateToml(index: int, targetSizeBytes: int) -> bytes:
    content = f"[file]\nid = {index}\nname = \"file-{index}\"\nenabled = true\n"
    return _padToSize(content, targetSizeBytes)


def _makeSourceCodeGenerator(commentPrefix: str, template: str):
    def _generate(index: int, targetSizeBytes: int) -> bytes:
        rng = random.Random(index)
        lines = [f"{commentPrefix} Generated source file {index}", template.format(index=index)]
        currentSizeBytes = len("\n".join(lines).encode("utf-8"))
        counter = 0
        while currentSizeBytes < targetSizeBytes:
            line = f"{commentPrefix} {_randomSentence(rng, 6)} {counter}"
            lines.append(line)
            currentSizeBytes += len(line.encode("utf-8")) + 1
            counter += 1
        return "\n".join(lines).encode("utf-8")

    return _generate


generatePython = _makeSourceCodeGenerator("#", "def handleFile{index}():\n    return {index}")
generateGo = _makeSourceCodeGenerator("//", "func HandleFile{index}() int {{\n    return {index}\n}}")
generateJava = _makeSourceCodeGenerator("//", "class File{index} {{ int id = {index}; }}")
generateCpp = _makeSourceCodeGenerator("//", "int handleFile{index}() {{ return {index}; }}")
generateC = _makeSourceCodeGenerator("//", "int handle_file_{index}(void) {{ return {index}; }}")
generateCSharp = _makeSourceCodeGenerator("//", "class File{index} {{ int Id = {index}; }}")
generateJavaScript = _makeSourceCodeGenerator("//", "function handleFile{index}() {{ return {index}; }}")
generateTypeScript = _makeSourceCodeGenerator("//", "export function handleFile{index}(): number {{ return {index}; }}")
generatePhp = _makeSourceCodeGenerator("//", "function handleFile{index}() {{ return {index}; }}")
generateRuby = _makeSourceCodeGenerator("#", "def handle_file_{index}\n  {index}\nend")
generateSwift = _makeSourceCodeGenerator("//", "func handleFile{index}() -> Int {{ return {index} }}")
generateKotlin = _makeSourceCodeGenerator("//", "fun handleFile{index}(): Int = {index}")
generateRust = _makeSourceCodeGenerator("//", "fn handle_file_{index}() -> i32 {{ {index} }}")
generateShell = _makeSourceCodeGenerator("#", "echo \"file {index}\"")
generateSql = _makeSourceCodeGenerator("--", "SELECT {index} AS file_id;")


def buildTextFormatSpecs() -> list[FileFormatSpec]:
    return [
        FileFormatSpec("txt", "text/plain", generateTxt, "text"),
        FileFormatSpec("md", "text/markdown", generateMarkdown, "text"),
        FileFormatSpec("rtf", "application/rtf", generateRtf, "text"),
        FileFormatSpec("log", "text/plain", generateLog, "text"),
        FileFormatSpec("ini", "text/plain", generateIni, "text"),
        FileFormatSpec("cfg", "text/plain", generateCfg, "text"),
        FileFormatSpec("json", "application/json", generateJson, "data"),
        FileFormatSpec("csv", "text/csv", generateCsv, "data"),
        FileFormatSpec("tsv", "text/tab-separated-values", generateTsv, "data"),
        FileFormatSpec("xml", "application/xml", generateXml, "data"),
        FileFormatSpec("html", "text/html", generateHtml, "text"),
        FileFormatSpec("yaml", "application/x-yaml", generateYaml, "data"),
        FileFormatSpec("toml", "application/toml", generateToml, "data"),
        FileFormatSpec("py", "text/x-python", generatePython, "code"),
        FileFormatSpec("go", "text/x-go", generateGo, "code"),
        FileFormatSpec("java", "text/x-java-source", generateJava, "code"),
        FileFormatSpec("cpp", "text/x-c++src", generateCpp, "code"),
        FileFormatSpec("c", "text/x-csrc", generateC, "code"),
        FileFormatSpec("cs", "text/x-csharp", generateCSharp, "code"),
        FileFormatSpec("js", "application/javascript", generateJavaScript, "code"),
        FileFormatSpec("ts", "application/typescript", generateTypeScript, "code"),
        FileFormatSpec("php", "application/x-httpd-php", generatePhp, "code"),
        FileFormatSpec("rb", "text/x-ruby", generateRuby, "code"),
        FileFormatSpec("swift", "text/x-swift", generateSwift, "code"),
        FileFormatSpec("kt", "text/x-kotlin", generateKotlin, "code"),
        FileFormatSpec("rs", "text/x-rust", generateRust, "code"),
        FileFormatSpec("sh", "application/x-sh", generateShell, "code"),
        FileFormatSpec("sql", "application/sql", generateSql, "code"),
    ]
