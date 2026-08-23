import { useEffect, useState } from "react"
import { drivesApi } from "../api/client"

const driveNameCache = new Map<string, string>()

/** Resolves a Shared Drive ID to its display name, caching results for the session. */
export function useDriveName(driveId: string): string | null {
  const [name, setName] = useState<string | null>(driveNameCache.get(driveId) ?? null)

  useEffect(() => {
    if (driveNameCache.has(driveId)) {
      setName(driveNameCache.get(driveId)!)
      return
    }
    let cancelled = false
    drivesApi
      .list({ pageSize: 100 })
      .then((response) => {
        if (cancelled) return
        for (const drive of response.drives) {
          driveNameCache.set(drive.id, drive.name)
        }
        setName(driveNameCache.get(driveId) ?? null)
      })
      .catch(() => {
        if (!cancelled) setName(null)
      })
    return () => {
      cancelled = true
    }
  }, [driveId])

  return name
}
