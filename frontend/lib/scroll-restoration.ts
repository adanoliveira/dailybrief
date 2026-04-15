/**
 * Immediate scroll position restoration
 * This runs BEFORE React renders to prevent scroll flash
 */

interface FeedRoute {
  feedType: 'personalized' | 'world'
  topicSlug?: string
}

/**
 * Parse the current URL to determine feed type and topic
 */
function parseFeedFromURL(): FeedRoute | null {
  if (typeof window === 'undefined') return null
  
  const path = window.location.pathname
  
  // Parse feed routes
  if (path.includes('/home')) {
    return { feedType: 'personalized' }
  }
  
  if (path.includes('/world')) {
    return { feedType: 'world' }
  }
  
  if (path.includes('/headlines')) {
    return { feedType: 'world' }
  }
  
  // Could extend for topic-specific routes
  // e.g., /world/technology, /home/business, etc.
  
  return null
}

/**
 * Generate the same cache key format as HookStateCache
 */
function generateScrollCacheKey(feedType: string, topicSlug?: string): string {
  const parts = [feedType]
  if (topicSlug && topicSlug !== 'for-you' && topicSlug !== 'all') {
    parts.push(topicSlug)
  }
  parts.push('relevance') // Default sort order
  return parts.join(':')
}

/**
 * Immediately restore scroll position from sessionStorage
 * Call this as early as possible in page load
 */
export function restoreScrollImmediately(): void {
  try {
    const feed = parseFeedFromURL()
    if (!feed) return
    
    const cacheKey = generateScrollCacheKey(feed.feedType, feed.topicSlug)
    const savedPosition = sessionStorage.getItem(`scroll-${cacheKey}`)
    
    if (savedPosition) {
      const position = parseInt(savedPosition, 10)
      console.log(`🔄 Immediate scroll restoration: ${position}px for ${cacheKey}`)
      
      // Restore immediately - no animation to prevent flash
      window.scrollTo(0, position)
      
      // Mark as restored to prevent React from doing it again
      sessionStorage.setItem(`scroll-restored-${cacheKey}`, 'true')
    }
  } catch (error) {
    console.warn('Failed to restore scroll immediately:', error)
  }
}

/**
 * Check if scroll position was already restored immediately
 */
export function wasScrollRestoredImmediately(feedType: string, topicSlug?: string): boolean {
  try {
    const cacheKey = generateScrollCacheKey(feedType, topicSlug)
    return sessionStorage.getItem(`scroll-restored-${cacheKey}`) === 'true'
  } catch (error) {
    return false
  }
}

/**
 * Clear the restoration flag (call when feed changes)
 */
export function clearScrollRestorationFlag(feedType: string, topicSlug?: string): void {
  try {
    const cacheKey = generateScrollCacheKey(feedType, topicSlug)
    sessionStorage.removeItem(`scroll-restored-${cacheKey}`)
  } catch (error) {
    // Ignore errors
  }
}

/**
 * Save current scroll position to sessionStorage immediately
 * Use this when navigating away from feed pages
 */
export function saveScrollImmediately(): void {
  try {
    const feed = parseFeedFromURL()
    if (!feed) return
    
    const cacheKey = generateScrollCacheKey(feed.feedType, feed.topicSlug)
    const currentPosition = window.pageYOffset || document.documentElement.scrollTop
    
    if (currentPosition > 0) {
      sessionStorage.setItem(`scroll-${cacheKey}`, currentPosition.toString())
      console.log(`💾 Immediate scroll save: ${currentPosition}px for ${cacheKey}`)
    }
  } catch (error) {
    console.warn('Failed to save scroll immediately:', error)
  }
} 