/**
 * Provide a smooth scroller to an on-page marketing section, accounting for the sticky header.
 * @returns A function scrolling to a selector, or navigating to the landing with the hash when the section is missing.
 */
export function useScrollToSection(): (selector: string) => void {
  const localePath: ReturnType<typeof useLocalePath> = useLocalePath()

  /**
   * Smooth-scroll to a section, or navigate to the landing carrying the hash when it is not on the current page.
   * @param selector - CSS selector of the target section.
   */
  function scrollToSection(selector: string): void {
    const element: Element | null = document.querySelector(selector)
    if (!element) {
      navigateTo(`${localePath('/')}${selector}`)
      return
    }
    const headerOffset: number = 80
    const elementPosition: number = element.getBoundingClientRect().top
    const offsetPosition: number = elementPosition + window.pageYOffset - headerOffset
    window.scrollTo({ top: offsetPosition, behavior: 'smooth' })
  }

  return scrollToSection
}
