import { useState, useEffect, useCallback, useRef } from 'react'
import { dataManager, LocalArticlePreview, SyncOptions } from './data-manager'
import { UserPreferences, ArticleDetail, PaginatedResponse } from './api'
import { localDB } from './local-database'

// ===============================================
// PERSISTENT STATE CACHE FOR HOOKS
// ===============================================

interface FeedCacheKey {
  feedType: 'personalized' | 'world'
  topicSlug?: string
  searchQuery?: string
  sortOrder?: 'relevance' | 'newest' | 'oldest'
}

interface FeedCacheEntry {
  articles: LocalArticlePreview[]
  hasMore: boolean
  totalItems: number
  lastSyncAt: Date | null
  page: number
  isLoading: boolean
  error: string | null
  timestamp: number
  scrollPosition?: number // Add scroll position tracking
}

interface FeedState {
  articles: LocalArticlePreview[]
  hasMore: boolean
  totalItems: number
  lastSyncAt: Date | null
  page: number
  isLoading: boolean
  error: string | null
}

interface UserPreferencesCacheEntry {
  data: UserPreferences | null
  isLoading: boolean
  error: string | null
  lastSyncAt: Date | null
  timestamp: number
}

interface ArticleDetailCacheEntry {
  data: ArticleDetail | null
  isLoading: boolean
  error: string | null
  timestamp: number
}

class HookStateCache {
  private feedCache = new Map<string, FeedCacheEntry>()
  private userPreferencesCache: UserPreferencesCacheEntry | null = null
  public readonly CACHE_TTL = 15 * 60 * 1000 // 15 minutes (longer than 10min background sync)

  getFeedCacheKey(key: FeedCacheKey): string {
    return `${key.feedType}:${key.topicSlug || 'all'}:${key.searchQuery || ''}:${key.sortOrder || 'relevance'}`
  }

  getFeedCache(key: FeedCacheKey): FeedCacheEntry | null {
    const cacheKey = this.getFeedCacheKey(key)
    const entry = this.feedCache.get(cacheKey)
    
    if (entry && (Date.now() - entry.timestamp) < this.CACHE_TTL) {
      return entry
    }
    
    // Clean up expired entry
    if (entry) {
      this.feedCache.delete(cacheKey)
    }
    
    return null
  }

  setFeedCache(key: FeedCacheKey, entry: Partial<FeedCacheEntry>): void {
    const cacheKey = this.getFeedCacheKey(key)
    const existing = this.feedCache.get(cacheKey)
    
    this.feedCache.set(cacheKey, {
      articles: [],
      hasMore: true,
      totalItems: 0,
      lastSyncAt: null,
      page: 1,
      isLoading: false,
      error: null,
      timestamp: Date.now(),
      ...existing,
      ...entry
    })
  }

  getUserPreferencesCache(): UserPreferencesCacheEntry | null {
    if (this.userPreferencesCache && (Date.now() - this.userPreferencesCache.timestamp) < this.CACHE_TTL) {
      return this.userPreferencesCache
    }
    
    // Clean up expired entry
    if (this.userPreferencesCache) {
      this.userPreferencesCache = null
    }
    
    return null
  }

  setUserPreferencesCache(entry: Partial<UserPreferencesCacheEntry>): void {
    this.userPreferencesCache = {
      data: null,
      isLoading: false,
      error: null,
      lastSyncAt: null,
      timestamp: Date.now(),
      ...this.userPreferencesCache,
      ...entry
    }
  }

  clearFeedCache(key?: FeedCacheKey): void {
    if (key) {
      const cacheKey = this.getFeedCacheKey(key)
      this.feedCache.delete(cacheKey)
    } else {
      this.feedCache.clear()
    }
  }

  clearUserPreferencesCache(): void {
    this.userPreferencesCache = null
  }

  // Article Detail Cache methods
  private articleDetailCache = new Map<string, ArticleDetailCacheEntry>()

  getArticleDetailCache(key: string): ArticleDetailCacheEntry | null {
    const entry = this.articleDetailCache.get(key)
    
    if (entry && (Date.now() - entry.timestamp) < this.CACHE_TTL) {
      return entry
    }
    
    // Clean up expired entry
    if (entry) {
      this.articleDetailCache.delete(key)
    }
    
    return null
  }

  setArticleDetailCache(key: string, entry: Partial<ArticleDetailCacheEntry>): void {
    const existing = this.articleDetailCache.get(key)
    
    this.articleDetailCache.set(key, {
      data: null,
      isLoading: false,
      error: null,
      timestamp: Date.now(),
      ...existing,
      ...entry
    })
  }

  clearArticleDetailCache(key?: string): void {
    if (key) {
      this.articleDetailCache.delete(key)
    } else {
      this.articleDetailCache.clear()
    }
  }

  // Scroll position management
  saveScrollPosition(key: FeedCacheKey, scrollPosition: number): void {
    const cacheKey = this.getFeedCacheKey(key)
    const existing = this.feedCache.get(cacheKey)
    if (existing) {
      this.feedCache.set(cacheKey, {
        ...existing,
        scrollPosition,
        timestamp: Date.now()
      })
    }
  }

  getScrollPosition(key: FeedCacheKey): number | null {
    const cached = this.getFeedCache(key)
    return cached?.scrollPosition ?? null
  }

  // Recently viewed articles tracking
  private recentlyViewedArticles: string[] = []
  private readonly MAX_RECENT_ARTICLES = 20

  trackRecentlyViewedArticle(articleId: string): void {
    // Remove if already exists to move to front
    this.recentlyViewedArticles = this.recentlyViewedArticles.filter(id => id !== articleId)
    
    // Add to front
    this.recentlyViewedArticles.unshift(articleId)
    
    // Keep only MAX_RECENT_ARTICLES
    if (this.recentlyViewedArticles.length > this.MAX_RECENT_ARTICLES) {
      this.recentlyViewedArticles = this.recentlyViewedArticles.slice(0, this.MAX_RECENT_ARTICLES)
    }
  }

  getRecentlyViewedArticles(limit: number = 10): string[] {
    return this.recentlyViewedArticles.slice(0, limit)
  }

  /**
   * Invalidate specific feed cache to trigger UI refresh after background sync
   */
  invalidateFeedCache(feedType: 'personalized' | 'world'): void {
    // Find and remove cache entries for this feed type
    const keysToRemove: string[] = []
    for (const [key] of this.feedCache.entries()) {
      if (key.startsWith(`${feedType}:`)) {
        keysToRemove.push(key)
      }
    }
    
    keysToRemove.forEach(key => {
      console.log(`HookStateCache: Invalidating feed cache for ${key}`)
      this.feedCache.delete(key)
    })
  }

  clearAll(): void {
    this.feedCache.clear()
    this.userPreferencesCache = null
    this.articleDetailCache.clear()
    this.recentlyViewedArticles = []
  }
}

const hookStateCache = new HookStateCache()

// Export for testing/debugging
export { hookStateCache }

// ===============================================
// OFFLINE STATUS HOOK
// ===============================================

export function useOfflineStatus() {
  const [isOnline, setIsOnline] = useState(true)
  const [wasOffline, setWasOffline] = useState(false)

  useEffect(() => {
    if (typeof window === 'undefined') return

    const updateOnlineStatus = () => {
      const online = navigator.onLine
      
      if (!online && isOnline) {
        // Just went offline
        setWasOffline(true)
        console.log('useOfflineStatus: App went offline - using local storage only')
      } else if (online && !isOnline && wasOffline) {
        // Back online after being offline
        console.log('useOfflineStatus: App back online - triggering background refresh')
        dataManager.forceRefreshAll().catch(console.error)
      }
      
      setIsOnline(online)
    }

    // Set initial state
    updateOnlineStatus()

    // Listen for connectivity changes
    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)

    return () => {
      window.removeEventListener('online', updateOnlineStatus)
      window.removeEventListener('offline', updateOnlineStatus)
    }
  }, [isOnline, wasOffline])

  return {
    isOnline,
    wasOffline
  }
}

// ===============================================
// USER PREFERENCES HOOK
// ===============================================

export function useUserPreferences(options: SyncOptions = {}) {
  // Initialize from cache if available (INSTANT LOADING!)
  const initializeFromCache = useCallback(() => {
    const cached = hookStateCache.getUserPreferencesCache()
    return {
      data: cached?.data || null,
      isLoading: !cached, // Only show loading if no cache
      error: cached?.error || null,
      lastSyncAt: cached?.lastSyncAt || null
    }
  }, [])

  const [state, setState] = useState(initializeFromCache)
  
  // Use refs to prevent unnecessary re-renders
  const optionsRef = useRef(options)
  optionsRef.current = options

  // Update cache whenever state changes
  const updateStateAndCache = useCallback((newState: Partial<typeof state>) => {
    setState(prev => {
      const updated = { ...prev, ...newState }
      
      // Update cache for persistence
      hookStateCache.setUserPreferencesCache({
        data: updated.data,
        isLoading: updated.isLoading,
        error: updated.error,
        lastSyncAt: updated.lastSyncAt
      })
      
      return updated
    })
  }, [])

  const loadPreferences = useCallback(async (forceRefresh = false) => {
    try {
      // Only show loading if we don't have cached data
      if (!state.data || forceRefresh) {
        updateStateAndCache({ isLoading: true, error: null })
      }
      
      console.log('useUserPreferences: Loading preferences...')
      
      const preferences = await dataManager.getUserPreferences({
        ...optionsRef.current,
        forceRefresh
      })
      
      updateStateAndCache({
        data: preferences,
        lastSyncAt: new Date(),
        isLoading: false,
        error: null
      })
      
      console.log('useUserPreferences: Loaded successfully')
    } catch (err) {
      console.error('useUserPreferences: Failed to load:', err)
      updateStateAndCache({
        error: err instanceof Error ? err.message : 'Failed to load preferences',
        isLoading: false
      })
    }
  }, [state.data, updateStateAndCache])

  const refresh = useCallback(() => {
    console.log('useUserPreferences: Manual refresh requested')
    return loadPreferences(true)
  }, [loadPreferences])

  // Load on mount only if no cached data
  useEffect(() => {
    const cached = hookStateCache.getUserPreferencesCache()
    
    if (cached) {
      console.log('useUserPreferences: Using cached data')
      // Update state with cached data (instant!)
      setState({
        data: cached.data,
        isLoading: false,
        error: cached.error,
        lastSyncAt: cached.lastSyncAt
      })
      
      // Trigger background refresh if cache is stale
      if (!cached.lastSyncAt || Date.now() - cached.lastSyncAt.getTime() > 5 * 60 * 1000) {
        loadPreferences(false)
      }
    } else {
      console.log('useUserPreferences: No cache, loading fresh')
      loadPreferences(false)
    }
  }, [loadPreferences])

  return {
    data: state.data,
    isLoading: state.isLoading,
    error: state.error,
    lastSyncAt: state.lastSyncAt,
    refresh
  }
}

// ===============================================
// FEED HOOK WITH INFINITE SCROLL
// ===============================================

export function useFeed(
  feedType: 'personalized' | 'world',
  topicSlug?: string,
  searchQuery?: string,
  sortOrder?: 'relevance' | 'newest' | 'oldest',
  options: SyncOptions = {},
  publicMode = false
) {
  const cacheKey: FeedCacheKey = { feedType, topicSlug, searchQuery, sortOrder }
  
  // Initialize state from cache if available (INSTANT LOADING!)
  const initializeFromCache = useCallback((): FeedState => {
    const cached = hookStateCache.getFeedCache(cacheKey)
    return cached ? {
      articles: cached.articles,
      hasMore: cached.hasMore,
      totalItems: cached.totalItems,
      lastSyncAt: cached.lastSyncAt,
      page: cached.page,
      isLoading: cached.isLoading,
      error: cached.error
    } : {
      articles: [],
      hasMore: true,
      totalItems: 0,
      lastSyncAt: null,
      page: 1,
      isLoading: true, // Only true if no cache
      error: null
    }
  }, [cacheKey.feedType, cacheKey.topicSlug, cacheKey.searchQuery, cacheKey.sortOrder])

  const [state, setState] = useState<FeedState>(initializeFromCache)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [pendingArticles, setPendingArticles] = useState({ newArticlesCount: 0, updatedArticlesCount: 0 })
  const [isLoadingPending, setIsLoadingPending] = useState(false)
  
  // Use refs to track current state and prevent unnecessary re-renders
  const currentQuery = useRef({ feedType, topicSlug, searchQuery, sortOrder })
  const isInitialMount = useRef(true)
  const optionsRef = useRef(options)
  optionsRef.current = options

  // Save state to cache whenever it changes
  const updateStateAndCache = useCallback((newState: Partial<FeedState>) => {
    setState(prev => {
      const updated = { ...prev, ...newState }
      
      // Get existing cache to preserve scroll position
      const existingCache = hookStateCache.getFeedCache(cacheKey)
      
      // Update cache for persistence, preserving scroll position
      hookStateCache.setFeedCache(cacheKey, {
        articles: updated.articles,
        hasMore: updated.hasMore,
        totalItems: updated.totalItems,
        lastSyncAt: updated.lastSyncAt,
        page: updated.page,
        isLoading: updated.isLoading,
        error: updated.error,
        scrollPosition: existingCache?.scrollPosition, // Preserve existing scroll position
        timestamp: Date.now()
      })
      
      return updated
    })
  }, [cacheKey])

  const loadFeed = useCallback(async (
    pageNum: number, 
    reset = false,
    forceRefresh = false
  ) => {
    try {
      // Only show main loading for initial loads or resets
      if (reset || state.articles.length === 0) {
        updateStateAndCache({ isLoading: true, error: null })
      } else {
        setIsLoadingMore(true)
      }

      console.log(`useFeed: Loading ${feedType} feed (page ${pageNum}, reset: ${reset}, cached: ${state.articles.length > 0}, public: ${publicMode})`)

      const response = publicMode 
        ? await dataManager.getPublicFeed(topicSlug, pageNum, 10)
        : await dataManager.getFeed(
        feedType,
        topicSlug,
        pageNum,
        10, // page size
        { ...optionsRef.current, forceRefresh }
      )

      if (!response) {
        console.log(`useFeed: No response from DataManager ${publicMode ? '(public API failed)' : '(likely not authenticated)'}`)
        updateStateAndCache({
          articles: [],
          hasMore: false,
          totalItems: 0,
          isLoading: false,
          page: 1
        })
        return
      }

      let newArticles: LocalArticlePreview[]
      let newPage: number

      if (reset || pageNum === 1) {
        // Reset: replace all articles
        newArticles = response.articles
        newPage = 1
      } else {
        // Append: add to existing articles with deduplication
        const existingIds = new Set(state.articles.map(article => article.id))
        const uniqueNewArticles = response.articles.filter(article => !existingIds.has(article.id))
        newArticles = [...state.articles, ...uniqueNewArticles]
        newPage = pageNum
        
        if (uniqueNewArticles.length < response.articles.length) {
          console.log(`useFeed: Filtered out ${response.articles.length - uniqueNewArticles.length} duplicate articles`)
        }
      }

      updateStateAndCache({
        articles: newArticles,
        hasMore: response.pagination.hasNext,
        totalItems: response.pagination.totalItems,
        lastSyncAt: new Date(),
        isLoading: false,
        page: newPage,
        error: null
      })

      console.log(`useFeed: Loaded ${response.articles.length} articles (total in state: ${newArticles.length}, hasMore: ${response.pagination.hasNext})`)

    } catch (err) {
      console.error('useFeed: Failed to load feed:', err)
      updateStateAndCache({
        error: err instanceof Error ? err.message : 'Failed to load feed',
        isLoading: false
      })
    } finally {
      setIsLoadingMore(false)
      isInitialMount.current = false
    }
  }, [feedType, topicSlug, state.articles, updateStateAndCache])

  // Check for query changes and reset if needed
  useEffect(() => {
    const newQuery = { feedType, topicSlug, searchQuery, sortOrder }
    const queryChanged = JSON.stringify(currentQuery.current) !== JSON.stringify(newQuery)
    
    if (queryChanged) {
      console.log(`useFeed: Query changed, checking cache`, newQuery)
      currentQuery.current = newQuery
      
      // Check if we have cached data for this new query
      const cached = hookStateCache.getFeedCache(cacheKey)
      
             if (cached) {
                 // We have cached data - use it immediately (INSTANT!)
        console.log(`useFeed: ⚡ INSTANT - Using cached data for new query (${cached.articles.length} articles, scroll: ${cached.scrollPosition || 0})`)
        setState({
          articles: cached.articles,
          hasMore: cached.hasMore,
          totalItems: cached.totalItems,
          lastSyncAt: cached.lastSyncAt,
          page: cached.page,
          isLoading: cached.isLoading,
          error: cached.error
        })
         
                 // Only trigger background refresh if cache is significantly stale (15+ minutes)
        // Background sync handles regular updates every 10 minutes
        if (!cached.lastSyncAt || Date.now() - cached.lastSyncAt.getTime() > 15 * 60 * 1000) {
          console.log(`useFeed: Cache is stale (${Math.round((Date.now() - (cached.lastSyncAt?.getTime() || 0)) / 60000)} min old), refreshing in background`)
          loadFeed(1, true, false)
        }
       } else {
        // No cached data - load fresh
        console.log(`useFeed: No cache for new query, loading fresh`)
        setState(initializeFromCache())
        loadFeed(1, true, false)
      }
    } else if (isInitialMount.current && state.articles.length === 0) {
      // Initial mount with no cache - load data
      console.log(`useFeed: Initial mount, no cached data`)
      loadFeed(1, true, false)
    } else if (isInitialMount.current) {
      // Initial mount with cache - only refresh if significantly stale
      console.log(`useFeed: Initial mount with cached data (${state.articles.length} articles)`)
      if (!state.lastSyncAt || Date.now() - state.lastSyncAt.getTime() > 15 * 60 * 1000) {
        console.log(`useFeed: Initial cache is stale, refreshing in background`)
        loadFeed(1, true, false)
      } else {
        console.log(`useFeed: Initial cache is fresh, using without refresh`)
      }
    }
    
    isInitialMount.current = false
  }, [feedType, topicSlug, searchQuery, sortOrder, cacheKey, loadFeed, initializeFromCache, state.articles.length, state.lastSyncAt])

  // Load more pages
  const loadMore = useCallback(() => {
    if (!isLoadingMore && state.hasMore && !state.isLoading) {
      const nextPage = state.page + 1
      console.log(`useFeed: Loading page ${nextPage}`)
      loadFeed(nextPage, false, false)
    }
  }, [state.page, state.hasMore, isLoadingMore, state.isLoading, loadFeed])

  // Manual refresh (force refresh from backend)
  const refresh = useCallback(() => {
    console.log('useFeed: Manual refresh requested')
    return loadFeed(1, true, true) // Reset and force refresh
  }, [loadFeed])

  // Background refresh (non-blocking)
  const backgroundRefresh = useCallback(() => {
    if (!state.isLoading && !isLoadingMore) {
      console.log('useFeed: Background refresh triggered')
      
      // Use backgroundSync option for non-blocking refresh
      dataManager.getFeed(
        feedType,
        topicSlug,
        1,
        10,
        { ...optionsRef.current, backgroundSync: true }
      ).then(response => {
        if (response && state.page === 1) {
          // Update first page silently if we're viewing it
          updateStateAndCache({
            articles: response.articles,
            hasMore: response.pagination.hasNext,
            totalItems: response.pagination.totalItems,
            lastSyncAt: new Date()
          })
        }
      }).catch(console.error)
    }
  }, [feedType, topicSlug, state.page, state.isLoading, isLoadingMore, updateStateAndCache])

  // Scroll position management
  const saveScrollPosition = useCallback((scrollPosition: number) => {
    hookStateCache.saveScrollPosition(cacheKey, scrollPosition)
    
    // Also save to sessionStorage for immediate restoration (matching cache key format)
    try {
      const normalizedTopicSlug = cacheKey.topicSlug === 'for-you' || cacheKey.topicSlug === 'all' ? cacheKey.topicSlug : ''
      const sessionCacheKey = `${cacheKey.feedType}:${normalizedTopicSlug}::relevance`
      const sessionStorageKey = `scroll-${sessionCacheKey}`
      
      sessionStorage.setItem(sessionStorageKey, scrollPosition.toString())
    } catch (error) {
      // Silently ignore sessionStorage errors
    }
  }, [cacheKey.feedType, cacheKey.topicSlug, cacheKey.searchQuery, cacheKey.sortOrder])

  const getScrollPosition = useCallback((): number | null => {
    const cached = hookStateCache.getScrollPosition(cacheKey)
    if (cached) return cached
    
    // Fallback to sessionStorage (matching cache key format)
    try {
      const normalizedTopicSlug = cacheKey.topicSlug === 'for-you' || cacheKey.topicSlug === 'all' ? cacheKey.topicSlug : ''
      const sessionCacheKey = `${cacheKey.feedType}:${normalizedTopicSlug}::relevance`
      const sessionStorageKey = `scroll-${sessionCacheKey}`
      const sessionValue = sessionStorage.getItem(sessionStorageKey)
      
      return sessionValue ? parseInt(sessionValue, 10) : null
    } catch (error) {
      return null
    }
  }, [cacheKey.feedType, cacheKey.topicSlug, cacheKey.searchQuery, cacheKey.sortOrder])

  // Load pending articles when user clicks notification
  const loadPendingArticles = useCallback(async () => {
    if (isLoadingPending) return
    
    setIsLoadingPending(true)
    try {
      // Get current feed sync to find the feedSyncId
      const session = await import('next-auth/react').then(m => m.getSession())
      if (!session?.user?.django_user_id) return
      
      const userId = String(session.user.django_user_id)
      const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
      
      console.log(`🔄 useFeed: loadPendingArticles for ${feedType}:${topicSlug || 'for-you'} (normalized: ${normalizedTopicSlug || 'undefined'})`)
      
      // First, try topic-specific feed sync
      let feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
      console.log(`useFeed: Topic-specific feedSync:`, feedSync ? { id: feedSync.id, topicSlug: feedSync.topicSlug, pending: feedSync.pendingNewArticles || 0 } : 'none')
      
      // If no topic-specific feed sync or it has no pending articles, try general feed
      if ((!feedSync?.id || (!feedSync.pendingNewArticles && !feedSync.pendingUpdatedArticles)) && normalizedTopicSlug) {
        console.log('useFeed: No topic-specific pending articles, checking general feed')
        const generalFeedSync = await localDB.getFeedSync(userId, feedType, undefined)
        console.log(`useFeed: General feedSync:`, generalFeedSync ? { id: generalFeedSync.id, topicSlug: generalFeedSync.topicSlug, pending: generalFeedSync.pendingNewArticles || 0 } : 'none')
        if (generalFeedSync?.id && (generalFeedSync.pendingNewArticles || generalFeedSync.pendingUpdatedArticles)) {
          feedSync = generalFeedSync
          console.log('useFeed: Using general feed pending articles for topic-specific request')
        }
      }
      
      if (!feedSync?.id) {
        console.warn('useFeed: No feedSync found for loading pending articles')
        return
      }
      
      // Load the pending articles
      await dataManager.loadPendingArticles(feedSync.id)
      
      // Clear pending count
      setPendingArticles({ newArticlesCount: 0, updatedArticlesCount: 0 })
      
      // Refresh the feed to show the new articles
      await loadFeed(1, true, false)
      
      console.log('useFeed: Successfully loaded pending articles')
      
    } catch (error) {
      console.error('useFeed: Failed to load pending articles:', error)
    } finally {
      setIsLoadingPending(false)
    }
  }, [feedType, topicSlug, isLoadingPending, loadFeed])

  // Check for pending articles periodically
  const checkPendingArticles = useCallback(async () => {
    try {
      const session = await import('next-auth/react').then(m => m.getSession())
      if (!session?.user?.django_user_id) return
      
      const userId = String(session.user.django_user_id)
      const pending = await dataManager.getPendingArticlesCount(userId, feedType, topicSlug)
      console.log(`🔔 useFeed: checkPendingArticles result for ${feedType}:${topicSlug || 'for-you'}:`, pending)
      
      if (pending.newArticlesCount > 0 || pending.updatedArticlesCount > 0) {
        console.log(`useFeed: Setting pending articles state:`, pending)
        setPendingArticles(pending)
      } else {
        console.log(`useFeed: No pending articles, clearing state`)
        setPendingArticles({ newArticlesCount: 0, updatedArticlesCount: 0 })
      }
    } catch (error) {
      console.error('useFeed: Failed to check pending articles:', error)
    }
  }, [feedType, topicSlug])

  // Check for pending articles when component mounts and periodically
  useEffect(() => {
    checkPendingArticles()
    
    // Check every 30 seconds for pending articles
    const interval = setInterval(checkPendingArticles, 30000)
    
    return () => clearInterval(interval)
  }, [checkPendingArticles])

  return {
    articles: state.articles,
    isLoading: state.isLoading,
    isLoadingMore,
    error: state.error,
    hasMore: state.hasMore,
    page: state.page,
    totalPages: Math.ceil(state.totalItems / 10),
    totalItems: state.totalItems,
    lastSyncAt: state.lastSyncAt,
    loadMore,
    refresh,
    backgroundRefresh,
    saveScrollPosition,
    getScrollPosition,
    // Pending articles functionality
    pendingArticles,
    isLoadingPending,
    loadPendingArticles,
    checkPendingArticles
  }
}

// ===============================================
// ARTICLE DETAIL HOOK
// ===============================================

export function useArticleDetail(articleId: string, options: SyncOptions = {}) {
  const [data, setData] = useState<ArticleDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Stable options reference
  const optionsRef = useRef(options)
  optionsRef.current = options

  // Load article detail - simple function
  const loadArticleDetail = useCallback(async (forceRefresh = false) => {
    if (!articleId) return

    try {
      setIsLoading(true)
      setError(null)

      console.log(`useArticleDetail: Loading article ${articleId}`)
      
      const articleDetail = await dataManager.getArticleDetail(articleId, { 
        ...optionsRef.current, 
        forceRefresh,
        backgroundSync: !forceRefresh 
      })
      
      if (articleDetail) {
        setData(articleDetail)
        setIsLoading(false)
        setError(null)
        
        // Save to cache
        const cacheKey = `article-detail:${articleId}`
        hookStateCache.setArticleDetailCache(cacheKey, {
          data: articleDetail,
          timestamp: Date.now(),
          isLoading: false,
          error: null
        })
        
        // Auto-mark as read when article content is loaded
        await dataManager.markArticleAsRead(articleId)
      } else {
        setError('Article not found')
        setIsLoading(false)
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load article detail'
      setError(errorMessage)
      setIsLoading(false)
      console.error(`useArticleDetail: Failed to load article ${articleId}:`, err)
    }
  }, [articleId])

  // Auto-load on mount and when articleId changes
  useEffect(() => {
    if (!articleId) return
    
    const cacheKey = `article-detail:${articleId}`
    const cached = hookStateCache.getArticleDetailCache(cacheKey)
    
    if (cached && cached.data && (Date.now() - cached.timestamp) < hookStateCache.CACHE_TTL) {
      console.log(`useArticleDetail: Using cached data for article ${articleId}`)
      // Use cached data immediately
      setData(cached.data)
      setIsLoading(false)
      setError(null)
      
      // Track as recently viewed for background sync
      hookStateCache.trackRecentlyViewedArticle(articleId)
      
      // Trigger background refresh if data might be stale
      const backgroundRefresh = async () => {
        try {
          const freshData = await dataManager.getArticleDetail(articleId, { 
            ...optionsRef.current, 
            backgroundSync: true 
          })
          if (freshData && JSON.stringify(freshData) !== JSON.stringify(cached.data)) {
            setData(freshData)
            // Update cache
            hookStateCache.setArticleDetailCache(cacheKey, {
              data: freshData,
              timestamp: Date.now(),
              isLoading: false,
              error: null
            })
          }
        } catch (err) {
          console.log('useArticleDetail: Background refresh failed:', err)
        }
      }
      backgroundRefresh()
    } else {
      // Inline loading logic to avoid closure issues
      const loadFresh = async () => {
        try {
          setIsLoading(true)
          setError(null)

          const articleDetail = await dataManager.getArticleDetail(articleId, { 
            ...optionsRef.current, 
            forceRefresh: false,
            backgroundSync: false 
          })
          
          if (articleDetail) {
            setData(articleDetail)
            setIsLoading(false)
            setError(null)
            
            // Save to cache
            const cacheKey = `article-detail:${articleId}`
            hookStateCache.setArticleDetailCache(cacheKey, {
              data: articleDetail,
              timestamp: Date.now(),
              isLoading: false,
              error: null
            })
            
            // Track as recently viewed for background sync
            hookStateCache.trackRecentlyViewedArticle(articleId)
            
            // Auto-mark as read when article content is loaded
            await dataManager.markArticleAsRead(articleId)
          } else {
            setError('Article not found')
            setIsLoading(false)
          }
          
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to load article detail'
          setError(errorMessage)
          setIsLoading(false)
          console.error(`useArticleDetail: Failed to load article ${articleId}:`, err)
        }
      }
      
      loadFresh()
    }
  }, [articleId]) // Only depend on articleId to prevent infinite loops

  // Toggle saved status
  const toggleSaved = useCallback(async (): Promise<boolean> => {
    try {
      const newSavedState = await dataManager.toggleArticleSaved(articleId)
      
      // Update local state to reflect change
      if (data) {
        setData(prev => prev ? { 
          ...prev, 
          isSaved: newSavedState, 
          savedAt: newSavedState ? new Date() : undefined 
        } as ArticleDetail & { isSaved: boolean; savedAt?: Date } : prev)
      }
      
      return newSavedState
    } catch (err) {
      console.error(`useArticleDetail: Failed to toggle saved status for article ${articleId}:`, err)
      throw err
    }
  }, [articleId, data])

  return {
    data,
    isLoading,
    error,
    refresh: () => loadArticleDetail(true),
    toggleSaved
  }
}

// ===============================================
// SYNC STATUS HOOK (FOR DEBUGGING)
// ===============================================

export function useSyncStatus() {
  const [status, setStatus] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadStatus = useCallback(async () => {
    try {
      setIsLoading(true)
      const syncStatus = await dataManager.getSyncStatus()
      setStatus(syncStatus)
    } catch (err) {
      console.error('useSyncStatus: Failed to load sync status:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const forceRefreshAll = useCallback(async () => {
    try {
      await dataManager.forceRefreshAll()
      // Reload status after refresh
      await loadStatus()
    } catch (err) {
      console.error('useSyncStatus: Failed to force refresh all data:', err)
      throw err
    }
  }, [loadStatus])

  const cleanupOldData = useCallback(async () => {
    try {
      await localDB.cleanup()
      await loadStatus()
    } catch (err) {
      console.error('useSyncStatus: Failed to cleanup old data:', err)
      throw err
    }
  }, [loadStatus])

  useEffect(() => {
    loadStatus()
  }, [loadStatus])

  return {
    status,
    isLoading,
    refresh: loadStatus,
    forceRefreshAll,
    cleanupOldData
  }
}

// ===============================================
// BACKGROUND SYNC HOOK
// ===============================================

// Global tracking to prevent multiple background sync instances
let backgroundSyncInstance: NodeJS.Timeout | null = null
let backgroundSyncActive = false

export function useBackgroundSync(intervalMs: number = 10 * 60 * 1000) {
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)
  const [isBackgroundSyncing, setIsBackgroundSyncing] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const lastErrorTime = useRef<number>(0)

  const performBackgroundSync = useCallback(async () => {
    try {
      // Prevent too frequent retries if there were recent errors (wait at least 5 minutes)
      const now = Date.now()
      if (lastErrorTime.current > 0 && (now - lastErrorTime.current) < 5 * 60 * 1000) {
        console.log('useBackgroundSync: Skipping sync due to recent error, waiting before retry')
        return
      }

      setIsBackgroundSyncing(true)
      console.log('useBackgroundSync: Performing comprehensive background sync...')
      
      // Check if we're authenticated first to prevent loops after database cleanup
      const session = await import('next-auth/react').then(m => m.getSession())
      if (!session?.user?.django_user_id) {
        console.log('useBackgroundSync: No authenticated session, skipping background sync')
        return
      }
      
      // 1. Sync user preferences
      console.log('useBackgroundSync: Syncing user preferences...')
      await dataManager.getUserPreferences({ maxAge: 0, backgroundSync: false })
      
      // 2. Sync recently viewed article details (last 10 articles)
      console.log('useBackgroundSync: Syncing recently viewed articles...')
      const recentArticles = hookStateCache.getRecentlyViewedArticles(10)
      if (recentArticles.length > 0) {
        console.log(`useBackgroundSync: Found ${recentArticles.length} recent articles to sync`)
        // Sync articles in parallel for better performance
        const articleSyncPromises = recentArticles.map(async (articleId: string) => {
          try {
            await dataManager.getArticleDetail(articleId, { 
              maxAge: 30 * 60 * 1000, // 30 minutes max age
              backgroundSync: true 
            })
          } catch (error) {
            console.warn(`useBackgroundSync: Failed to sync article ${articleId}:`, error)
          }
        })
        await Promise.all(articleSyncPromises)
        console.log('useBackgroundSync: Recently viewed articles sync completed')
      }
      
      // 3. Smart background feed refresh (preserves cached pages and scroll position)
      console.log('useBackgroundSync: Smart refreshing feeds in background...')
      try {
        // Use session already obtained above
        const userId = String(session.user.django_user_id)
        
        // Use new cache-preserving background sync instead of destructive forceRefresh
        // This updates only the top articles while preserving user's loaded pages and scroll position
        const feedRefreshPromises = [
          dataManager.backgroundSyncFeed(userId, 'personalized'),
          dataManager.backgroundSyncFeed(userId, 'world')
        ]
        await Promise.all(feedRefreshPromises.map(p => p.catch((err: any) => 
          console.warn('useBackgroundSync: Feed background sync failed:', err)
        )))
        
        // 4. Notify about pending articles detected during background sync
        console.log('useBackgroundSync: Background sync completed - new articles are pending user action')
        // Note: Pending articles notifications will be triggered by the checkPendingArticles intervals in useFeed hooks
        
        console.log('useBackgroundSync: Smart background feed refresh completed - new articles detected and waiting for user to load')
      } catch (error) {
        console.warn('useBackgroundSync: Smart feed refresh failed:', error)
      }
      
      // 4. Background sync digests (latest digest)
      console.log('useBackgroundSync: Syncing latest digest...')
      try {
        // Use session already obtained above
        const userId = String(session.user.django_user_id)
        await dataManager.backgroundSyncDigests(userId)
        console.log('useBackgroundSync: Digest sync completed')
      } catch (error) {
        console.warn('useBackgroundSync: Digest sync failed:', error)
      }
      
      setLastSyncTime(new Date())
      lastErrorTime.current = 0 // Clear error time on successful sync
      console.log('useBackgroundSync: Comprehensive background sync completed successfully')
      
    } catch (error) {
      console.error('useBackgroundSync: Background sync failed:', error)
      lastErrorTime.current = Date.now() // Record error time to prevent frequent retries
    } finally {
      setIsBackgroundSyncing(false)
    }
  }, [])

  // Set up background sync interval with global deduplication
  useEffect(() => {
    // Prevent multiple instances
    if (backgroundSyncActive) {
      console.log('useBackgroundSync: Instance already active, skipping setup')
      return
    }

    // Clear any existing interval (local or global)
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }
    if (backgroundSyncInstance) {
      clearInterval(backgroundSyncInstance)
    }

    // Mark as active and set up new interval
    backgroundSyncActive = true
    intervalRef.current = setInterval(performBackgroundSync, intervalMs)
    backgroundSyncInstance = intervalRef.current
    
    console.log(`useBackgroundSync: Started background sync every ${intervalMs / 1000 / 60} minutes`)

    // Cleanup on unmount
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      if (backgroundSyncInstance) {
        clearInterval(backgroundSyncInstance)
        backgroundSyncInstance = null
      }
      backgroundSyncActive = false
      console.log('useBackgroundSync: Cleaned up background sync')
    }
  }, [intervalMs]) // Removed performBackgroundSync dependency to prevent loops

  // Trigger initial sync if needed (only once)
  useEffect(() => {
    if (!lastSyncTime) {
      performBackgroundSync()
    }
  }, []) // Empty dependency array - run only once on mount

  return {
    lastSyncTime,
    isBackgroundSyncing,
    forceSync: performBackgroundSync
  }
}



// ===============================================
// CACHE MANAGEMENT UTILITIES
// ===============================================

export function clearFeedCache(feedType?: 'personalized' | 'world', topicSlug?: string) {
  if (feedType) {
    hookStateCache.clearFeedCache({ feedType, topicSlug })
  } else {
    hookStateCache.clearFeedCache()
  }
}

export function clearUserPreferencesCache() {
  hookStateCache.clearUserPreferencesCache()
}

export function clearAllCaches() {
  hookStateCache.clearAll()
}

// ===============================================
// DEVELOPMENT HELPERS
// ===============================================

if (typeof window !== 'undefined') {
  (window as any).hookStateCache = hookStateCache;
  (window as any).clearFeedCache = clearFeedCache;
  (window as any).clearUserPreferencesCache = clearUserPreferencesCache;
  (window as any).clearAllCaches = clearAllCaches;
} 