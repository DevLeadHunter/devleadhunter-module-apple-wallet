import { onMounted, onBeforeUnmount } from 'vue'

/**
 * Fire a `site_section_view` event the first time each `section[id]` of the page scrolls into view.
 * @param properties - Extra event properties merged into each section event.
 */
export function useSectionViewTracking(properties: Record<string, unknown> = {}): void {
  const { track }: { track: (event: string, properties?: Record<string, unknown> | undefined) => void } =
    useSiteTracking()

  /** Observer armed on mount, disconnected on unmount. */
  let observer: IntersectionObserver | null = null

  onMounted((): void => {
    if (typeof IntersectionObserver === 'undefined') return
    const seen: Set<string> = new Set<string>()
    observer = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]): void => {
        for (const entry of entries) {
          const id: string = (entry.target as HTMLElement).id
          if (entry.isIntersecting && id && !seen.has(id)) {
            seen.add(id)
            track('site_section_view', { section: id, ...properties })
            observer?.unobserve(entry.target)
          }
        }
      },
      { threshold: 0.5 },
    )
    document.querySelectorAll('section[id]').forEach((element: Element): void => {
      observer?.observe(element)
    })
  })

  onBeforeUnmount((): void => {
    observer?.disconnect()
    observer = null
  })
}
