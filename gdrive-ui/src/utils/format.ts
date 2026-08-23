export function formatBytes(bytes: number | string | null | undefined): string {
  if (bytes === null || bytes === undefined) return "—"
  const numericBytes = typeof bytes === "string" ? Number(bytes) : bytes
  if (Number.isNaN(numericBytes)) return "—"
  if (numericBytes === 0) return "0 B"

  const units = ["B", "KB", "MB", "GB", "TB"]
  const exponent = Math.min(Math.floor(Math.log(numericBytes) / Math.log(1024)), units.length - 1)
  const value = numericBytes / 1024 ** exponent
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`
}

export function formatDate(value: string | number | null | undefined): string {
  if (!value) return "—"
  const date = typeof value === "number" ? new Date(value * 1000) : new Date(value)
  if (Number.isNaN(date.getTime())) return "—"
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return "—"
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  if (minutes < 60) return `${minutes}m ${remainingSeconds}s`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ${minutes % 60}m`
}
