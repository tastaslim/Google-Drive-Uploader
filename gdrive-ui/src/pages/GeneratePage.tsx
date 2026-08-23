import { useEffect, useRef, useState } from "react"
import { ApiError, uploadsApi } from "../api/client"
import type { UploadJobResponse } from "../api/types"
import { useDriveId } from "../hooks/useDriveId"
import { StatusBadge } from "../components/StatusBadge"
import { Spinner } from "../components/Spinner"
import { formatBytes, formatDuration } from "../utils/format"
import { UploadIcon } from "../components/icons"
import { FolderPicker } from "../components/FolderPicker"

const AVERAGE_SIZE_PRESETS = [
  { label: "~2.5 MB (all small files)", value: 2.5 * 1024 * 1024 },
  { label: "~10 MB (a little large content)", value: 10 * 1024 * 1024 },
  { label: "~50 MB", value: 50 * 1024 * 1024 },
  { label: "~150 MB", value: 150 * 1024 * 1024 },
  { label: "~500 MB", value: 500 * 1024 * 1024 },
  { label: "~1 GB", value: 1 * 1024 * 1024 * 1024 },
  { label: "~5 GB", value: 5 * 1024 * 1024 * 1024 },
]

const POLL_INTERVAL_MS = 1500
const TERMINAL_STATUSES = new Set(["completed", "completed_with_errors", "failed", "cancelled"])

function EventStatusDot({ status }: { status: string }) {
  const color =
    status === "uploaded" ? "var(--color-success)" :
    status === "failed" ? "var(--color-danger)" :
    "var(--color-accent)"
  return <span style={{ width: 6, height: 6, borderRadius: 999, background: color, flexShrink: 0 }} />
}

export function GeneratePage() {
  const sharedDriveIdOrUrl = useDriveId()

  const [allExtensions, setAllExtensions] = useState<string[]>([])
  const [excludedExtensions, setExcludedExtensions] = useState<Set<string>>(new Set())
  const [extensionsLoading, setExtensionsLoading] = useState(true)
  const [extensionFilter, setExtensionFilter] = useState("")

  const [count, setCount] = useState(1000)
  const [averageFileSizeBytes, setAverageFileSizeBytes] = useState(AVERAGE_SIZE_PRESETS[0].value)
  const [destinationFolder, setDestinationFolder] = useState<{ id: string; name: string } | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [job, setJob] = useState<UploadJobResponse | null>(null)
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    uploadsApi
      .getFormats()
      .then((response) => setAllExtensions(response.extensions))
      .catch(() => setAllExtensions([]))
      .finally(() => setExtensionsLoading(false))
  }, [])

  useEffect(() => {
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current)
    }
  }, [])

  function stopPolling() {
    if (pollTimer.current) {
      clearInterval(pollTimer.current)
      pollTimer.current = null
    }
  }

  function startPolling(jobId: string) {
    stopPolling()
    pollTimer.current = setInterval(async () => {
      try {
        const updated = await uploadsApi.get(jobId)
        setJob(updated)
        if (TERMINAL_STATUSES.has(updated.status)) {
          stopPolling()
        }
      } catch {
        stopPolling()
      }
    }, POLL_INTERVAL_MS)
  }

  function toggleExtension(extension: string) {
    setExcludedExtensions((current) => {
      const next = new Set(current)
      if (next.has(extension)) next.delete(extension)
      else next.add(extension)
      return next
    })
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const created = await uploadsApi.create({
        count,
        sharedDriveIdOrUrl,
        folderId: destinationFolder?.id ?? null,
        averageFileSizeBytes,
        excludedExtensions: Array.from(excludedExtensions),
      })
      setJob(created)
      startPolling(created.jobId)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to start upload job.")
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCancel() {
    if (!job) return
    try {
      const cancelled = await uploadsApi.cancel(job.jobId)
      setJob(cancelled)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to cancel job.")
    }
  }

  const progressPercent = job && job.requestedCount > 0
    ? Math.round(((job.uploadedCount + job.failedCount) / job.requestedCount) * 100)
    : 0

  const visibleExtensions = allExtensions.filter((ext) =>
    ext.toLowerCase().includes(extensionFilter.toLowerCase()),
  )

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Generate &amp; Upload</h1>
          <p className="page-subtitle">
            Generate and stream synthetic files across 90+ formats into your Shared Drive as a background job,
            with live progress you can watch in real time.
          </p>
        </div>
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      {!job && (
        <div className="card card-padded" style={{ marginBottom: 24 }}>
          <form onSubmit={handleSubmit}>
            <div className="field-row">
              <div className="field-group">
                <label className="field-label" htmlFor="count">File count</label>
                <input
                  id="count"
                  type="number"
                  min={1}
                  max={200000}
                  className="text-input"
                  value={count}
                  onChange={(event) => setCount(Number(event.target.value))}
                />
              </div>
              <div className="field-group">
                <label className="field-label">Destination folder (optional)</label>
                <FolderPicker
                  sharedDriveIdOrUrl={sharedDriveIdOrUrl}
                  value={destinationFolder}
                  onChange={setDestinationFolder}
                />
                <span className="field-hint">
                  Search by name (partial match) or type a new name to create and use that folder. Leave empty for
                  the Shared Drive root.
                </span>
              </div>
            </div>

            <div className="field-group">
              <label className="field-label" htmlFor="averageSize">Average file size</label>
              <select
                id="averageSize"
                className="select-input"
                value={averageFileSizeBytes}
                onChange={(event) => setAverageFileSizeBytes(Number(event.target.value))}
              >
                {AVERAGE_SIZE_PRESETS.map((preset) => (
                  <option key={preset.value} value={preset.value}>
                    {preset.label}
                  </option>
                ))}
              </select>
              <span className="field-hint">
                A static number of large files (50MB-5GB, streamed without ever being held in memory) are mixed
                in with small generated files (&lt;10MB) to approximate this average.
              </span>
            </div>

            <div className="field-group">
              <label className="field-label">
                Formats to exclude {excludedExtensions.size > 0 && `(${excludedExtensions.size} excluded)`}
              </label>
              <input
                className="text-input"
                placeholder="Filter formats…"
                value={extensionFilter}
                onChange={(event) => setExtensionFilter(event.target.value)}
                style={{ marginBottom: 10 }}
              />
              {extensionsLoading ? (
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 12 }}>
                  <Spinner size={14} />
                  <span className="field-hint">Loading available formats…</span>
                </div>
              ) : (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(90px, 1fr))",
                    gap: 6,
                    maxHeight: 220,
                    overflowY: "auto",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-sm)",
                    padding: 10,
                  }}
                >
                  {visibleExtensions.map((extension) => (
                    <label
                      key={extension}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        fontSize: 12.5,
                        cursor: "pointer",
                      }}
                    >
                      <input
                        type="checkbox"
                        className="checkbox"
                        checked={!excludedExtensions.has(extension)}
                        onChange={() => toggleExtension(extension)}
                      />
                      .{extension}
                    </label>
                  ))}
                </div>
              )}
              <span className="field-hint">
                Unchecked formats are excluded from generation. All {allExtensions.length} formats are included by default.
              </span>
            </div>

            <button type="submit" className="btn btn-primary" disabled={submitting}>
              <UploadIcon width={16} height={16} />
              {submitting ? "Starting..." : "Start generating"}
            </button>
          </form>
        </div>
      )}

      {job && (
        <div className="card">
          <div className="card-header">
            <h2>Job {job.jobId.slice(0, 8)}</h2>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <StatusBadge status={job.status} />
              {!TERMINAL_STATUSES.has(job.status) && (
                <button className="btn btn-secondary btn-sm" onClick={handleCancel}>
                  Cancel
                </button>
              )}
              {TERMINAL_STATUSES.has(job.status) && (
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    setJob(null)
                    setError(null)
                  }}
                >
                  Start another
                </button>
              )}
            </div>
          </div>
          <div className="card-padded">
            <div className="progress-track" style={{ marginBottom: 20 }}>
              <div
                className={`progress-fill${job.failedCount > 0 ? " danger" : job.status === "completed" ? " success" : ""}`}
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            <div className="stat-grid">
              <div className="stat-tile">
                <div className="stat-tile-label">Uploaded</div>
                <div className="stat-tile-value">{job.uploadedCount.toLocaleString()}</div>
              </div>
              <div className="stat-tile">
                <div className="stat-tile-label">Failed</div>
                <div className="stat-tile-value">{job.failedCount.toLocaleString()}</div>
              </div>
              <div className="stat-tile">
                <div className="stat-tile-label">Remaining</div>
                <div className="stat-tile-value">{job.remainingCount.toLocaleString()}</div>
              </div>
              <div className="stat-tile">
                <div className="stat-tile-label">Elapsed</div>
                <div className="stat-tile-value">{formatDuration(job.elapsedSeconds)}</div>
              </div>
            </div>

            <div style={{ fontSize: 13.5, color: "var(--color-text-muted)", marginBottom: 20 }}>
              <strong style={{ color: "var(--color-text)" }}>{job.smallFileCount.toLocaleString()}</strong> small files
              {Object.keys(job.largeFileCountsByBucket).length > 0 && (
                <>
                  {" "}+{" "}
                  {Object.entries(job.largeFileCountsByBucket)
                    .map(([bucket, bucketCount]) => `${bucketCount} × ${bucket}`)
                    .join(", ")}
                </>
              )}
              {job.excludedExtensions.length > 0 && (
                <div style={{ marginTop: 4 }}>
                  Excluding: {job.excludedExtensions.map((ext) => `.${ext}`).join(", ")}
                </div>
              )}
            </div>

            <div className="field-label" style={{ marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
              Live activity
              {!TERMINAL_STATUSES.has(job.status) && <Spinner size={12} />}
            </div>
            <div
              style={{
                maxHeight: 320,
                overflowY: "auto",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-sm)",
                fontFamily: "var(--font-mono)",
                fontSize: 12,
              }}
            >
              {job.recentEvents.length === 0 && (
                <div style={{ padding: 16, color: "var(--color-text-faint)", fontFamily: "var(--font-sans)" }}>
                  Waiting for activity…
                </div>
              )}
              {[...job.recentEvents].reverse().map((jobEvent, index) => (
                <div
                  key={`${jobEvent.fileIndex}-${jobEvent.status}-${index}`}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "6px 12px",
                    borderBottom: "1px solid var(--color-border)",
                  }}
                >
                  <EventStatusDot status={jobEvent.status} />
                  <span style={{ color: "var(--color-text-faint)", width: 66, flexShrink: 0 }}>
                    {jobEvent.status}
                  </span>
                  <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {jobEvent.fileName}
                  </span>
                  {jobEvent.sizeBytes !== null && (
                    <span style={{ color: "var(--color-text-faint)", flexShrink: 0 }}>
                      {formatBytes(jobEvent.sizeBytes)}
                    </span>
                  )}
                </div>
              ))}
            </div>

            {job.errors.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div className="field-label" style={{ marginBottom: 8 }}>Errors</div>
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>File</th>
                        <th>Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {job.errors.map((jobError) => (
                        <tr key={jobError.fileIndex}>
                          <td className="cell-muted">{jobError.fileName}</td>
                          <td>{jobError.errorMessage}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}
