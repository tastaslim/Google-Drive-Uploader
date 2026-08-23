import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { ApiError, drivesApi } from "../api/client"
import type { SharedDriveResource } from "../api/types"
import { formatDate } from "../utils/format"
import { ChevronRightIcon, HardDriveIcon, RefreshIcon } from "../components/icons"

export function DrivesPage() {
  const [drives, setDrives] = useState<SharedDriveResource[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const response = await drivesApi.list({ pageSize: 100 })
      setDrives(response.drives)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load Shared Drives.")
      setDrives([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Shared Drives</h1>
          <p className="page-subtitle">
            Pick a Shared Drive to upload files, or browse and manage its contents.
          </p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load} disabled={loading}>
          <RefreshIcon width={14} height={14} />
          Refresh
        </button>
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      {loading && (
        <div className="drive-grid">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="card" style={{ padding: 20, height: 128 }}>
              <div className="skeleton" style={{ width: 44, height: 44, borderRadius: 12, marginBottom: 14 }} />
              <div className="skeleton" style={{ width: "70%", height: 14, marginBottom: 8 }} />
              <div className="skeleton" style={{ width: "40%", height: 12 }} />
            </div>
          ))}
        </div>
      )}

      {!loading && drives && drives.length === 0 && !error && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">
              <HardDriveIcon width={22} height={22} />
            </div>
            <div className="empty-state-title">No Shared Drives found</div>
            <div className="empty-state-body">
              The connected Google identity isn't a member of any Shared Drive yet.
            </div>
          </div>
        </div>
      )}

      {!loading && drives && drives.length > 0 && (
        <div className="drive-grid">
          {drives.map((drive) => (
            <Link key={drive.id} to={`/drives/${drive.id}/browse`} className="drive-card">
              <div className="drive-card-top">
                <div className="drive-card-icon">
                  <HardDriveIcon width={20} height={20} />
                </div>
                <ChevronRightIcon width={16} height={16} className="drive-card-arrow" />
              </div>
              <div>
                <div className="drive-card-name">{drive.name}</div>
                <div className="drive-card-meta">Created {formatDate(drive.createdTime)}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  )
}
