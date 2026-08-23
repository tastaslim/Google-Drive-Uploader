import { useCallback, useEffect, useState } from "react"
import { ApiError, trashApi } from "../api/client"
import type { FileResource } from "../api/types"
import { useDriveId } from "../hooks/useDriveId"
import { useIntersectionLoadMore } from "../hooks/useIntersectionLoadMore"
import { formatBytes, formatDate } from "../utils/format"
import { getFileTypeStyle, isFolderResource } from "../utils/fileType"
import { FolderIcon, RefreshIcon, RestoreIcon, TrashIcon } from "../components/icons"
import { FileTypeIcon } from "../components/FileTypeIcon"
import { ConfirmDialog } from "../components/ConfirmDialog"
import { Spinner } from "../components/Spinner"

const PAGE_SIZE = 500

function TypeBadge({ item }: { item: FileResource }) {
  const style = getFileTypeStyle(item.mimeType, item.name)
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "3px 9px",
        borderRadius: 999,
        fontSize: 11.5,
        fontWeight: 650,
        color: style.color,
        background: style.background,
      }}
    >
      {style.label}
    </span>
  )
}

export function TrashPage() {
  const sharedDriveIdOrUrl = useDriveId()

  const [items, setItems] = useState<FileResource[]>([])
  const [nextPageToken, setNextPageToken] = useState<string | null | undefined>(undefined)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [restoringItem, setRestoringItem] = useState<FileResource | null>(null)
  const [deletingItem, setDeletingItem] = useState<FileResource | null>(null)
  const [bulkRestoreOpen, setBulkRestoreOpen] = useState(false)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await trashApi.list({ sharedDriveIdOrUrl, pageSize: PAGE_SIZE })
      setItems(response.files)
      setNextPageToken(response.nextPageToken)
      setSelected(new Set())
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load trash.")
    } finally {
      setLoading(false)
    }
  }, [sharedDriveIdOrUrl])

  useEffect(() => {
    refresh()
  }, [refresh])

  const loadMore = useCallback(async () => {
    if (!nextPageToken || loadingMore) return
    setLoadingMore(true)
    try {
      const response = await trashApi.list({ sharedDriveIdOrUrl, pageSize: PAGE_SIZE, pageToken: nextPageToken })
      setItems((current) => [...current, ...response.files])
      setNextPageToken(response.nextPageToken)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load more items.")
    } finally {
      setLoadingMore(false)
    }
  }, [sharedDriveIdOrUrl, nextPageToken, loadingMore])

  const sentinelRef = useIntersectionLoadMore(loadMore, Boolean(nextPageToken) && !loading)

  function toggleSelected(id: string) {
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function toggleSelectAll() {
    setSelected((current) => (current.size === items.length ? new Set() : new Set(items.map((item) => item.id))))
  }

  async function handleConfirmRestore() {
    if (!restoringItem) return
    setBusy(true)
    try {
      await trashApi.restore(restoringItem.id, sharedDriveIdOrUrl)
      setRestoringItem(null)
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to restore item.")
    } finally {
      setBusy(false)
    }
  }

  async function handleConfirmDelete() {
    if (!deletingItem) return
    setBusy(true)
    try {
      await trashApi.permanentlyDelete(deletingItem.id, sharedDriveIdOrUrl)
      setDeletingItem(null)
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to permanently delete item.")
    } finally {
      setBusy(false)
    }
  }

  async function handleConfirmBulkRestore() {
    setBusy(true)
    try {
      for (const id of selected) {
        await trashApi.restore(id, sharedDriveIdOrUrl)
      }
      setBulkRestoreOpen(false)
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to restore selected items.")
    } finally {
      setBusy(false)
    }
  }

  async function handleConfirmBulkDelete() {
    setBusy(true)
    try {
      for (const id of selected) {
        await trashApi.permanentlyDelete(id, sharedDriveIdOrUrl)
      }
      setBulkDeleteOpen(false)
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to permanently delete selected items.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Trash</h1>
          <p className="page-subtitle">
            Items stay here until restored or permanently deleted. Permanent deletion cannot be undone.
          </p>
        </div>
      </div>

      {error && <div className="banner banner-error">{error}</div>}

      <div className="toolbar">
        <div className="toolbar-left">
          <button className="btn btn-secondary btn-sm" onClick={() => refresh()}>
            <RefreshIcon width={14} height={14} />
            Refresh
          </button>
        </div>
        <div className="toolbar-right">
          {selected.size > 0 && (
            <>
              <button className="btn btn-secondary btn-sm" onClick={() => setBulkRestoreOpen(true)}>
                <RestoreIcon width={14} height={14} />
                Restore {selected.size} selected
              </button>
              <button className="btn btn-danger btn-sm" onClick={() => setBulkDeleteOpen(true)}>
                <TrashIcon width={14} height={14} />
                Delete forever
              </button>
            </>
          )}
        </div>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: 32 }}>
                  <input
                    type="checkbox"
                    className="checkbox"
                    checked={items.length > 0 && selected.size === items.length}
                    onChange={toggleSelectAll}
                  />
                </th>
                <th>Name</th>
                <th>Type</th>
                <th>Size</th>
                <th>Originally modified</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={6}>
                    <div
                      style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: 12,
                        padding: "56px 24px",
                      }}
                    >
                      <Spinner size={28} />
                      <span style={{ fontSize: 13.5, color: "var(--color-text-muted)" }}>Loading…</span>
                    </div>
                  </td>
                </tr>
              )}
              {!loading &&
                items.map((item) => {
                  const folder = isFolderResource(item.mimeType)
                  const typeStyle = getFileTypeStyle(item.mimeType, item.name)
                  return (
                    <tr key={item.id}>
                      <td>
                        <input
                          type="checkbox"
                          className="checkbox"
                          checked={selected.has(item.id)}
                          onChange={() => toggleSelected(item.id)}
                        />
                      </td>
                      <td>
                        <div className="cell-name">
                          <div className={`cell-icon-wrap${folder ? " folder" : ""}`}>
                            {folder ? (
                              <FolderIcon width={15} height={15} />
                            ) : (
                              <FileTypeIcon color={typeStyle.color} glyph={typeStyle.glyph} size={30} />
                            )}
                          </div>
                          {item.name}
                        </div>
                      </td>
                      <td>
                        <TypeBadge item={item} />
                      </td>
                      <td className="cell-muted">{folder ? "—" : formatBytes(item.size)}</td>
                      <td className="cell-muted">{formatDate(item.modifiedTime)}</td>
                      <td>
                        <div className="cell-actions">
                          <button
                            className="btn btn-secondary btn-icon"
                            title="Restore"
                            onClick={() => setRestoringItem(item)}
                          >
                            <RestoreIcon width={14} height={14} />
                          </button>
                          <button
                            className="btn btn-danger btn-icon"
                            title="Delete forever"
                            onClick={() => setDeletingItem(item)}
                          >
                            <TrashIcon width={14} height={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">
                      <div className="empty-state-icon">
                        <TrashIcon width={20} height={20} />
                      </div>
                      <div className="empty-state-title">Trash is empty</div>
                      <div className="empty-state-body">Items you delete from this Shared Drive will show up here.</div>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {(nextPageToken || loadingMore) && (
          <div
            ref={sentinelRef}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "16px",
              borderTop: items.length > 0 ? "1px solid var(--color-border)" : "none",
            }}
          >
            {loadingMore ? (
              <span style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Loading more…</span>
            ) : (
              <span style={{ fontSize: 12, color: "var(--color-text-faint)" }}>Scroll to load more</span>
            )}
          </div>
        )}
      </div>

      {items.length > 0 && (
        <div style={{ fontSize: 12.5, color: "var(--color-text-faint)", marginTop: 12 }}>
          {items.length.toLocaleString()} item{items.length === 1 ? "" : "s"} in trash
          {!nextPageToken && " · all items loaded"}
        </div>
      )}

      {restoringItem && (
        <ConfirmDialog
          title="Restore item"
          message={`Restore "${restoringItem.name}" to its original location?`}
          confirmLabel="Restore"
          destructive={false}
          busy={busy}
          onCancel={() => setRestoringItem(null)}
          onConfirm={handleConfirmRestore}
        />
      )}

      {deletingItem && (
        <ConfirmDialog
          title="Delete forever"
          message={`Permanently delete "${deletingItem.name}"? This cannot be undone.`}
          confirmLabel="Delete forever"
          busy={busy}
          onCancel={() => setDeletingItem(null)}
          onConfirm={handleConfirmDelete}
        />
      )}

      {bulkRestoreOpen && (
        <ConfirmDialog
          title="Restore selected items"
          message={`Restore ${selected.size} item${selected.size === 1 ? "" : "s"} to their original location?`}
          confirmLabel="Restore"
          destructive={false}
          busy={busy}
          onCancel={() => setBulkRestoreOpen(false)}
          onConfirm={handleConfirmBulkRestore}
        />
      )}

      {bulkDeleteOpen && (
        <ConfirmDialog
          title="Delete forever"
          message={`Permanently delete ${selected.size} item${selected.size === 1 ? "" : "s"}? This cannot be undone.`}
          confirmLabel="Delete forever"
          busy={busy}
          onCancel={() => setBulkDeleteOpen(false)}
          onConfirm={handleConfirmBulkDelete}
        />
      )}
    </>
  )
}
