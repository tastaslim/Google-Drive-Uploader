import { useEffect, useState } from "react"
import { ApiError, foldersApi } from "../api/client"
import type { FolderStatsResponse } from "../api/types"

const statsCache = new Map<string, FolderStatsResponse>()
const inFlight = new Map<string, Promise<FolderStatsResponse>>()

export interface FolderStatsState {
  stats: FolderStatsResponse | null
  loading: boolean
  error: string | null
}

/**
 * Lazily computes a folder's recursive file/subfolder count and total size
 * (Drive doesn't track this natively — the backend walks the tree on
 * request). Cached for the session so revisiting a folder is instant;
 * concurrent requests for the same folder share one in-flight call so
 * scrolling a long listing doesn't fire duplicate recursive walks.
 */
export function useFolderStats(folderId: string, sharedDriveIdOrUrl: string, enabled: boolean): FolderStatsState {
  const cached = statsCache.get(folderId) ?? null
  const [stats, setStats] = useState<FolderStatsResponse | null>(cached)
  const [loading, setLoading] = useState(enabled && !cached)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!enabled) return
    const existing = statsCache.get(folderId)
    if (existing) {
      setStats(existing)
      setLoading(false)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    let request = inFlight.get(folderId)
    if (!request) {
      request = foldersApi.stats(folderId, sharedDriveIdOrUrl)
      inFlight.set(folderId, request)
      request.finally(() => inFlight.delete(folderId))
    }

    request
      .then((response) => {
        statsCache.set(folderId, response)
        if (!cancelled) {
          setStats(response)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Failed to load folder stats.")
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [folderId, sharedDriveIdOrUrl, enabled])

  return { stats, loading, error }
}
