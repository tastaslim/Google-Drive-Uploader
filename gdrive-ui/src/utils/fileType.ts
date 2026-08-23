export type FileGlyph =
  | "letter-pdf"
  | "letter-doc"
  | "letter-sheet"
  | "letter-slide"
  | "letter-ebook"
  | "text"
  | "data"
  | "database"
  | "image"
  | "video"
  | "audio"
  | "archive"
  | "email"
  | "calendar"
  | "font"
  | "certificate"
  | "code"
  | "none"

export interface FileTypeStyle {
  label: string
  color: string
  background: string
  glyph: FileGlyph
}

const GOOGLE_NATIVE_STYLES: Record<string, FileTypeStyle> = {
  "application/vnd.google-apps.document": { label: "Doc", color: "#2563eb", background: "#eaf1ff", glyph: "letter-doc" },
  "application/vnd.google-apps.spreadsheet": { label: "Sheet", color: "#16a34a", background: "#eafbf1", glyph: "letter-sheet" },
  "application/vnd.google-apps.presentation": { label: "Slides", color: "#d97706", background: "#fff6e5", glyph: "letter-slide" },
  "application/vnd.google-apps.vid": { label: "Vid", color: "#9333ea", background: "#f5ecff", glyph: "video" },
  "application/vnd.google-apps.form": { label: "Form", color: "#673ab7", background: "#efeafd", glyph: "letter-doc" },
  "application/vnd.google-apps.drawing": { label: "Drawing", color: "#dc2626", background: "#fdecec", glyph: "image" },
  "application/vnd.google-apps.site": { label: "Site", color: "#2563eb", background: "#eaf1ff", glyph: "code" },
  "application/vnd.google-apps.script": { label: "Script", color: "#4b5563", background: "#eef0f3", glyph: "code" },
  "application/vnd.google-apps.folder": { label: "Folder", color: "#3b5bfd", background: "#eef1ff", glyph: "none" },
}

const RED = { color: "#dc2626", background: "#fdecec" }
const BLUE = { color: "#2563eb", background: "#eaf1ff" }
const GREEN = { color: "#16a34a", background: "#eafbf1" }
const YELLOW = { color: "#d97706", background: "#fff6e5" }
const CYAN = { color: "#0891b2", background: "#e7f8fb" }
const PINK = { color: "#db2777", background: "#fdedf5" }
const PURPLE = { color: "#9333ea", background: "#f5ecff" }
const VIOLET = { color: "#673ab7", background: "#efeafd" }
const GRAY = { color: "#4b5563", background: "#eef0f3" }
const AMBER = { color: "#b45309", background: "#fef3e2" }
const SLATE = { color: "#334155", background: "#eef1f5" }
const TEAL = { color: "#0d9488", background: "#e6faf7" }

interface ExtensionGroup {
  extensions: string[]
  label: string
  style: { color: string; background: string }
  glyph: FileGlyph
}

const EXTENSION_GROUPS: ExtensionGroup[] = [
  // Documents
  { extensions: ["pdf"], label: "PDF", style: RED, glyph: "letter-pdf" },
  { extensions: ["doc", "docx", "dot", "dotx", "odt", "rtf"], label: "Word", style: BLUE, glyph: "letter-doc" },
  { extensions: ["xls", "xlsx", "xlsm", "xlsb", "ods", "csv", "tsv"], label: "Excel", style: GREEN, glyph: "letter-sheet" },
  { extensions: ["ppt", "pptx", "pps", "ppsx", "odp"], label: "PowerPoint", style: YELLOW, glyph: "letter-slide" },
  { extensions: ["epub", "mobi"], label: "eBook", style: AMBER, glyph: "letter-ebook" },
  { extensions: ["txt", "md", "log"], label: "Text", style: GRAY, glyph: "text" },

  // Config / data
  { extensions: ["json", "yaml", "yml", "toml", "xml", "ini", "cfg"], label: "Data", style: SLATE, glyph: "data" },
  { extensions: ["sqlite", "db", "parquet", "pickle", "npy"], label: "Database", style: TEAL, glyph: "database" },

  // Images
  { extensions: ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp", "heic"], label: "Image", style: CYAN, glyph: "image" },
  { extensions: ["svg"], label: "Vector", style: CYAN, glyph: "image" },
  { extensions: ["ico"], label: "Icon", style: CYAN, glyph: "image" },

  // Media
  { extensions: ["mp4", "mov", "webm", "avi", "mkv", "mpeg", "3gp"], label: "Video", style: PINK, glyph: "video" },
  { extensions: ["mp3", "wav", "flac", "ogg", "m4a", "aac"], label: "Audio", style: PURPLE, glyph: "audio" },

  // Archives
  { extensions: ["zip", "tar", "tar.gz", "tar.bz2", "gz", "bz2", "xz", "7z", "rar"], label: "Archive", style: VIOLET, glyph: "archive" },

  // Email / calendar
  { extensions: ["eml", "msg", "mbox", "pst", "ost"], label: "Email", style: SLATE, glyph: "email" },
  { extensions: ["ics", "vcf"], label: "Calendar", style: SLATE, glyph: "calendar" },

  // Fonts
  { extensions: ["ttf", "otf", "woff", "woff2"], label: "Font", style: AMBER, glyph: "font" },

  // Certificates / keys
  { extensions: ["pem", "crt", "cer", "key", "pfx", "p12"], label: "Certificate", style: GRAY, glyph: "certificate" },

  // Code
  {
    extensions: [
      "py", "go", "java", "cpp", "c", "cs", "js", "ts", "tsx", "jsx", "php", "rb", "swift",
      "kt", "rs", "sh", "sql", "html", "css", "scss",
    ],
    label: "Code",
    style: SLATE,
    glyph: "code",
  },
]

const EXTENSION_TO_STYLE: Record<
  string,
  { label: string; style: { color: string; background: string }; glyph: FileGlyph }
> = {}
for (const group of EXTENSION_GROUPS) {
  for (const extension of group.extensions) {
    EXTENSION_TO_STYLE[extension] = { label: group.label, style: group.style, glyph: group.glyph }
  }
}

const DEFAULT_STYLE: FileTypeStyle = { label: "File", color: GRAY.color, background: GRAY.background, glyph: "none" }

export const FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

export function isFolderResource(mimeType: string): boolean {
  return mimeType === FOLDER_MIME_TYPE
}

function extractExtension(name: string): string | undefined {
  // Handle compound extensions like "tar.gz" before falling back to the
  // last dot-segment, so archives don't get misclassified as a ".gz" file.
  const lower = name.toLowerCase()
  if (lower.endsWith(".tar.gz")) return "tar.gz"
  if (lower.endsWith(".tar.bz2")) return "tar.bz2"
  if (!lower.includes(".")) return undefined
  return lower.split(".").pop()
}

export function getFileTypeStyle(mimeType: string, name: string): FileTypeStyle {
  if (GOOGLE_NATIVE_STYLES[mimeType]) return GOOGLE_NATIVE_STYLES[mimeType]

  const extension = extractExtension(name)
  if (extension && EXTENSION_TO_STYLE[extension]) {
    const { label, style, glyph } = EXTENSION_TO_STYLE[extension]
    return { label, color: style.color, background: style.background, glyph }
  }

  if (mimeType.startsWith("image/")) return { label: "Image", ...CYAN, glyph: "image" }
  if (mimeType.startsWith("video/")) return { label: "Video", ...PINK, glyph: "video" }
  if (mimeType.startsWith("audio/")) return { label: "Audio", ...PURPLE, glyph: "audio" }
  if (mimeType === "application/zip" || mimeType.includes("compressed")) return { label: "Archive", ...VIOLET, glyph: "archive" }
  if (mimeType === "text/plain") return { label: "Text", ...GRAY, glyph: "text" }

  return DEFAULT_STYLE
}
