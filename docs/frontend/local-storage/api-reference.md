# Local Storage API Reference

## Overview

Complete API reference for the DailyBrief local storage system, including all public methods, interfaces, and usage examples.

## 📚 Core APIs

### DataManager

Central orchestration layer for local-first data operations.

#### Methods

##### `getFeed(feedType, topicSlug?, page?, pageSize?, options?)`

Retrieves feed data with local-first caching strategy.

```typescript
async getFeed(
  feedType: 'personalized' | 'world',
  topicSlug?: string,
  page: number = 1,
  pageSize: number = 10,
  options: GetFeedOptions = {}
): Promise<FeedResult | null>
```

**Parameters:**
- `feedType` - Type of feed to retrieve
- `topicSlug` - Optional topic filter (e.g., 'technology', 'sports')
- `page` - Page number for pagination (1-based)
- `pageSize` - Number of articles per page
- `options` - Additional options

**Options:**
```typescript
interface GetFeedOptions {
  backgroundSync?: boolean     // Enable background sync (default: true)
  forceRefresh?: boolean      // Force fresh API call (default: false)
  maxAge?: number            // Override default staleness threshold
}
```

**Returns:**
```typescript
interface FeedResult {
  articles: Article[]
  pagination: {
    currentPage: number
    pageSize: number
    totalCount: number
    hasNext: boolean
  }
}
```

**Example:**
```typescript
// Get first page of personalized feed
const result = await dataManager.getFeed('personalized', undefined, 1, 10)

// Get technology articles with forced refresh
const techFeed = await dataManager.getFeed(
  'personalized', 
  'technology', 
  1, 
  10, 
  { forceRefresh: true }
)
```

##### `getArticleDetail(articleId, options?)`

Retrieves full article content with local-first caching.

```typescript
async getArticleDetail(
  articleId: string,
  options: GetArticleDetailOptions = {}
): Promise<ArticleDetail | null>
```

**Parameters:**
- `articleId` - Unique article identifier
- `options` - Additional options

**Options:**
```typescript
interface GetArticleDetailOptions {
  backgroundSync?: boolean    // Enable background sync (default: true)
  forceRefresh?: boolean     // Force fresh API call (default: false)
  maxAge?: number           // Override default staleness threshold
}
```

**Returns:**
```typescript
interface ArticleDetail {
  id: string
  title: string
  description?: string
  url: string
  publishedAt: Date
  source?: string
  content?: string
  summary?: string
  entities?: any[]
  heroImage?: string
  blocks?: ContentBlock[]
  isRead: boolean
  isSaved: boolean
  readingTime?: number
}
```

**Example:**
```typescript
// Get article with background sync
const article = await dataManager.getArticleDetail(
  'article-uuid-123', 
  { backgroundSync: true }
)

// Force fresh content for article
const freshArticle = await dataManager.getArticleDetail(
  'article-uuid-123',
  { forceRefresh: true }
)
```

##### `getUserPreferences(options?)`

Retrieves user preferences with caching.

```typescript
async getUserPreferences(
  options: GetUserPreferencesOptions = {}
): Promise<UserPreferences | null>
```

**Parameters:**
- `options` - Additional options

**Options:**
```typescript
interface GetUserPreferencesOptions {
  backgroundSync?: boolean    // Enable background sync (default: true)
  forceRefresh?: boolean     // Force fresh API call (default: false)
}
```

**Returns:**
```typescript
interface UserPreferences {
  topics: string[]
  regions: string[]
  languages: string[]
  publications: string[]
  topics_details: TopicDetail[]
  // ... other preference fields
}
```

##### `markArticleAsRead(articleId)`

Marks an article as read with optimistic updates.

```typescript
async markArticleAsRead(articleId: string): Promise<void>
```

**Example:**
```typescript
await dataManager.markArticleAsRead('article-uuid-123')
```

##### `toggleArticleSaved(articleId, isSaved)`

Toggles article saved status with optimistic updates.

```typescript
async toggleArticleSaved(articleId: string, isSaved: boolean): Promise<void>
```

**Example:**
```typescript
// Save article
await dataManager.toggleArticleSaved('article-uuid-123', true)

// Unsave article
await dataManager.toggleArticleSaved('article-uuid-123', false)
```

##### `clearUserData(userId)`

Clears all local data for a specific user.

```typescript
async clearUserData(userId: string): Promise<void>
```

### LocalDatabase

Dexie.js-based IndexedDB abstraction layer.

#### Methods

##### `saveUserProfile(profile)`

Saves user profile to local database.

```typescript
async saveUserProfile(profile: LocalUserProfile): Promise<number>
```

**Parameters:**
```typescript
interface LocalUserProfile {
  userId: string
  publicId: string
  email: string
  name: string
  hasCompletedOnboarding: boolean
  preferences: string        // JSON-serialized
  lastSyncAt: Date
}
```

##### `getUserProfile(userId)`

Retrieves user profile from local database.

```typescript
async getUserProfile(userId: string): Promise<LocalUserProfile | null>
```

##### `saveArticle(article)`

Saves article to local database.

```typescript
async saveArticle(article: LocalArticle): Promise<number>
```

**Parameters:**
```typescript
interface LocalArticle {
  backendId: string
  title: string
  description?: string
  url: string
  publishedAt: Date
  source?: string
  content?: string
  summary?: string
  entities?: string         // JSON-serialized
  isTopHeadline: boolean
  isRead: boolean
  isSaved: boolean
  lastSyncAt: Date
}
```

##### `getArticle(backendId)`

Retrieves article from local database.

```typescript
async getArticle(backendId: string): Promise<LocalArticle | null>
```

##### `getFeedArticles(userId, feedType, topicSlug, page, pageSize)`

Retrieves paginated feed articles.

```typescript
async getFeedArticles(
  userId: string,
  feedType: string,
  topicSlug: string | undefined,
  page: number,
  pageSize: number
): Promise<{
  articles: LocalArticle[]
  totalCount: number
  hasNext: boolean
}>
```

##### `emergencyCleanup()`

Performs emergency storage cleanup when quota exceeded.

```typescript
async emergencyCleanup(): Promise<void>
```

### StorageManager

Storage health and lifecycle management.

#### Methods

##### `checkStorageHealth()`

Checks overall storage health and availability.

```typescript
async checkStorageHealth(): Promise<StorageHealth>
```

**Returns:**
```typescript
interface StorageHealth {
  isAvailable: boolean
  usage: {
    used: number         // Bytes used
    available: number    // Bytes available  
    total: number       // Total quota
    percentage: number  // Usage percentage (0-100)
  }
  issues: string[]      // Array of health issues
  recommendations: string[]  // Suggested actions
}
```

**Example:**
```typescript
const health = await storageManager.checkStorageHealth()
console.log(`Storage usage: ${health.usage.percentage}%`)

if (health.issues.length > 0) {
  console.warn('Storage issues:', health.issues)
}
```

##### `getStorageInfo()`

Gets detailed storage usage information.

```typescript
async getStorageInfo(): Promise<StorageInfo>
```

**Returns:**
```typescript
interface StorageInfo {
  indexedDB: {
    used: number
    available: number
    databases: Array<{
      name: string
      size: number
      tables: Array<{
        name: string
        count: number
        size: number
      }>
    }>
  }
  localStorage: {
    used: number
    available: number
    keys: number
  }
  sessionStorage: {
    used: number
    keys: number
  }
}
```

##### `cleanupOldData()`

Removes old data based on retention policies.

```typescript
async cleanupOldData(): Promise<{
  articlesRemoved: number
  feedSyncsRemoved: number
  bytesFreed: number
}>
```

**Example:**
```typescript
const result = await storageManager.cleanupOldData()
console.log(`Cleaned up ${result.articlesRemoved} articles, freed ${result.bytesFreed} bytes`)
```

##### `clearUserData(userId)`

Clears all data for a specific user.

```typescript
async clearUserData(userId: string): Promise<void>
```

##### `clearAllData()`

Clears all local storage data (emergency reset).

```typescript
async clearAllData(): Promise<void>
```

## 🎣 React Hooks

### useFeed

Primary hook for feed data with local-first caching.

```typescript
function useFeed(
  feedType: 'personalized' | 'world',
  topicSlug?: string,
  searchQuery?: string,
  sortOrder: 'relevance' | 'newest' = 'relevance',
  options: UseFeedOptions = {}
): UseFeedResult
```

**Parameters:**
- `feedType` - Type of feed to load
- `topicSlug` - Optional topic filter
- `searchQuery` - Optional search query (future feature)
- `sortOrder` - Sort order for articles
- `options` - Hook configuration options

**Options:**
```typescript
interface UseFeedOptions {
  backgroundSync?: boolean    // Enable background sync
  autoMarkRead?: boolean     // Auto-mark articles as read
  prefetchNext?: boolean     // Prefetch next page
}
```

**Returns:**
```typescript
interface UseFeedResult {
  articles: Article[]        // Current articles
  isLoading: boolean        // Loading state
  hasMore: boolean         // More articles available
  error: string | null     // Error message
  loadMore: () => void     // Load next page
  refresh: () => void      // Refresh current data
  saveScrollPosition: (position: number) => void
  getScrollPosition: () => number | null
}
```

**Example:**
```typescript
function NewsFeed() {
  const {
    articles,
    isLoading,
    hasMore,
    loadMore,
    saveScrollPosition,
    getScrollPosition
  } = useFeed('personalized', 'technology')

  useEffect(() => {
    // Restore scroll position
    const savedPosition = getScrollPosition()
    if (savedPosition) {
      window.scrollTo(0, savedPosition)
    }
  }, [getScrollPosition])

  return (
    <div>
      {articles.map(article => (
        <ArticleCard key={article.id} article={article} />
      ))}
      {hasMore && (
        <button onClick={loadMore} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  )
}
```

### useArticleDetail

Hook for article content with background sync.

```typescript
function useArticleDetail(
  articleId: string,
  options: UseArticleDetailOptions = {}
): UseArticleDetailResult
```

**Parameters:**
- `articleId` - Article ID to load
- `options` - Hook configuration options

**Options:**
```typescript
interface UseArticleDetailOptions {
  autoMarkRead?: boolean     // Auto-mark as read (default: true)
  backgroundSync?: boolean   // Enable background sync
  maxAge?: number           // Override staleness threshold
}
```

**Returns:**
```typescript
interface UseArticleDetailResult {
  article: ArticleDetail | null
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  toggleSaved: () => Promise<void>
}
```

**Example:**
```typescript
function ArticlePage({ articleId }: { articleId: string }) {
  const { article, isLoading, error, toggleSaved } = useArticleDetail(articleId)

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error}</div>
  if (!article) return <div>Article not found</div>

  return (
    <article>
      <h1>{article.title}</h1>
      <button onClick={toggleSaved}>
        {article.isSaved ? 'Unsave' : 'Save'} Article
      </button>
      <div dangerouslySetInnerHTML={{ __html: article.content }} />
    </article>
  )
}
```

### useUserPreferences

Hook for user preferences with caching.

```typescript
function useUserPreferences(
  options: UseUserPreferencesOptions = {}
): UseUserPreferencesResult
```

**Options:**
```typescript
interface UseUserPreferencesOptions {
  backgroundSync?: boolean   // Enable background sync
  autoRefresh?: boolean     // Auto-refresh on window focus
}
```

**Returns:**
```typescript
interface UseUserPreferencesResult {
  preferences: UserPreferences | null
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  updatePreferences: (updates: Partial<UserPreferences>) => Promise<void>
}
```

**Example:**
```typescript
function PreferencesPanel() {
  const { preferences, updatePreferences } = useUserPreferences()

  const handleTopicToggle = async (topicId: string) => {
    if (!preferences) return
    
    const newTopics = preferences.topics.includes(topicId)
      ? preferences.topics.filter(id => id !== topicId)
      : [...preferences.topics, topicId]
    
    await updatePreferences({ topics: newTopics })
  }

  return (
    <div>
      {preferences?.topics_details.map(topic => (
        <button
          key={topic.id}
          onClick={() => handleTopicToggle(topic.id)}
          className={preferences.topics.includes(topic.id) ? 'selected' : ''}
        >
          {topic.name}
        </button>
      ))}
    </div>
  )
}
```

### useOfflineStatus

Hook for monitoring online/offline status.

```typescript
function useOfflineStatus(): UseOfflineStatusResult
```

**Returns:**
```typescript
interface UseOfflineStatusResult {
  isOnline: boolean         // Current online status
  wasOffline: boolean      // Was offline since last check
  lastOnlineAt: Date | null // Last time app was online
}
```

**Example:**
```typescript
function OfflineIndicator() {
  const { isOnline, wasOffline } = useOfflineStatus()

  if (isOnline && wasOffline) {
    return <div className="alert success">Back online!</div>
  }

  if (!isOnline) {
    return <div className="alert warning">You're offline</div>
  }

  return null
}
```

### useBackgroundSync

Hook for managing background synchronization.

```typescript
function useBackgroundSync(
  interval?: number,
  options: UseBackgroundSyncOptions = {}
): UseBackgroundSyncResult
```

**Parameters:**
- `interval` - Sync interval in milliseconds (default: 10 minutes)
- `options` - Sync configuration options

**Options:**
```typescript
interface UseBackgroundSyncOptions {
  enabled?: boolean         // Enable background sync
  onVisibilityChange?: boolean // Sync on tab visibility change
  onNetworkChange?: boolean   // Sync on network status change
}
```

**Returns:**
```typescript
interface UseBackgroundSyncResult {
  isSyncing: boolean       // Currently syncing
  lastSyncAt: Date | null  // Last sync timestamp
  syncNow: () => Promise<void> // Manual sync trigger
}
```

## 🔧 Utility Functions

### Scroll Restoration

#### `initClientScrollRestoration()`

Initializes client-side scroll restoration for Next.js navigation.

```typescript
function initClientScrollRestoration(): void
```

**Usage:**
```typescript
useEffect(() => {
  initClientScrollRestoration()
}, [])
```

#### `saveScrollImmediately(position)`

Saves scroll position immediately to sessionStorage.

```typescript
function saveScrollImmediately(position: number): void
```

#### `restoreScrollImmediately()`

Restores scroll position immediately (used in inline script).

```typescript
function restoreScrollImmediately(): boolean
```

### Debug Functions

Available in development mode via browser console.

#### `debugFeedState()`

Displays current feed state and cache contents.

```typescript
function debugFeedState(): void
```

**Example:**
```javascript
// In browser console
debugFeedState()
// Outputs: Current feeds, article counts, cache status
```

#### `debugStorageHealth()`

Displays storage health and usage statistics.

```typescript
function debugStorageHealth(): Promise<void>
```

#### `clearAllCaches()`

Clears all in-memory caches.

```typescript
function clearAllCaches(): void
```

#### `testStorageCleanup()`

Triggers manual storage cleanup for testing.

```typescript
function testStorageCleanup(): Promise<void>
```

#### `debugScrollPositions()`

Shows current scroll positions in cache.

```typescript
function debugScrollPositions(): void
```

## 🎯 Type Definitions

### Core Types

```typescript
// Article types
interface Article {
  id: string
  title: string
  description?: string
  url: string
  publishedAt: Date
  source?: string
  isRead: boolean
  isSaved: boolean
  readingTime?: number
}

interface ArticleDetail extends Article {
  content?: string
  summary?: string
  entities?: any[]
  heroImage?: string
  blocks?: ContentBlock[]
}

// Feed types
type FeedType = 'personalized' | 'world'
type SortOrder = 'relevance' | 'newest'

interface FeedCacheKey {
  feedType: FeedType
  topicSlug?: string
  sortOrder?: SortOrder
}

// User preference types
interface UserPreferences {
  topics: string[]
  regions: string[]
  languages: string[]
  publications: string[]
  topics_details: TopicDetail[]
}

interface TopicDetail {
  id: string
  name: string
  slug: string
  description?: string
}
```

### Cache Types

```typescript
interface FeedCacheEntry {
  articles: Article[]
  timestamp: number
  hasMore: boolean
  scrollPosition?: number
}

interface ArticleDetailCacheEntry {
  article: ArticleDetail
  timestamp: number
}

interface UserPreferencesCacheEntry {
  preferences: UserPreferences
  timestamp: number
}
```

### Configuration Types

```typescript
interface DataManagerConfig {
  userPreferencesMaxAge: number
  feedMaxAge: number
  articleDetailMaxAge: number
  enableBackgroundSync: boolean
  maxConcurrentSyncs: number
}

interface StorageConfig {
  cleanupThreshold: number      // Storage usage threshold (0-1)
  articleRetentionDays: number  // Days to keep articles
  feedSyncRetentionDays: number // Days to keep feed sync data
}
```

## 🚨 Error Types

```typescript
// Storage errors
class StorageQuotaExceededError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'StorageQuotaExceededError'
  }
}

class StorageUnavailableError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'StorageUnavailableError'
  }
}

// Network errors
class OfflineError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'OfflineError'
  }
}

// Data errors
class DataCorruptionError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DataCorruptionError'
  }
}
```

## 📊 Performance API

### Metrics Collection

```typescript
interface PerformanceMetrics {
  feedLoadTime: number         // Time to load feed (ms)
  articleLoadTime: number      // Time to load article (ms)
  cacheHitRate: number        // Cache hit percentage (0-100)
  storageUsage: number        // Storage usage percentage (0-100)
  scrollRestorationTime: number // Time to restore scroll (ms)
}

// Get current performance metrics
function getPerformanceMetrics(): Promise<PerformanceMetrics>
```

### Health Monitoring

```typescript
interface HealthCheck {
  timestamp: Date
  status: 'healthy' | 'warning' | 'critical'
  checks: {
    storage: boolean
    cache: boolean
    sync: boolean
    offline: boolean
  }
  metrics: PerformanceMetrics
}

// Run comprehensive health check
function runHealthCheck(): Promise<HealthCheck>
```

This API reference provides complete documentation for all public interfaces and methods in the local storage system, enabling developers to effectively integrate and extend the functionality. 