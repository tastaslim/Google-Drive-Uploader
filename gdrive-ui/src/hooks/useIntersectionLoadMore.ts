import { useEffect, useRef } from "react"

/** Calls onIntersect whenever the returned sentinel element scrolls into view,
 * as long as `enabled` is true (e.g. there's a next page and nothing is loading). */
export function useIntersectionLoadMore(onIntersect: () => void, enabled: boolean) {
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const node = sentinelRef.current
    if (!node || !enabled) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          onIntersect()
        }
      },
      { rootMargin: "200px" },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [onIntersect, enabled])

  return sentinelRef
}
