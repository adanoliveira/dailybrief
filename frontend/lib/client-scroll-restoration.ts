/**
 * Client-side scroll restoration for Next.js navigation
 * This handles scroll restoration when navigating between pages via Next.js router
 */

/**
 * Parse current URL to determine feed type and topic
 */
function getCurrentFeedInfo(): { feedType: string; topicSlug: string } | null {
  if (typeof window === 'undefined') return null
  
  const path = window.location.pathname
  
  if (path.includes('/home')) {
    return { feedType: 'personalized', topicSlug: 'for-you' }
  }
  
  if (path.includes('/world') || path.includes('/headlines')) {
    return { feedType: 'world', topicSlug: 'all' }
  }
  
  return null
}

/**
 * Restore scroll position immediately (client-side version of inline script)
 */
export function restoreScrollOnNavigation(): boolean {
  try {
    const feedInfo = getCurrentFeedInfo()
    if (!feedInfo) return false
    
    const cacheKey = `${feedInfo.feedType}:${feedInfo.topicSlug}::relevance`
    const savedPosition = sessionStorage.getItem(`scroll-${cacheKey}`)
    
    if (savedPosition) {
      const position = parseInt(savedPosition, 10)
      
      // Restore immediately
      window.scrollTo(0, position)
      
      // Mark as restored to prevent React from doing it again
      sessionStorage.setItem(`scroll-restored-${cacheKey}`, 'true')
      ;(window as any).__scrollRestored = cacheKey
      
      return true
    }
    
    return false
  } catch (error) {
    console.warn('Client-side scroll restoration failed:', error)
    return false
  }
}

/**
 * Clean up old sessionStorage keys (legacy format)
 */
export function cleanupOldScrollKeys(): void {
  try {
    const oldKeys = [
      'scroll-personalized:relevance',
      'scroll-world:relevance',
      'scroll-restored-personalized:relevance',
      'scroll-restored-world:relevance'
    ]
    
    oldKeys.forEach(key => {
      if (sessionStorage.getItem(key)) {
        sessionStorage.removeItem(key)
      }
    })
  } catch (error) {
    console.warn('Failed to cleanup old scroll keys:', error)
  }
}

/**
 * Initialize client-side scroll restoration
 * Call this when the component mounts
 */
export function initClientScrollRestoration(): void {
  // Clean up old keys first
  cleanupOldScrollKeys()
  
  // Try to restore scroll position
  restoreScrollOnNavigation()
} 