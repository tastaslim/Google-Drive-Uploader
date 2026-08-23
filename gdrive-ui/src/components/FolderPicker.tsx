import { useEffect, useRef, useState } from "react"
import { ApiError, foldersApi } from "../api/client"
import type { FolderSearchResultItem } from "../api/types"
import { Spinner } from "./Spinner"
import { FolderIcon, PlusIcon } from "./icons"

interface FolderPickerProps {
  sharedDriveIdOrUrl: string
  value: { id: string; name: string } | null
  onChange: (folder: { id: string; name: string } | null) => void
}

const SEARCH_DEBOUNCE_MS = 300
const PAGE_SIZE = 5

/**
 * Searches folders drive-wide by name substring (not an exact-match lookup)
 * and lets the user pick one, or create a brand new folder at the Shared
 * Drive root which is then selected automatically.
 */
export function FolderPicker({ sharedDriveIdOrUrl, value, onChange }: FolderPickerProps) {
  const [query, setQuery] = useState("")
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState<FolderSearchResultItem[]>([])
  const [nextPageToken, setNextPageToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (!query.trim()) {
      setResults([])
      setNextPageToken(null)
      setLoading(false)
      return
    }
    setLoading(true)
    debounceRef.current = setTimeout(async () => {
      try {
        const response = await foldersApi.search({ sharedDriveIdOrUrl, query: query.trim(), pageSize: PAGE_SIZE })
        setResults(response.folders)
        setNextPageToken(response.nextPageToken ?? null)
        setError(null)
      } catch (err) {
        setError(err instanceof ApiError ? err.detail : "Folder search failed.")
      } finally {
        setLoading(false)
      }
    }, SEARCH_DEBOUNCE_MS)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query, sharedDriveIdOrUrl])

  async function loadMore() {
    if (!nextPageToken || loadingMore) return
    setLoadingMore(true)
    try {
      const response = await foldersApi.search({
        sharedDriveIdOrUrl,
        query: query.trim(),
        pageSize: PAGE_SIZE,
        pageToken: nextPageToken,
      })
      setResults((current) => [...current, ...response.folders])
      setNextPageToken(response.nextPageToken ?? null)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to load more folders.")
    } finally {
      setLoadingMore(false)
    }
  }

  function selectFolder(folder: { id: string; name: string }) {
    onChange({ id: folder.id, name: folder.name })
    setQuery("")
    setResults([])
    setOpen(false)
  }

  function clearSelection() {
    onChange(null)
    setQuery("")
  }

  async function handleCreateFolder() {
    const name = query.trim()
    if (!name) return
    setCreating(true)
    setError(null)
    try {
      const created = await foldersApi.create({ sharedDriveIdOrUrl, name })
      selectFolder(created)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Failed to create folder.")
    } finally {
      setCreating(false)
    }
  }

  const exactNameMatch = results.some((r) => r.name.toLowerCase() === query.trim().toLowerCase())

  return (
    <div ref={containerRef} style={{ position: "relative" }}>
      {value ? (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 10px",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
            background: "var(--color-bg-subtle)",
          }}
        >
          <FolderIcon width={15} height={15} color="var(--color-accent)" />
          <span style={{ flex: 1, fontSize: 13.5, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {value.name}
          </span>
          <button type="button" className="btn btn-secondary btn-sm" onClick={clearSelection}>
            Change
          </button>
        </div>
      ) : (
        <>
          <input
            className="text-input"
            placeholder="Search folder by name, or type a new name to create one…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setOpen(true)
            }}
            onFocus={() => setOpen(true)}
          />
          {open && query.trim() && (
            <div
              className="card"
              style={{
                position: "absolute",
                top: "calc(100% + 4px)",
                left: 0,
                right: 0,
                zIndex: 20,
                maxHeight: 260,
                overflowY: "auto",
                boxShadow: "var(--shadow-md)",
              }}
            >
              {loading && (
                <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 12 }}>
                  <Spinner size={13} />
                  <span className="field-hint">Searching…</span>
                </div>
              )}
              {!loading &&
                results.map((folder) => (
                  <button
                    key={folder.id}
                    type="button"
                    onClick={() => selectFolder(folder)}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 8,
                      width: "100%",
                      padding: "9px 12px",
                      border: "none",
                      borderBottom: "1px solid var(--color-border)",
                      background: "transparent",
                      textAlign: "left",
                      cursor: "pointer",
                      font: "inherit",
                    }}
                    onMouseEnter={(event) => (event.currentTarget.style.background = "var(--color-bg-subtle)")}
                    onMouseLeave={(event) => (event.currentTarget.style.background = "transparent")}
                  >
                    <FolderIcon width={14} height={14} color="var(--color-accent)" style={{ marginTop: 2, flexShrink: 0 }} />
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {folder.name}
                      </div>
                      <div
                        title={folder.path}
                        style={{
                          fontSize: 11.5,
                          color: "var(--color-text-faint)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          marginTop: 1,
                        }}
                      >
                        {folder.path}
                      </div>
                    </span>
                  </button>
                ))}
              {!loading && results.length === 0 && (
                <div style={{ padding: 12, fontSize: 12.5, color: "var(--color-text-faint)" }}>
                  No matching folders.
                </div>
              )}
              {!loading && nextPageToken && (
                <button
                  type="button"
                  onClick={loadMore}
                  disabled={loadingMore}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 8,
                    width: "100%",
                    padding: "9px 12px",
                    border: "none",
                    borderBottom: "1px solid var(--color-border)",
                    background: "transparent",
                    cursor: "pointer",
                    font: "inherit",
                    fontSize: 12.5,
                    fontWeight: 600,
                    color: "var(--color-text-muted)",
                  }}
                >
                  {loadingMore ? <Spinner size={12} /> : null}
                  {loadingMore ? "Loading…" : "Load more folders"}
                </button>
              )}
              {!loading && !exactNameMatch && (
                <button
                  type="button"
                  onClick={handleCreateFolder}
                  disabled={creating}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    width: "100%",
                    padding: "10px 12px",
                    border: "none",
                    background: "transparent",
                    textAlign: "left",
                    cursor: "pointer",
                    font: "inherit",
                    color: "var(--color-accent)",
                    fontWeight: 600,
                  }}
                >
                  {creating ? <Spinner size={13} /> : <PlusIcon width={14} height={14} />}
                  {creating ? "Creating…" : `Create new folder "${query.trim()}"`}
                </button>
              )}
            </div>
          )}
        </>
      )}
      {error && <div style={{ marginTop: 6, fontSize: 12, color: "var(--color-danger)" }}>{error}</div>}
    </div>
  )
}
