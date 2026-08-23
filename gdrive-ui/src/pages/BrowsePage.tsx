import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { ApiError, filesApi, foldersApi } from "../api/client"
import type { FileResource, NativeAppType } from "../api/types"
import { useDriveId } from "../hooks/useDriveId"
import { useDriveName } from "../hooks/useDriveName"
import { useIntersectionLoadMore } from "../hooks/useIntersectionLoadMore"
import { formatBytes, formatDate } from "../utils/format"
import { getFileTypeStyle, isFolderResource } from "../utils/fileType"
import {
  DownloadIcon,
  EditIcon,
  FolderIcon,
  HardDriveIcon,
  RefreshIcon,
  StarIcon,
  TrashIcon,
} from "../components/icons"
import { EditResourceModal } from "../components/EditResourceModal"
import { ConfirmDialog } from "../components/ConfirmDialog"
import { DetailRow, DetailsPanel } from "../components/DetailsPanel"
import { Spinner } from "../components/Spinner"
import { ContextMenu, type ContextMenuPosition } from "../components/ContextMenu"
import { FileTypeIcon } from "../components/FileTypeIcon"
import { useFolderStats } from "../hooks/useFolderStats"

const PAGE_SIZE = 500

interface BreadcrumbEntry {
  id: string | undefined
  name: string
}

interface WebkitFile extends File {
  webkitRelativePath: string
}

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

/** Shows a folder row's recursive item count, fetched lazily and cached (see useFolderStats). */
function FolderItemCountCell({ folderId, sharedDriveIdOrUrl }: { folderId: string; sharedDriveIdOrUrl: string }) {
  const { stats, loading, error } = useFolderStats(folderId, sharedDriveIdOrUrl, true)
  if (loading) return <Spinner size={12} />
  if (error) return <span title={error}>—</span>
  if (!stats) return <span>—</span>
  const total = stats.fileCount + stats.folderCount
  return <span>{total.toLocaleString()} item{total === 1 ? "" : "s"}</span>
}

/** Shows a folder row's recursive total size, fetched lazily and cached (see useFolderStats). */
function FolderSizeCell({ folderId, sharedDriveIdOrUrl }: { folderId: string; sharedDriveIdOrUrl: string }) {
  const { stats, loading, error } = useFolderStats(folderId, sharedDriveIdOrUrl, true)
  if (loading) return <Spinner size={12} />
  if (error) return <span>—</span>
  if (!stats) return <span>—</span>
  return <span>{formatBytes(stats.totalSizeBytes)}</span>
}

/** Encodes the breadcrumb chain (minus root) as URL path segments of folderId:name pairs. */
function encodePathSegment(entry: BreadcrumbEntry): string {
  return `${entry.id}~${encodeURIComponent(entry.name)}`
}

function decodePathSegment(segment: string): BreadcrumbEntry {
  const separatorIndex = segment.indexOf("~")
  if (separatorIndex === -1) return { id: segment, name: segment }
  return {
    id: segment.slice(0, separatorIndex),
    name: decodeURIComponent(segment.slice(separatorIndex + 1)),
  }
}

export function BrowsePage() {
  const sharedDriveIdOrUrl = useDriveId()
  const navigate = useNavigate()
  const params = useParams<{ "*": string }>()
  const driveName = useDriveName(sharedDriveIdOrUrl)

  const breadcrumbs = useMemo<BreadcrumbEntry[]>(() => {
    const raw = params["*"] ?? ""
    const segments = raw ? raw.split("/").filter(Boolean) : []
    return [{ id: undefined, name: driveName ?? "Shared Drive" }, ...segments.map(decodePathSegment)]
  }, [params, driveName])

  const currentFolderId = breadcrumbs[breadcrumbs.length - 1]?.id

  const [items, setItems] = useState<FileResource[]>([])
  const [nextPageToken, setNextPageToken] = useState<string | null | undefined>(undefined)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [editingItem, setEditingItem] = useState<FileResource | null>(null)
  const [deletingItem, setDeletingItem] = useState<FileResource | null>(null)
  const [detailsItem, setDetailsItem] = useState<FileResource | null>(null)
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false)
  const [creatingFolder, setCreatingFolder] = useState(false)
  const [newFolderName, setNewFolderName] = useState("")
  const [busy, setBusy] = useState(false)
  const [contextMenuPosition, setContextMenuPosition] = useState<ContextMenuPosition | null>(null)
  const [transferStatus, setTransferStatus] = useState<string | null>(null)
  const [draggedIds, setDraggedIds] = useState<Set<string> | null>(null)
  const [dropTargetId, setDropTargetId] = useState<string | null>(null)
  const [moving, setMoving] = useState(false)

  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const folderInputRef = useRef<HTMLInputElement | null>(null)

  function sortItems(unsorted: FileResource[]): FileResource[] {
    return [...unsorted].sort((a, b) => {
      const aIsFolder = isFolderResource(a.mimeType)
      const bIsFolder = isFolderResource(b.mimeType)
      if (aIsFolder !== bIsFolder) return aIsFolder ? -1 : 1
      return a.name.localeCompare(b.name)
    })
  }

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await filesApi.list({
        sharedDriveIdOrUrl,
        folderId: currentFolderId,
        pageSize: PAGE_SIZE,
        includeFolders: true,
      })
      setItems(sortItems(response.files))
      setNextPageToken(response.nextPageToken)
      setSelected(new Set())
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load this folder.")
    } finally {
      setLoading(false)
    }
  }, [sharedDriveIdOrUrl, currentFolderId])

  useEffect(() => {
    refresh()
  }, [refresh])

  const loadMore = useCallback(async () => {
    if (!nextPageToken || loadingMore) return
    setLoadingMore(true)
    try {
      const response = await filesApi.list({
        sharedDriveIdOrUrl,
        folderId: currentFolderId,
        pageSize: PAGE_SIZE,
        pageToken: nextPageToken,
        includeFolders: true,
      })
      setItems((current) => sortItems([...current, ...response.files]))
      setNextPageToken(response.nextPageToken)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load more items.")
    } finally {
      setLoadingMore(false)
    }
  }, [sharedDriveIdOrUrl, currentFolderId, nextPageToken, loadingMore])

  const sentinelRef = useIntersectionLoadMore(loadMore, Boolean(nextPageToken) && !loading)

  function buildBrowseUrl(nextBreadcrumbs: BreadcrumbEntry[]): string {
    const segments = nextBreadcrumbs.slice(1).map((entry) => encodePathSegment(entry))
    return `/drives/${sharedDriveIdOrUrl}/browse${segments.length ? "/" + segments.join("/") : ""}`
  }

  function openFolder(folder: FileResource) {
    navigate(buildBrowseUrl([...breadcrumbs, { id: folder.id, name: folder.name }]))
  }

  function goToBreadcrumb(index: number) {
    navigate(buildBrowseUrl(breadcrumbs.slice(0, index + 1)))
  }

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

  async function handleCreateFolder() {
    if (!newFolderName.trim()) return
    setBusy(true)
    setError(null)
    try {
      await foldersApi.create({
        sharedDriveIdOrUrl,
        name: newFolderName.trim(),
        parentFolderId: currentFolderId,
      })
      setNewFolderName("")
      setCreatingFolder(false)
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create folder.")
    } finally {
      setBusy(false)
    }
  }

  async function handleSaveEdit(values: { name?: string; newParentFolderId?: string; description?: string; starred?: boolean }) {
    if (!editingItem) return
    const isFolder = isFolderResource(editingItem.mimeType)
    if (isFolder) {
      await foldersApi.update(editingItem.id, { sharedDriveIdOrUrl, ...values })
    } else {
      await filesApi.update(editingItem.id, { sharedDriveIdOrUrl, ...values })
    }
    setEditingItem(null)
    refresh()
  }

  async function handleConfirmDelete() {
    if (!deletingItem) return
    setBusy(true)
    try {
      const isFolder = isFolderResource(deletingItem.mimeType)
      if (isFolder) {
        await foldersApi.remove(deletingItem.id, sharedDriveIdOrUrl, false)
      } else {
        await filesApi.remove(deletingItem.id, sharedDriveIdOrUrl, false)
      }
      setDeletingItem(null)
      setDetailsItem((current) => (current?.id === deletingItem.id ? null : current))
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to delete item.")
    } finally {
      setBusy(false)
    }
  }

  async function handleConfirmBulkDelete() {
    setBusy(true)
    try {
      const selectedIds = Array.from(selected)
      const selectedItems = items.filter((item) => selectedIds.includes(item.id))
      const fileIds = selectedItems.filter((item) => !isFolderResource(item.mimeType)).map((item) => item.id)
      const folderIds = selectedItems.filter((item) => isFolderResource(item.mimeType)).map((item) => item.id)

      if (fileIds.length > 0) {
        await filesApi.removeBatch({ sharedDriveIdOrUrl, fileIds, permanent: false })
      }
      for (const folderId of folderIds) {
        await foldersApi.remove(folderId, sharedDriveIdOrUrl, false)
      }
      setBulkDeleteOpen(false)
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to delete selected items.")
    } finally {
      setBusy(false)
    }
  }

  function handleContextMenu(event: React.MouseEvent) {
    event.preventDefault()
    setContextMenuPosition({ x: event.clientX, y: event.clientY })
  }

  async function moveItems(itemIds: string[], destinationFolderId: string | undefined) {
    const movable = items.filter((item) => itemIds.includes(item.id) && item.id !== destinationFolderId)
    if (movable.length === 0) return
    setMoving(true)
    setError(null)
    try {
      await Promise.all(
        movable.map((item) =>
          isFolderResource(item.mimeType)
            ? foldersApi.update(item.id, { sharedDriveIdOrUrl, newParentFolderId: destinationFolderId ?? null })
            : filesApi.update(item.id, { sharedDriveIdOrUrl, newParentFolderId: destinationFolderId ?? null }),
        ),
      )
      setSelected(new Set())
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to move item(s).")
    } finally {
      setMoving(false)
    }
  }

  function handleRowDragStart(event: React.DragEvent, item: FileResource) {
    const idsToMove = selected.has(item.id) && selected.size > 1 ? Array.from(selected) : [item.id]
    setDraggedIds(new Set(idsToMove))
    event.dataTransfer.effectAllowed = "move"
    event.dataTransfer.setData("text/plain", idsToMove.join(","))
  }

  function handleRowDragEnd() {
    setDraggedIds(null)
    setDropTargetId(null)
  }

  function handleFolderRowDragOver(event: React.DragEvent, folder: FileResource) {
    if (!draggedIds || draggedIds.has(folder.id)) return
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
    if (dropTargetId !== folder.id) setDropTargetId(folder.id)
  }

  function handleFolderRowDragLeave(folder: FileResource) {
    setDropTargetId((current) => (current === folder.id ? null : current))
  }

  async function handleFolderRowDrop(event: React.DragEvent, folder: FileResource) {
    event.preventDefault()
    const idsToMove = draggedIds ? Array.from(draggedIds) : []
    setDraggedIds(null)
    setDropTargetId(null)
    if (idsToMove.length === 0 || idsToMove.includes(folder.id)) return
    await moveItems(idsToMove, folder.id)
  }

  function handleBreadcrumbDragOver(event: React.DragEvent, breadcrumbFolderId: string | undefined) {
    if (!draggedIds) return
    if (breadcrumbFolderId === currentFolderId) return
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
    if (dropTargetId !== (breadcrumbFolderId ?? "root")) setDropTargetId(breadcrumbFolderId ?? "root")
  }

  function handleBreadcrumbDragLeave(breadcrumbFolderId: string | undefined) {
    const key = breadcrumbFolderId ?? "root"
    setDropTargetId((current) => (current === key ? null : current))
  }

  async function handleBreadcrumbDrop(event: React.DragEvent, breadcrumbFolderId: string | undefined) {
    event.preventDefault()
    const idsToMove = draggedIds ? Array.from(draggedIds) : []
    setDraggedIds(null)
    setDropTargetId(null)
    if (idsToMove.length === 0 || breadcrumbFolderId === currentFolderId) return
    await moveItems(idsToMove, breadcrumbFolderId)
  }

  async function handleRealFileSelected(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return
    const files = Array.from(fileList)
    setError(null)
    setTransferStatus(`Uploading ${files.length} file${files.length === 1 ? "" : "s"}…`)
    let successCount = 0
    for (const file of files) {
      try {
        await filesApi.uploadReal(file, sharedDriveIdOrUrl, currentFolderId)
        successCount += 1
        setTransferStatus(`Uploaded ${successCount}/${files.length} file${files.length === 1 ? "" : "s"}…`)
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : `Failed to upload ${file.name}.`)
      }
    }
    setTransferStatus(null)
    refresh()
  }

  async function handleRealFolderSelected(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return
    const files = Array.from(fileList) as WebkitFile[]
    setError(null)
    setTransferStatus(`Uploading folder (${files.length} file${files.length === 1 ? "" : "s"})…`)
    try {
      const filesWithPaths = files.map((file) => ({ file, relativePath: file.webkitRelativePath || file.name }))
      const result = await foldersApi.uploadBatch(filesWithPaths, sharedDriveIdOrUrl, currentFolderId)
      const failedCount = result.results.filter((r) => !r.success).length
      if (failedCount > 0) {
        setError(`${failedCount} of ${files.length} files failed to upload.`)
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to upload folder.")
    } finally {
      setTransferStatus(null)
      refresh()
    }
  }

  async function handleCreateNative(appType: NativeAppType) {
    setError(null)
    try {
      await filesApi.createNative({
        sharedDriveIdOrUrl,
        appType,
        folderId: currentFolderId,
      })
      refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : `Failed to create ${appType}.`)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Browse</h1>
          <p className="page-subtitle">
            Files and folders in this Shared Drive, just like Google Drive. Right-click to upload or create.
          </p>
        </div>
      </div>

      {error && <div className="banner banner-error">{error}</div>}
      {transferStatus && (
        <div className="banner banner-info">
          <Spinner size={14} />
          {transferStatus}
        </div>
      )}
      {moving && (
        <div className="banner banner-info">
          <Spinner size={14} />
          Moving…
        </div>
      )}

      <div className="breadcrumbs">
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1
          const isDropTarget = draggedIds && dropTargetId === (crumb.id ?? "root") && !isLast
          return (
            <span key={crumb.id ?? "root"} style={{ display: "flex", alignItems: "center", gap: 4 }}>
              {index > 0 && <span className="breadcrumb-sep">/</span>}
              {isLast ? (
                <span className="breadcrumb-current" style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {index === 0 && <HardDriveIcon width={13} height={13} />}
                  {crumb.name}
                </span>
              ) : (
                <button
                  className="breadcrumb-link"
                  onClick={() => goToBreadcrumb(index)}
                  onDragOver={(event) => handleBreadcrumbDragOver(event, crumb.id)}
                  onDragLeave={() => handleBreadcrumbDragLeave(crumb.id)}
                  onDrop={(event) => handleBreadcrumbDrop(event, crumb.id)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    outline: isDropTarget ? "2px solid var(--color-accent)" : undefined,
                    outlineOffset: isDropTarget ? -2 : undefined,
                    background: isDropTarget ? "var(--color-accent-soft)" : undefined,
                  }}
                >
                  {index === 0 && <HardDriveIcon width={13} height={13} />}
                  {crumb.name}
                </button>
              )}
            </span>
          )
        })}
      </div>

      <div className="toolbar">
        <div className="toolbar-left">
          <button className="btn btn-secondary btn-sm" onClick={() => refresh()}>
            <RefreshIcon width={14} height={14} />
            Refresh
          </button>
          <span style={{ fontSize: 12, color: "var(--color-text-faint)" }}>
            Right-click anywhere below to upload, create a folder, or create a Google file
          </span>
        </div>
        <div className="toolbar-right">
          {selected.size > 0 && (
            <button className="btn btn-danger btn-sm" onClick={() => setBulkDeleteOpen(true)}>
              <TrashIcon width={14} height={14} />
              Delete {selected.size} selected
            </button>
          )}
        </div>
      </div>

      <div className="card" onContextMenu={handleContextMenu}>
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
                <th>Modified</th>
                <th>Items</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7}>
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
                  const isDropTarget = folder && dropTargetId === item.id
                  const isBeingDragged = draggedIds?.has(item.id) ?? false
                  return (
                    <tr
                      key={item.id}
                      draggable
                      onDragStart={(event) => handleRowDragStart(event, item)}
                      onDragEnd={handleRowDragEnd}
                      onDragOver={folder ? (event) => handleFolderRowDragOver(event, item) : undefined}
                      onDragLeave={folder ? () => handleFolderRowDragLeave(item) : undefined}
                      onDrop={folder ? (event) => handleFolderRowDrop(event, item) : undefined}
                      style={{
                        cursor: "pointer",
                        opacity: isBeingDragged ? 0.45 : 1,
                        outline: isDropTarget ? "2px solid var(--color-accent)" : undefined,
                        outlineOffset: isDropTarget ? -2 : undefined,
                        background: isDropTarget ? "var(--color-accent-soft)" : undefined,
                      }}
                      onClick={() => (folder ? openFolder(item) : setDetailsItem(item))}
                    >
                      <td onClick={(event) => event.stopPropagation()}>
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
                          {item.starred && <StarIcon width={13} height={13} color="var(--color-warning)" />}
                        </div>
                      </td>
                      <td>
                        <TypeBadge item={item} />
                      </td>
                      <td className="cell-muted">
                        {folder ? (
                          <FolderSizeCell folderId={item.id} sharedDriveIdOrUrl={sharedDriveIdOrUrl} />
                        ) : (
                          formatBytes(item.size)
                        )}
                      </td>
                      <td className="cell-muted">{formatDate(item.modifiedTime)}</td>
                      <td className="cell-muted">
                        {folder && <FolderItemCountCell folderId={item.id} sharedDriveIdOrUrl={sharedDriveIdOrUrl} />}
                      </td>
                      <td onClick={(event) => event.stopPropagation()}>
                        <div className="cell-actions">
                          <a
                            className="btn btn-secondary btn-icon"
                            href={folder ? foldersApi.downloadUrl(item.id, sharedDriveIdOrUrl) : filesApi.downloadUrl(item.id, sharedDriveIdOrUrl)}
                            title={folder ? "Download as zip" : "Download"}
                          >
                            <DownloadIcon width={14} height={14} />
                          </a>
                          <button className="btn btn-secondary btn-icon" title="Edit" onClick={() => setEditingItem(item)}>
                            <EditIcon width={14} height={14} />
                          </button>
                          <button className="btn btn-danger btn-icon" title="Delete" onClick={() => setDeletingItem(item)}>
                            <TrashIcon width={14} height={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              {!loading && items.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">
                      <div className="empty-state-icon">
                        <FolderIcon width={20} height={20} />
                      </div>
                      <div className="empty-state-title">This folder is empty</div>
                      <div className="empty-state-body">Right-click to upload files or create a subfolder.</div>
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
          {items.length.toLocaleString()} item{items.length === 1 ? "" : "s"} loaded
          {!nextPageToken && " · all items loaded"}
        </div>
      )}

      {contextMenuPosition && (
        <ContextMenu
          position={contextMenuPosition}
          onClose={() => setContextMenuPosition(null)}
          onNewFolder={() => setCreatingFolder(true)}
          onFileUpload={() => fileInputRef.current?.click()}
          onFolderUpload={() => folderInputRef.current?.click()}
          onCreateNative={handleCreateNative}
        />
      )}

      <input
        ref={fileInputRef}
        type="file"
        multiple
        style={{ display: "none" }}
        onChange={(event) => {
          handleRealFileSelected(event.target.files)
          event.target.value = ""
        }}
      />
      <input
        ref={folderInputRef}
        type="file"
        // @ts-expect-error non-standard attributes for directory selection, no React typing exists
        webkitdirectory=""
        directory=""
        multiple
        style={{ display: "none" }}
        onChange={(event) => {
          handleRealFolderSelected(event.target.files)
          event.target.value = ""
        }}
      />

      {creatingFolder && (
        <div className="modal-overlay" onClick={() => setCreatingFolder(false)}>
          <div className="card modal-panel" style={{ width: 380, maxWidth: "90vw" }} onClick={(event) => event.stopPropagation()}>
            <div className="card-padded">
              <div className="field-group">
                <label className="field-label">Folder name</label>
                <input
                  className="text-input"
                  autoFocus
                  value={newFolderName}
                  onChange={(event) => setNewFolderName(event.target.value)}
                  onKeyDown={(event) => event.key === "Enter" && handleCreateFolder()}
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
                <button className="btn btn-secondary" onClick={() => setCreatingFolder(false)} disabled={busy}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={handleCreateFolder} disabled={busy || !newFolderName.trim()}>
                  {busy ? "Creating..." : "Create"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {detailsItem && (
        <DetailsPanel
          title={detailsItem.name}
          typeBadge={<TypeBadge item={detailsItem} />}
          onClose={() => setDetailsItem(null)}
          footer={
            <div style={{ display: "flex", gap: 8 }}>
              {!isFolderResource(detailsItem.mimeType) && (
                <a
                  className="btn btn-secondary btn-sm"
                  style={{ flex: 1 }}
                  href={filesApi.downloadUrl(detailsItem.id, sharedDriveIdOrUrl)}
                >
                  <DownloadIcon width={14} height={14} />
                  Download
                </a>
              )}
              <button className="btn btn-secondary btn-sm" style={{ flex: 1 }} onClick={() => setEditingItem(detailsItem)}>
                <EditIcon width={14} height={14} />
                Edit
              </button>
              <button className="btn btn-danger btn-sm btn-icon" onClick={() => setDeletingItem(detailsItem)}>
                <TrashIcon width={14} height={14} />
              </button>
            </div>
          }
        >
          <DetailRow label="ID" value={<span style={{ fontFamily: "var(--font-mono)", fontSize: 12.5 }}>{detailsItem.id}</span>} />
          <DetailRow label="MIME type" value={<span style={{ fontFamily: "var(--font-mono)", fontSize: 12.5 }}>{detailsItem.mimeType}</span>} />
          {!isFolderResource(detailsItem.mimeType) && <DetailRow label="Size" value={formatBytes(detailsItem.size)} />}
          <DetailRow label="Created" value={formatDate(detailsItem.createdTime)} />
          <DetailRow label="Modified" value={formatDate(detailsItem.modifiedTime)} />
          {detailsItem.description && <DetailRow label="Description" value={detailsItem.description} />}
          {detailsItem.md5Checksum && (
            <DetailRow
              label="MD5 checksum"
              value={<span style={{ fontFamily: "var(--font-mono)", fontSize: 12 }}>{detailsItem.md5Checksum}</span>}
            />
          )}
          {detailsItem.webViewLink && (
            <DetailRow
              label="Web link"
              value={
                <a href={detailsItem.webViewLink} target="_blank" rel="noreferrer" style={{ color: "var(--color-accent)" }}>
                  Open in Google Drive ↗
                </a>
              }
            />
          )}
          <DetailRow label="Starred" value={detailsItem.starred ? "Yes" : "No"} />
        </DetailsPanel>
      )}

      {editingItem && (
        <EditResourceModal
          title={`Edit "${editingItem.name}"`}
          initialName={editingItem.name}
          initialDescription={editingItem.description}
          initialStarred={editingItem.starred}
          onCancel={() => setEditingItem(null)}
          onSave={handleSaveEdit}
        />
      )}

      {deletingItem && (
        <ConfirmDialog
          title={isFolderResource(deletingItem.mimeType) ? "Delete folder" : "Delete file"}
          message={
            isFolderResource(deletingItem.mimeType)
              ? `Move "${deletingItem.name}" to trash? Contents may become inaccessible.`
              : `Move "${deletingItem.name}" to trash?`
          }
          confirmLabel="Delete"
          busy={busy}
          onCancel={() => setDeletingItem(null)}
          onConfirm={handleConfirmDelete}
        />
      )}

      {bulkDeleteOpen && (
        <ConfirmDialog
          title="Delete selected items"
          message={`Move ${selected.size} item${selected.size === 1 ? "" : "s"} to trash?`}
          confirmLabel="Delete"
          busy={busy}
          onCancel={() => setBulkDeleteOpen(false)}
          onConfirm={handleConfirmBulkDelete}
        />
      )}
    </>
  )
}
