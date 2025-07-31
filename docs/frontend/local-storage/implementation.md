# Local Storage Implementation Guide

## Overview

This document provides detailed technical implementation guidance for the DailyBrief local storage system, including file structure, code patterns, development workflows, and best practices.

## 📁 File Structure

```
frontend/lib/
├── local-database.ts        # IndexedDB layer (Dexie.js)
├── data-manager.ts          # Central orchestration layer
├── storage-manager.ts       # Storage health & lifecycle management
├── use-local-data.ts       # React hooks integration
├── scroll-restoration.ts   # Inline script utilities
├── client-scroll-restoration.ts  # Next.js navigation handling
└── test-database.ts        # Development testing utilities

frontend/components/
└── infinite-news-feed.tsx  # Scroll restoration integration

frontend/app/
├── layout.tsx              # Inline scroll restoration script
└── test/page.tsx          # Development testing interface
```

## 🛠️ Core Implementation Files

### 1. Local Database (`local-database.ts`)

**Purpose**: Dexie.js-based IndexedDB abstraction layer

#### Data Models

```typescript
// User profile with preferences
interface LocalUserProfile {
  userId: string             // Backend user ID
  publicId: string          // Public UUID for API exposure
  email: string
  name: string
  hasCompletedOnboarding: boolean
  preferences: string       // JSON-serialized user preferences
  lastSyncAt: Date
  createdAt?: Date
  updatedAt?: Date
}

// Article content and metadata  
interface LocalArticle {
  backendId: string         // Backend article ID (unique)
  title: string
  description?: string
  url: string
  publishedAt: Date
  source?: string
  content?: string          // Full article content
  summary?: string          // AI-generated summary
  entities?: string         // JSON-serialized entities
  isTopHeadline: boolean
  isRead: boolean           // User interaction state
  isSaved: boolean          // User interaction state
  lastSyncAt: Date
  createdAt?: Date
  updatedAt?: Date
}

// Feed synchronization state
interface FeedSync {
  userId: string
  feedType: 'personalized' | 'world'
  topicSlug?: string        // Optional topic filter
  lastSyncAt: Date
  hasMore: boolean          // Backend pagination state
  isStale: boolean          // Cache staleness flag
  totalCount: number        // Total articles in this feed
  createdAt?: Date
  updatedAt?: Date
}

// Feed-article relationship mapping
interface FeedItem {
  feedSyncId: number        // Reference to FeedSync
  articleId: number         // Reference to LocalArticle
  position: number          // Order position in feed
  addedAt: Date            // When this item was added to feed
}
```

#### Database Schema

```typescript
class LocalDatabase extends Dexie {
  userProfiles!: Table<LocalUserProfile, number>
  articles!: Table<LocalArticle, number>
  feedSyncs!: Table<FeedSync, number>
  feedItems!: Table<FeedItem, number>

  constructor() {
    super('DailyBriefLocalDB')
    
    this.version(1).stores({
      userProfiles: '++id, userId, publicId, lastSyncAt',
      articles: '++id, backendId, publishedAt, isTopHeadline, isRead, isSaved, lastSyncAt',
      feedSyncs: '++id, userId, feedType, lastSyncAt, nextSyncAt, isStale',
      feedItems: '++id, feedSyncId, articleId, position, addedAt'
    })
    
    // Automatic timestamp hooks
    this.userProfiles.hook('creating', (primKey, obj, trans) => {
      obj.createdAt = new Date()
      obj.updatedAt = new Date()
    })
    
    this.userProfiles.hook('updating', (modifications, primKey, obj, trans) => {
      modifications.updatedAt = new Date()
    })
  }
}
```

#### Key Methods

```typescript
// Safe database operations with error handling
async safeExecute<T>(operation: () => Promise<T>, context: string): Promise<T | null> {
  try {
    return await operation()
  } catch (error) {
    if (error.name === 'QuotaExceededError') {
      // Trigger emergency cleanup
      await this.emergencyCleanup()
      throw new Error('Storage quota exceeded - cleaned up and retrying')
    }
    
    return null
  }
}

// Optimized feed article retrieval with pagination
async getFeedArticles(
  userId: string, 
  feedType: string, 
  topicSlug: string | undefined, 
  page: number, 
  pageSize: number
): Promise<{ articles: LocalArticle[], totalCount: number, hasNext: boolean }> {
  
  const feedSync = await this.getFeedSync(userId, feedType, topicSlug)
  if (!feedSync) {
    return { articles: [], totalCount: 0, hasNext: false }
  }

  const offset = (page - 1) * pageSize
  
  // Get feed items with pagination
  const feedItems = await this.feedItems
    .where('feedSyncId')
    .equals(feedSync.id!)
    .offset(offset)
    .limit(pageSize)
    .toArray()

  const articleIds = feedItems.map(item => item.articleId)
  
  // Fetch articles in correct order
  const articles = await this.articles
    .where('id')
    .anyOf(articleIds)
    .toArray()
    
  // Sort articles by feed position
  const sortedArticles = feedItems
    .map(item => articles.find(a => a.id === item.articleId))
    .filter(Boolean) as LocalArticle[]

  const totalCount = await this.feedItems
    .where('feedSyncId')
    .equals(feedSync.id!)
    .count()

  const totalPages = Math.ceil(totalCount / pageSize)
  const hasNext = (page < totalPages) || feedSync.hasMore

  return { 
    articles: sortedArticles, 
    totalCount, 
    hasNext 
  }
}
```

### 2. Data Manager (`data-manager.ts`)

**Purpose**: Central orchestration layer implementing local-first strategy

#### Configuration

```typescript
interface DataManagerConfig {
  userPreferencesMaxAge: number  // 30 minutes
  feedMaxAge: number            // 10 minutes
  articleDetailMaxAge: number   // 1 hour
  enableBackgroundSync: boolean
  maxConcurrentSyncs: number
}

const DEFAULT_CONFIG: DataManagerConfig = {
  userPreferencesMaxAge: 30 * 60 * 1000,  // 30 minutes
  feedMaxAge: 10 * 60 * 1000,             // 10 minutes
  articleDetailMaxAge: 60 * 60 * 1000,    // 1 hour
  enableBackgroundSync: true,
  maxConcurrentSyncs: 3
}
```

#### Core Methods

```typescript
class DataManager {
  private activeSyncs = new Set<string>()
  private syncQueue = new Map<string, Promise<any>>()
  
  // Local-first feed access
  async getFeed(
    feedType: string,
    topicSlug: string | undefined = undefined,
    page: number = 1,
    pageSize: number = 10,
    options: GetFeedOptions = {}
  ): Promise<FeedResult | null> {
    
    const currentUser = getUserFromContext()
    if (!currentUser) return null

    // Check local cache first
    const localResult = await localDB.getFeedArticles(
      currentUser.id, feedType, topicSlug, page, pageSize
    )

    const feedSync = await localDB.getFeedSync(
      currentUser.id, feedType, topicSlug
    )

    // Determine if we have the requested page locally
    const hasLocalPage = localResult.articles.length > 0
    const isStale = feedSync ? this.isStale(feedSync.lastSyncAt, this.config.feedMaxAge) : true

    // Return immediately if we have fresh local data
    if (hasLocalPage && !isStale) {
      return {
        articles: localResult.articles,
        pagination: {
          currentPage: page,
          pageSize,
          totalCount: localResult.totalCount,
          hasNext: localResult.hasNext
        }
      }
    }

    // If no local data for this page, fetch from backend
    if (!hasLocalPage && localResult.hasNext) {
      return await this.fetchSinglePage(feedType, topicSlug, page, pageSize)
    }

    // Background sync if stale
    if (options.backgroundSync !== false && isStale) {
      this.queueBackgroundSync(
        `feed-${feedType}-${topicSlug || 'none'}`,
        () => this.syncFeed(feedType, topicSlug)
      )
    }

    return hasLocalPage ? {
      articles: localResult.articles,
      pagination: {
        currentPage: page,
        pageSize,
        totalCount: localResult.totalCount,
        hasNext: localResult.hasNext
      }
    } : null
  }

  // Single page fetch and cache
  private async fetchSinglePage(
    feedType: string,
    topicSlug: string | undefined,
    page: number,
    pageSize: number
  ): Promise<FeedResult | null> {
    
    const syncKey = `fetch-${feedType}-${topicSlug || 'none'}-page-${page}`
    if (this.activeSyncs.has(syncKey)) {
      return null // Prevent concurrent fetches
    }

    this.activeSyncs.add(syncKey)
    
    try {
      // Fetch from backend API
      const apiResult = feedType === 'personalized' 
        ? await getPersonalizedFeed({ page, page_size: pageSize })
        : await getWorldFeed({ page, page_size: pageSize })

      if (!apiResult?.articles) return null

      // Get existing feed sync record
      const currentUser = getUserFromContext()!
      let feedSync = await localDB.getFeedSync(currentUser.id, feedType, topicSlug)
      
      if (!feedSync) {
        // Create new feed sync
        const feedSyncId = await localDB.feedSyncs.add({
          userId: currentUser.id,
          feedType: feedType as any,
          topicSlug,
          lastSyncAt: new Date(),
          hasMore: apiResult.hasNext || false,
          isStale: false,
          totalCount: apiResult.articles.length
        })
        feedSync = await localDB.feedSyncs.get(feedSyncId!)
      }

      // Save articles and feed items
      await this.saveArticlesAndFeedItems(
        apiResult.articles, 
        feedSync!, 
        page, 
        pageSize
      )

      // Return formatted result
      const localResult = await localDB.getFeedArticles(
        currentUser.id, feedType, topicSlug, page, pageSize
      )

      return {
        articles: localResult.articles,
        pagination: {
          currentPage: page,
          pageSize,
          totalCount: localResult.totalCount,
          hasNext: localResult.hasNext
        }
      }

    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  // Background sync with debouncing
  private queueBackgroundSync(key: string, syncFn: () => Promise<void>): void {
    if (this.syncQueue.has(key)) return

    const syncPromise = new Promise<void>((resolve) => {
      setTimeout(async () => {
        try {
          await syncFn()
        } catch (error) {
          // Silent fail for background sync
        } finally {
          this.syncQueue.delete(key)
          resolve()
        }
      }, 100) // Small delay to batch rapid calls
    })

    this.syncQueue.set(key, syncPromise)
  }
}
```

### 3. React Hooks Integration (`use-local-data.ts`)

**Purpose**: Reactive React integration with state persistence

#### Hook State Cache

```typescript
class HookStateCache {
  private static instance: HookStateCache
  static readonly CACHE_TTL = 5 * 60 * 1000 // 5 minutes

  private feedCache = new Map<string, FeedCacheEntry>()
  private userPreferencesCache: UserPreferencesCacheEntry | null = null
  private articleDetailCache = new Map<string, ArticleDetailCacheEntry>()

  // Persistent state for feed hooks
  getFeedCache(key: FeedCacheKey): FeedCacheEntry | null {
    const cacheKey = this.generateCacheKey(key)
    const entry = this.feedCache.get(cacheKey)
    
    if (entry && this.isExpired(entry.timestamp)) {
      this.feedCache.delete(cacheKey)
      return null
    }
    
    return entry || null
  }

  setFeedCache(key: FeedCacheKey, data: Partial<FeedCacheEntry>): void {
    const cacheKey = this.generateCacheKey(key)
    const existing = this.feedCache.get(cacheKey) || { 
      articles: [], 
      timestamp: Date.now(), 
      hasMore: true 
    }
    
    this.feedCache.set(cacheKey, {
      ...existing,
      ...data,
      timestamp: Date.now()
    })
  }

  // Scroll position management
  saveScrollPosition(key: FeedCacheKey, scrollPosition: number): void {
    const cacheKey = this.generateCacheKey(key)
    
    // Update memory cache
    this.setFeedCache(key, { scrollPosition })
    
    // Update sessionStorage for persistence
    const sessionKey = `scroll-${cacheKey}`
    try {
      sessionStorage.setItem(sessionKey, scrollPosition.toString())
    } catch (error) {
      // Ignore storage errors
    }
  }

  getScrollPosition(key: FeedCacheKey): number | null {
    const cacheKey = this.generateCacheKey(key)
    
    // Try memory cache first
    const cached = this.getFeedCache(key)
    if (cached?.scrollPosition !== undefined) {
      return cached.scrollPosition
    }
    
    // Fallback to sessionStorage
    try {
      const sessionKey = `scroll-${cacheKey}`
      const saved = sessionStorage.getItem(sessionKey)
      return saved ? parseInt(saved, 10) : null
    } catch (error) {
      return null
    }
  }
}
```

#### Primary Hooks

```typescript
// Feed data hook with local-first caching
export function useFeed(
  feedType: 'personalized' | 'world',
  topicSlug?: string,
  searchQuery?: string,
  sortOrder: 'relevance' | 'newest' = 'relevance',
  options: UseFeedOptions = {}
): UseFeedResult {
  
  const [articles, setArticles] = useState<Article[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasMore, setHasMore] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  const cacheKey: FeedCacheKey = { feedType, topicSlug, sortOrder }
  const cache = HookStateCache.getInstance()

  // Initialize from cache
  useEffect(() => {
    const cachedData = cache.getFeedCache(cacheKey)
    if (cachedData) {
      setArticles(cachedData.articles)
      setHasMore(cachedData.hasMore)
      setCurrentPage(Math.ceil(cachedData.articles.length / 10))
      setIsLoading(false)
      return
    }

    // No cache, load fresh
    loadFeed(1, true)
  }, [feedType, topicSlug, sortOrder])

  const loadFeed = useCallback(async (
    page: number, 
    reset: boolean = false
  ) => {
    if (isLoading) return

    setIsLoading(true)
    setError(null)

    try {
      const result = await dataManager.getFeed(
        feedType, 
        topicSlug, 
        page, 
        10, 
        options
      )

      if (result) {
        const newArticles = reset ? result.articles : [...articles, ...result.articles]
        
        setArticles(newArticles)
        setHasMore(result.pagination.hasNext)
        setCurrentPage(page)

        // Update cache
        cache.setFeedCache(cacheKey, {
          articles: newArticles,
          hasMore: result.pagination.hasNext,
          timestamp: Date.now()
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feed')
    } finally {
      setIsLoading(false)
    }
  }, [feedType, topicSlug, articles, isLoading, options])

  const loadMore = useCallback(() => {
    if (!hasMore || isLoading) return
    loadFeed(currentPage + 1, false)
  }, [hasMore, isLoading, currentPage, loadFeed])

  // Scroll position helpers
  const saveScrollPosition = useCallback((position: number) => {
    cache.saveScrollPosition(cacheKey, position)
  }, [cacheKey, cache])

  const getScrollPosition = useCallback((): number | null => {
    return cache.getScrollPosition(cacheKey)
  }, [cacheKey, cache])

  return {
    articles,
    isLoading,
    hasMore,
    error,
    loadMore,
    refresh: () => loadFeed(1, true),
    saveScrollPosition,
    getScrollPosition
  }
}

// Article detail hook with background sync
export function useArticleDetail(
  articleId: string,
  options: UseArticleDetailOptions = {}
): UseArticleDetailResult {
  
  const [data, setData] = useState<ArticleDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const cache = HookStateCache.getInstance()

  useEffect(() => {
    if (!articleId) return

    const loadArticle = async () => {
      // Check cache first
      const cachedArticle = cache.getArticleDetailCache(articleId)
      if (cachedArticle && !cache.isExpired(cachedArticle.timestamp)) {
        setData(cachedArticle.article)
        setIsLoading(false)
        setError(null)
        return
      }

      setIsLoading(true)
      setError(null)

      try {
        const article = await dataManager.getArticleDetail(articleId, options)
        if (article) {
          setData(article)
          
          // Cache the result
          cache.setArticleDetailCache(articleId, {
            article,
            timestamp: Date.now()
          })
        } else {
          setError('Article not found')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load article')
      } finally {
        setIsLoading(false)
      }
    }

    loadArticle()
  }, [articleId, options, cache])

  const refresh = useCallback(async () => {
    if (!articleId) return

    setIsLoading(true)
    try {
      const article = await dataManager.getArticleDetail(articleId, { 
        ...options, 
        forceRefresh: true 
      })
      if (article) {
        setData(article)
        cache.setArticleDetailCache(articleId, {
          article,
          timestamp: Date.now()
        })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh article')
    } finally {
      setIsLoading(false)
    }
  }, [articleId, options, cache])

  const toggleSaved = useCallback(async () => {
    if (!data) return

    const newSavedState = !data.isSaved
    
    // Optimistic update
    setData(prev => prev ? { ...prev, isSaved: newSavedState } : null)
    
    try {
      await dataManager.toggleArticleSaved(articleId, newSavedState)
    } catch (error) {
      // Revert on error
      setData(prev => prev ? { ...prev, isSaved: !newSavedState } : null)
      throw error
    }
  }, [data, articleId])

  return {
    article: data,
    isLoading,
    error,
    refresh,
    toggleSaved
  }
}
```

## 🔄 Development Workflow

### 1. Local Development Setup

```bash
# Install dependencies
npm install dexie

# Start development server
npm run dev

# Access test interface
http://localhost:3000/test
```

### 2. Testing Utilities

```typescript
// Available in browser console during development
window.dataManager       // Access data manager directly
window.localDB          // Access database directly
window.debugFeedState    // Inspect current feed state
window.debugStorageHealth // Check storage health
window.clearAllCaches    // Reset all caches

// Test functions
debugFeedState()         // Shows cached articles and sync state
clearAllCaches()         // Clears memory cache completely
testStorageCleanup()     // Triggers storage cleanup manually
```

### 3. Debug Interface

The `/test` page provides interactive testing:

```typescript
// Example test usage
<Button onClick={() => debugFeedState()}>
  🔍 Debug Feed State
</Button>

<Button onClick={() => clearAllCaches()}>
  🗑️ Clear All Caches  
</Button>

<Button onClick={() => dataManager.getFeed('world', undefined, 6, 10)}>
  📄 Test Page 6 Loading
</Button>
```

## 🎯 Best Practices

### 1. Error Handling Patterns

```typescript
// Always wrap database operations
async function safeOperation<T>(operation: () => Promise<T>): Promise<T | null> {
  try {
    return await operation()
  } catch (error) {
    if (error.name === 'QuotaExceededError') {
      await storageManager.cleanupOldData()
      // Retry once after cleanup
      try {
        return await operation()
      } catch (retryError) {
        return null
      }
    }
    return null
  }
}

// Component error boundaries
const [error, setError] = useState<string | null>(null)

try {
  const result = await dataManager.getFeed(...)
  setError(null)
} catch (err) {
  setError(err instanceof Error ? err.message : 'Unknown error')
}
```

### 2. Performance Optimization

```typescript
// Debounced scroll saving
const debouncedSaveScroll = useCallback(
  debounce((position: number) => {
    saveScrollPosition(position)
  }, 150),
  [saveScrollPosition]
)

// Memoized expensive computations
const processedArticles = useMemo(() => {
  return articles.map(article => ({
    ...article,
    readingTime: calculateReadingTime(article.content)
  }))
}, [articles])

// Prevent unnecessary re-renders
const MemoizedNewsCard = React.memo(NewsCard)
```

### 3. Memory Management

```typescript
// Cleanup on component unmount
useEffect(() => {
  return () => {
    // Clear timers
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current)
    }
    
    // Clear intersection observers
    if (observerRef.current) {
      observerRef.current.disconnect()
    }
  }
}, [])

// Automatic cache cleanup
setInterval(() => {
  HookStateCache.getInstance().cleanupExpiredEntries()
}, 10 * 60 * 1000) // Every 10 minutes
```

### 4. Type Safety

```typescript
// Strict typing for all interfaces
interface FeedResult {
  articles: Article[]
  pagination: {
    currentPage: number
    pageSize: number
    totalCount: number
    hasNext: boolean
  }
}

// Runtime type validation for critical data
function validateArticle(data: any): data is Article {
  return (
    typeof data === 'object' &&
    typeof data.id === 'string' &&
    typeof data.title === 'string' &&
    data.publishedAt instanceof Date
  )
}
```

## 🔧 Configuration Management

### Environment Variables

```typescript
// Development vs Production configs
const config = {
  userPreferencesMaxAge: process.env.NODE_ENV === 'development' 
    ? 5 * 60 * 1000  // 5 minutes in dev
    : 30 * 60 * 1000, // 30 minutes in prod
    
  enableDebugLogging: process.env.NODE_ENV === 'development',
  
  storageQuotaThreshold: 0.85, // 85% usage triggers cleanup
  
  backgroundSyncInterval: 10 * 60 * 1000 // 10 minutes
}
```

### Feature Flags

```typescript
// Conditional features for gradual rollout
const FEATURES = {
  ADVANCED_SCROLL_RESTORATION: true,
  BACKGROUND_SYNC: true,
  PREDICTIVE_CACHING: false, // Future feature
  CROSS_TAB_SYNC: true
}

if (FEATURES.BACKGROUND_SYNC) {
  useBackgroundSync(10 * 60 * 1000) // 10 minutes
}
```

## 🚀 Deployment Considerations

### Production Optimizations

```typescript
// Remove debug logging in production builds
const log = process.env.NODE_ENV === 'development' 
  ? console.log 
  : () => {}

// Minimize bundle size
import { debounce } from 'lodash-es' // Use ES modules
// vs
import debounce from 'lodash/debounce' // Tree-shakeable

// Service worker registration for PWA
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  navigator.serviceWorker.register('/sw.js')
}
```

### Monitoring Integration

```typescript
// Error tracking
if (error && process.env.NODE_ENV === 'production') {
  // Send to error tracking service
  trackError('Local Storage Error', {
    operation: 'getFeed',
    feedType,
    error: error.message
  })
}

// Performance monitoring
const startTime = performance.now()
await dataManager.getFeed(...)
const endTime = performance.now()

if (process.env.NODE_ENV === 'production') {
  trackPerformance('Feed Load Time', endTime - startTime)
}
```

### Graceful Degradation

```typescript
// Fallback to API-only mode if local storage fails
class DataManager {
  private localStorageEnabled = true

  private async checkLocalStorageHealth(): Promise<boolean> {
    try {
      await localDB.userProfiles.limit(1).toArray()
      return true
    } catch (error) {
      this.localStorageEnabled = false
      return false
    }
  }

  async getFeed(...args): Promise<FeedResult | null> {
    if (!this.localStorageEnabled) {
      // Direct API call without caching
      return await this.fetchFromAPI(...args)
    }
    
    // Normal local-first flow
    return await this.getFeedWithCache(...args)
  }
}
```

This implementation provides a robust, maintainable foundation for the local storage system with clear separation of concerns, comprehensive error handling, and production-ready optimizations. 