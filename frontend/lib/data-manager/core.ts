import { localDB, LocalArticle, LocalUserProfile, FeedSync, LocalDigest, DigestSync } from '../local-database'
import { storageManager } from '../storage-manager'
import { 
  getUserPreferences, 
  getPersonalizedFeed, 
  getWorldFeed, 
  getPublicWorldFeed,
  getArticleDetail,
  UserPreferences,
  ArticlePreview,
  ArticleDetail,
  PaginatedResponse
} from '../api'
import { digestService, type Digest } from '../digest-service'
import { getSession } from 'next-auth/react'

// ===============================================
// TYPES AND INTERFACES
// ===============================================

export interface LocalArticlePreview extends ArticlePreview {
  isRead: boolean
  isSaved: boolean
  readAt?: Date
  savedAt?: Date
  topics?: Array<{
    id: number
    name: string
    slug: string
  }>
}

export interface SyncOptions {
  forceRefresh?: boolean
  backgroundSync?: boolean
  maxAge?: number
}

export interface DataManagerConfig {
  userPreferencesMaxAge: number // 30 minutes default
  feedMaxAge: number // 10 minutes default
  articleDetailMaxAge: number // 1 hour default
  digestMaxAge: number // 30 minutes default
  enableBackgroundSync: boolean
  maxConcurrentSyncs: number
}

// ===============================================
// DATA MANAGER CLASS
// ===============================================

/**
 * Central data manager for local storage and smart syncing
 * 
 * KEY PRINCIPLES TO PREVENT LOOPS:
 * 1. NO automatic API calls - all syncs are explicit
 * 2. Local-first - always return local data immediately if available
 * 3. Background sync - API calls happen separately from data access
 * 4. Debounced sync - prevent duplicate/rapid sync requests
 * 5. Clear separation - data access vs sync operations
 */
export class DataManager {
  private config: DataManagerConfig
  private syncQueue: Set<string> = new Set() // Prevent duplicate syncs
  private activeSyncs: Set<string> = new Set() // Track active syncs
  private readonly SYNC_DEBOUNCE_MS = 2000 // 2 second debounce

  constructor(config?: Partial<DataManagerConfig>) {
    this.config = {
      userPreferencesMaxAge: 30 * 60 * 1000, // 30 minutes
      feedMaxAge: 10 * 60 * 1000, // 10 minutes  
      articleDetailMaxAge: 60 * 60 * 1000, // 1 hour
      digestMaxAge: 30 * 60 * 1000, // 30 minutes
      enableBackgroundSync: true,
      maxConcurrentSyncs: 3,
      ...config
    }

    console.log('DataManager: Initialized with config:', this.config)
    
    // Start periodic storage health checks
    this.initStorageHealthMonitoring()
  }

  // ===============================================
  // STORAGE HEALTH MONITORING
  // ===============================================

  private initStorageHealthMonitoring(): void {
    // Only run storage monitoring in browser environment
    if (typeof window === 'undefined') {
      console.log('DataManager: Skipping storage health monitoring - not in browser environment')
      return
    }
    
    // Check storage health every 10 minutes
    setInterval(async () => {
      try {
        const isHealthy = await storageManager.isStorageHealthy()
        if (!isHealthy) {
          console.warn('Storage is getting full, triggering cleanup')
          await storageManager.cleanupOldData()
        }
      } catch (error) {
        console.error('Storage health check failed:', error)
      }
    }, 10 * 60 * 1000) // 10 minutes

    // Initial health check
    storageManager.checkStorageHealth().then(health => {
      if (!health.isAvailable) {
        console.error('Storage not available:', health.lastError)
      }
    }).catch(error => {
      console.warn('Initial storage health check failed:', error)
    })
  }

  // Get storage information for debugging/monitoring
  async getStorageInfo() {
    if (typeof window === 'undefined') {
      return { isAvailable: false, lastError: 'Not in browser environment' }
    }
    return await storageManager.checkStorageHealth()
  }

  // Manual cleanup trigger
  async cleanupStorage() {
    if (typeof window === 'undefined') {
      console.warn('DataManager: Storage cleanup skipped - not in browser environment')
      return
    }
    return await storageManager.cleanupOldData()
  }

  // Clear user data on logout
  async clearUserData(userId: string) {
    if (typeof window === 'undefined') {
      console.warn('DataManager: Clear user data skipped - not in browser environment')
      return
    }
    return await storageManager.clearUserData(userId)
  }

  // ===============================================
  // USER PREFERENCES - LOCAL FIRST
  // ===============================================

  /**
   * Get user preferences - LOCAL FIRST, no automatic syncing
   * Returns local data immediately, optionally triggers background sync
   */
  async getUserPreferences(options: SyncOptions = {}): Promise<UserPreferences | null> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for preferences')
      return null
    }

    const userId = String(session.user.django_user_id)
    const { maxAge = this.config.userPreferencesMaxAge, backgroundSync = false } = options

    // STEP 1: Always check local storage first (NO API CALL)
    const localProfile = await localDB.getUserProfile(userId)
    
    // STEP 2: Determine if data is stale
    const isStale = !localProfile || 
      (options.forceRefresh === true) ||
      localDB.isStale(localProfile.lastSyncAt, maxAge)

    console.log(`DataManager: getUserPreferences - userId: ${userId}, isStale: ${isStale}, hasLocal: ${!!localProfile}`)

    // STEP 3: Return local data if fresh
    if (localProfile && !isStale) {
      return this.mapLocalProfileToUserPreferences(localProfile)
    }

    // STEP 4: If we have stale local data and backgroundSync is enabled, return stale + trigger sync
    if (localProfile && isStale && backgroundSync && this.config.enableBackgroundSync) {
      const preferences = this.mapLocalProfileToUserPreferences(localProfile)
      
      // Trigger background sync (non-blocking)
      this.queueBackgroundSync(`user-preferences:${userId}`, () => 
        this.syncUserPreferences(userId)
      )
      
      return preferences
    }

    // STEP 5: No local data OR explicit refresh OR no backgroundSync - sync immediately (blocking)
    try {
      console.log(`DataManager: No fresh local data available, syncing immediately`)
      await this.syncUserPreferences(userId)
      const updatedProfile = await localDB.getUserProfile(userId)
      return updatedProfile ? this.mapLocalProfileToUserPreferences(updatedProfile) : null
    } catch (error) {
      console.error('DataManager: Failed to sync user preferences:', error)
      // Fallback to stale local data if available
      return localProfile ? this.mapLocalProfileToUserPreferences(localProfile) : null
    }
  }

  /**
   * Sync user preferences from backend - EXPLICIT sync method
   * Called only when needed, never automatically
   */
  private async syncUserPreferences(userId: string): Promise<void> {
    const syncKey = `user-preferences:${userId}`
    
    // Prevent concurrent syncs of the same data
    if (this.activeSyncs.has(syncKey)) {
      console.log(`DataManager: Skipping concurrent sync for ${syncKey}`)
      return
    }

    this.activeSyncs.add(syncKey)
    
    try {
      console.log(`DataManager: Syncing user preferences for ${userId}`)
      
      // API call - explicit and controlled
      const preferences = await getUserPreferences()
      
      // Save to local storage
      await localDB.saveUserProfile({
        userId: String(preferences.user_id),
        publicId: preferences.public_id,
        email: preferences.email,
        name: preferences.name,
        hasCompletedOnboarding: preferences.has_completed_onboarding,
        topics: JSON.stringify(preferences.topics),
        topicsDetails: JSON.stringify(preferences.topics_details || []),
        regions: JSON.stringify(preferences.regions),
        languages: JSON.stringify(preferences.languages),
        publications: JSON.stringify(preferences.publications),
        lastSyncAt: new Date()
      })
      
      console.log(`DataManager: Successfully synced user preferences`)
    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  /**
   * Convert local profile to UserPreferences format
   */
  private mapLocalProfileToUserPreferences(profile: LocalUserProfile): UserPreferences {
    return {
      user_id: parseInt(profile.userId),
      public_id: profile.publicId,
      email: profile.email,
      name: profile.name,
      has_completed_onboarding: profile.hasCompletedOnboarding,
      topics: JSON.parse(profile.topics),
      topics_details: JSON.parse(profile.topicsDetails || '[]'),
      regions: JSON.parse(profile.regions),
      languages: JSON.parse(profile.languages),
      publications: JSON.parse(profile.publications)
    }
  }

  // ===============================================
  // FEED MANAGEMENT - LOCAL FIRST
  // ===============================================

  /**
   * Get feed data - LOCAL FIRST, no automatic syncing
   * Returns local data immediately, optionally triggers background sync
   */
  async getFeed(
    feedType: 'personalized' | 'world',
    topicSlug?: string,
    page: number = 1,
    pageSize: number = 10,
    options: SyncOptions = {}
  ): Promise<PaginatedResponse<LocalArticlePreview> | null> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for feed')
      return null
    }

    const userId = String(session.user.django_user_id)
    const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
    const { maxAge = this.config.feedMaxAge, backgroundSync = false } = options

    console.log(`DataManager: getFeed - ${feedType}, topic: ${normalizedTopicSlug}, page: ${page}`)

    // STEP 1: Get feed sync metadata (NO API CALL)
    const feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
    
    // STEP 2: Determine if data is stale
    const isStale = !feedSync || 
      (options.forceRefresh === true) ||
      feedSync.isStale ||
      localDB.isStale(feedSync.lastSyncAt, maxAge)

        // STEP 3: Simple page-by-page logic
    if (feedSync?.id) {
      const localResult = await this.getLocalFeedPage(feedSync.id, page, pageSize)
      
      console.log(`DataManager: Page ${page} check - localArticles: ${localResult.articles.length}, hasMore: ${feedSync.hasMore}, forceRefresh: ${options.forceRefresh}, isStale: ${isStale}`)
      
      // If we have the requested page locally AND not forcing refresh, return it immediately
      if (localResult.articles.length > 0 && !options.forceRefresh) {
        console.log(`DataManager: ⚡ INSTANT - Returning cached page ${page}`)
        return localResult
      }
      
      // If forceRefresh is true, skip cache and sync immediately
      if (options.forceRefresh && localResult.articles.length > 0) {
        console.log(`DataManager: 🔄 FORCE REFRESH - Skipping cache for page ${page}, syncing fresh data`)
      }
      
      // If we don't have this page but backend has more, fetch just this page
      if (localResult.articles.length === 0 && feedSync.hasMore) {
        console.log(`DataManager: 🔄 LOADING - Page ${page} not cached, fetching from backend...`)
        await this.fetchSinglePage(userId, feedType, page, normalizedTopicSlug, pageSize)
        const newResult = await this.getLocalFeedPage(feedSync.id, page, pageSize)
        console.log(`DataManager: ✅ LOADED - Page ${page} cached with ${newResult.articles.length} articles`)
        return newResult
      }
      
      // If we don't have this page and backend has no more, return empty
      if (localResult.articles.length === 0 && !feedSync.hasMore) {
        console.log(`DataManager: No more pages available - returning empty`)
        return {
          articles: [],
          pagination: {
            page,
            pageSize,
            totalPages: Math.ceil(localResult.pagination.totalItems / pageSize),
            totalItems: localResult.pagination.totalItems,
            hasNext: false,
            hasPrevious: page > 1
          }
        }
      }
    }

    // STEP 4: No local data OR explicit refresh OR no backgroundSync - sync immediately (blocking)
    try {
      console.log(`DataManager: No fresh feed data available, syncing immediately`)
      await this.syncFeed(userId, feedType, normalizedTopicSlug)
      const updatedFeedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
      if (updatedFeedSync?.id) {
        return await this.getLocalFeedPage(updatedFeedSync.id, page, pageSize)
      }
    } catch (error) {
      console.error('DataManager: Failed to sync feed:', error)
      // Fallback to local data if available
      if (feedSync?.id) {
        return await this.getLocalFeedPage(feedSync.id, page, pageSize)
      }
    }

    return null
  }

  /**
   * Get local feed page - pure local storage access
   */
  private async getLocalFeedPage(
    feedSyncId: number,
    page: number,
    pageSize: number
  ): Promise<PaginatedResponse<LocalArticlePreview>> {
    const { articles, totalCount } = await localDB.getFeedArticles(feedSyncId, page, pageSize)
    
    const localArticles = articles.map(article => this.mapLocalArticleToPreview(article))
    const totalPages = Math.ceil(totalCount / pageSize)

    // Get feed sync to check if backend has more data  
    const feedSync = await localDB.feedSyncs.where('id').equals(feedSyncId).first()
    const backendHasMore = feedSync?.hasMore || false

    // Simple logic: hasNext if we have more local pages OR backend has more
    const hasNext = (page < totalPages) || backendHasMore

    return {
      articles: localArticles,
      pagination: {
        page,
        pageSize,
        totalPages,
        totalItems: totalCount,
        hasNext,
        hasPrevious: page > 1
      }
    }
  }

  /**
   * Sync feed from backend - EXPLICIT sync method
   * Called only when needed, never automatically
   */
  private async syncFeed(
    userId: string,
    feedType: 'personalized' | 'world',
    topicSlug?: string
  ): Promise<void> {
    const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
    const syncKey = `feed:${feedType}:${normalizedTopicSlug}:${userId}`
    
    // Prevent concurrent syncs
    if (this.activeSyncs.has(syncKey)) {
      console.log(`DataManager: Skipping concurrent sync for ${syncKey}`)
      return
    }

    this.activeSyncs.add(syncKey)

    try {
      console.log(`DataManager: Syncing ${feedType} feed (topic: ${topicSlug || 'none'})`)

      // Mark sync in progress
      let feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
      if (!feedSync) {
        feedSync = await localDB.saveFeedSync({
          userId,
          feedType,
          topicSlug: normalizedTopicSlug,
          lastSyncAt: new Date(0),
          isStale: true,
          syncInProgress: true,
          lastPage: 1,
          hasMore: true,
          syncCount: 0,
          consecutiveErrors: 0
        })
      } else {
        await localDB.saveFeedSync({
          ...feedSync,
          syncInProgress: true,
          lastError: undefined
        })
      }

      // Simple sync: Fetch one page at a time
      console.log(`DataManager: Syncing single page for ${feedType} feed`)

      // API call - fetch one page only
      const params = { page: 1, page_size: 10 } as any
      if (normalizedTopicSlug) params.topic = normalizedTopicSlug

      const response = feedType === 'personalized'
        ? await getPersonalizedFeed(params)
        : await getWorldFeed(params)

      console.log(`DataManager: Got ${response.articles.length} articles, hasNext: ${response.pagination.hasNext}`)

      // Save articles to local storage
      const feedItemsToAdd = []
      for (let i = 0; i < response.articles.length; i++) {
        const article = response.articles[i]
        
        const articleId = await localDB.saveArticle({
          backendId: article.id,
          title: article.title,
          visualTitle: article.visualTitle,
          description: article.description,
          url: article.url,
          imageUrl: article.imageUrl,
          publishedAt: new Date(article.publishedAt),
          readTime: article.readTime,
          isTopHeadline: article.isTopHeadline,
          sourceName: article.source.name,
          sourceLogoUrl: article.source.logoUrl,
          topics: (article as any).topics ? JSON.stringify((article as any).topics) : undefined,
          isRead: false,
          isSaved: false,
          lastSyncAt: new Date()
        })

        feedItemsToAdd.push({
          feedSyncId: feedSync.id!,
          articleId,
          position: i,
          addedAt: new Date()
        })
      }

      // Replace feed items (for page 1) 
      await localDB.replaceFeedItems(feedSync.id!, feedItemsToAdd)

      // Update feed sync status
      await localDB.saveFeedSync({
        ...feedSync,
        lastSyncAt: new Date(),
        syncInProgress: false,
        isStale: false,
        hasMore: response.pagination.hasNext,
        totalItems: response.pagination.totalItems,
        syncCount: feedSync.syncCount + 1,
        consecutiveErrors: 0,
        lastPage: 1
      })

      console.log(`DataManager: Successfully synced ${response.articles.length} articles`)
    } catch (error) {
      console.error('DataManager: Feed sync failed:', error)
      
      // Update error status
      const feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
      if (feedSync) {
        await localDB.saveFeedSync({
          ...feedSync,
          syncInProgress: false,
          lastError: error instanceof Error ? error.message : 'Unknown error',
          consecutiveErrors: feedSync.consecutiveErrors + 1
        })
      }
      
      throw error
    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  /**
   * Background sync for feeds - detects new articles without auto-inserting them
   * Returns info about pending articles for user-controlled loading
   */
  async backgroundSyncFeed(
    userId: string,
    feedType: 'personalized' | 'world',
    topicSlug?: string
  ): Promise<{ newArticlesCount: number; updatedArticlesCount: number } | null> {
    const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
    const syncKey = `background-feed:${feedType}:${normalizedTopicSlug}:${userId}`
    
    // Prevent concurrent syncs
    if (this.activeSyncs.has(syncKey)) {
      console.log(`DataManager: Skipping concurrent background sync for ${syncKey}`)
      return null
    }

    this.activeSyncs.add(syncKey)

    try {
      console.log(`DataManager: Background syncing ${feedType} feed (preserving cache)`)

      const feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
      if (!feedSync) {
        console.log(`DataManager: No existing feed sync found, falling back to full sync`)
        await this.syncFeed(userId, feedType, topicSlug)
        return { newArticlesCount: 0, updatedArticlesCount: 0 }
      }

      // Get the latest article timestamp to check for newer content efficiently
      const latestArticles = await localDB.feedItems
        .where('feedSyncId')
        .equals(feedSync.id!)
        .toArray()
      
      // Find the most recent article's published date
      let latestTimestamp: string | undefined
      if (latestArticles.length > 0) {
        // Get the article IDs and find their published dates
        const articleIds = latestArticles.map(item => item.articleId)
        const articles = await localDB.articles
          .where('id')
          .anyOf(articleIds)
          .toArray()
        
        if (articles.length > 0) {
          const mostRecent = articles.reduce((latest, current) => 
            current.publishedAt > latest.publishedAt ? current : latest
          )
          latestTimestamp = mostRecent.publishedAt.toISOString()
          console.log(`DataManager: Checking for articles newer than ${latestTimestamp}`)
        }
      }

      // First, efficiently check if there are any new articles using count_only
      const countParams = { 
        count_only: true,
        ...(latestTimestamp && { since: latestTimestamp }),
        ...(normalizedTopicSlug && { topic: normalizedTopicSlug })
      }

      const countResponse = feedType === 'personalized'
        ? await getPersonalizedFeed(countParams)
        : await getWorldFeed(countParams)

      const newArticlesAvailable = countResponse.new_articles_count || 0
      console.log(`DataManager: Found ${newArticlesAvailable} new articles available`)

      if (newArticlesAvailable === 0) {
        console.log(`DataManager: No new articles found, clearing any stale pending data`)
        
        // CRITICAL: Clear any existing pending data since backend confirms no new articles
        if (feedSync?.pendingNewArticles || feedSync?.pendingUpdatedArticles) {
          console.log(`DataManager: Clearing stale pending counts: ${feedSync.pendingNewArticles || 0} new, ${feedSync.pendingUpdatedArticles || 0} updated`)
          
          await localDB.saveFeedSync({
            ...feedSync,
            lastSyncAt: new Date(),
            isStale: false,
            pendingNewArticles: 0,
            pendingUpdatedArticles: 0,
            pendingArticlesData: undefined,
            syncCount: feedSync.syncCount + 1,
            consecutiveErrors: 0
          })
          
          // Clear from memory too
          this.pendingArticlesStore.delete(feedSync.id!)
        }
        
        return { newArticlesCount: 0, updatedArticlesCount: 0 }
      }

      // If new articles exist, fetch them efficiently
      const fetchParams = { 
        page: 1, 
        page_size: Math.min(newArticlesAvailable, 20), // Limit to reasonable batch size
        ...(latestTimestamp && { since: latestTimestamp }),
        ...(normalizedTopicSlug && { topic: normalizedTopicSlug })
      }

      const response = feedType === 'personalized'
        ? await getPersonalizedFeed(fetchParams)
        : await getWorldFeed(fetchParams)

      console.log(`DataManager: Background sync got ${response.articles.length} fresh articles (${response.new_articles_count} detected)`)

      // Save/update articles in local storage
      const feedItemsToUpdate = []
      for (let i = 0; i < response.articles.length; i++) {
        const article = response.articles[i]
        
        const articleId = await localDB.saveArticle({
          backendId: article.id,
          title: article.title,
          visualTitle: article.visualTitle,
          description: article.description,
          url: article.url,
          imageUrl: article.imageUrl,
          publishedAt: new Date(article.publishedAt),
          readTime: article.readTime,
          isTopHeadline: article.isTopHeadline,
          sourceName: article.source.name,
          sourceLogoUrl: article.source.logoUrl,
          topics: (article as any).topics ? JSON.stringify((article as any).topics) : undefined,
          isRead: false,
          isSaved: false,
          lastSyncAt: new Date()
        })

        feedItemsToUpdate.push({
          feedSyncId: feedSync.id!,
          articleId,
          position: i,
          addedAt: new Date()
        })
      }

      // Detect new articles without inserting them (user-controlled loading)
      const detectionResult = await localDB.detectNewArticles(feedSync.id!, feedItemsToUpdate)

      // Store pending articles info for user notification (include data for persistence)
      const pendingArticlesData = JSON.stringify({
        newArticles: detectionResult.newArticles,
        updatedArticles: detectionResult.updatedArticles
      })
      
      await localDB.saveFeedSync({
        ...feedSync,
        lastSyncAt: new Date(),
        isStale: false,
        hasMore: response.pagination.hasNext,
        totalItems: response.pagination.totalItems,
        syncCount: feedSync.syncCount + 1,
        consecutiveErrors: 0,
        pendingNewArticles: detectionResult.newArticlesCount,
        pendingUpdatedArticles: detectionResult.updatedArticlesCount,
        pendingArticlesData: pendingArticlesData
      })

      // Store the actual pending articles data temporarily (we'll need a better storage solution)
      console.log(`DataManager: Background sync completed - detected ${detectionResult.newArticlesCount} new articles, ${detectionResult.updatedArticlesCount} updated articles (waiting for user to load)`)
      
      // Store pending articles data for later insertion (persist to IndexedDB)
      await this.storePendingArticles(feedSync.id!, detectionResult.newArticles, detectionResult.updatedArticles)
      
      return { 
        newArticlesCount: detectionResult.newArticlesCount, 
        updatedArticlesCount: detectionResult.updatedArticlesCount 
      }
      
    } catch (error) {
      console.error('DataManager: Background feed sync failed:', error)
      
      // Update error status
      const feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
      if (feedSync) {
        await localDB.saveFeedSync({
          ...feedSync,
          lastError: error instanceof Error ? error.message : 'Unknown error',
          consecutiveErrors: feedSync.consecutiveErrors + 1
        })
      }
      
      throw error
    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  /**
   * Get public world feed for unauthenticated users - no caching, direct API call
   */
  async getPublicFeed(
    topicSlug?: string,
    page: number = 1,
    pageSize: number = 10
  ): Promise<PaginatedResponse<LocalArticlePreview> | null> {
    const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
    
    console.log(`DataManager: getPublicFeed - topic: ${normalizedTopicSlug}, page: ${page}`)

    try {
      // Call the public API directly (no auth required)
      const params = { page, page_size: pageSize } as any
      if (normalizedTopicSlug) params.topic = normalizedTopicSlug

      const response = await getPublicWorldFeed(params)
      
      console.log(`DataManager: Got ${response.articles.length} public articles`)

      // Convert articles to LocalArticlePreview format (no caching, no auth state)
      const localArticles: LocalArticlePreview[] = response.articles.map(article => ({
        ...article,
        isRead: false,
        isSaved: false,
        topics: (article as any).topics || []
      }))

      return {
        articles: localArticles,
        pagination: response.pagination
      }
    } catch (error) {
      console.error('DataManager: Public feed fetch failed:', error)
      return null
    }
  }

  // Temporary storage for pending articles (until user loads them)
  private pendingArticlesStore = new Map<number, {
    newArticles: any[];
    updatedArticles: any[];
  }>()

  /**
   * Store pending articles data for later insertion when user chooses to load them
   */
  private async storePendingArticles(feedSyncId: number, newArticles: any[], updatedArticles: any[]): Promise<void> {
    // Keep in-memory store for immediate access (fallback)
    this.pendingArticlesStore.set(feedSyncId, {
      newArticles,
      updatedArticles
    })
    console.log(`DataManager: Stored ${newArticles.length} new and ${updatedArticles.length} updated articles for feedSyncId ${feedSyncId} (persisted to IndexedDB)`)
  }

  /**
   * Load pending articles into the feed when user clicks the notification
   */
  async loadPendingArticles(feedSyncId: number): Promise<void> {
    console.log(`🔄 DataManager: loadPendingArticles called for feedSyncId ${feedSyncId}`)
    
    // Try to get from in-memory store first
    let pendingData = this.pendingArticlesStore.get(feedSyncId)
    console.log(`DataManager: In-memory store has data:`, !!pendingData)
    
    // If not in memory, try to get from IndexedDB (for page refreshes)
    if (!pendingData) {
      const feedSync = await localDB.feedSyncs.where('id').equals(feedSyncId).first()
      console.log(`DataManager: FeedSync from DB:`, feedSync ? { id: feedSync.id, topicSlug: feedSync.topicSlug, hasPendingData: !!feedSync.pendingArticlesData } : 'none')
      
      if (feedSync?.pendingArticlesData) {
        try {
          pendingData = JSON.parse(feedSync.pendingArticlesData)
          console.log(`DataManager: Restored pending articles from IndexedDB for feedSyncId ${feedSyncId}`)
        } catch (error) {
          console.error('DataManager: Failed to parse pending articles data:', error)
        }
      }
    }
    
    if (!pendingData) {
      console.warn(`DataManager: No pending articles found for feedSyncId ${feedSyncId}`)
      return
    }
    
    console.log(`DataManager: Pending data found:`, { 
      newArticles: pendingData.newArticles?.length || 0, 
      updatedArticles: pendingData.updatedArticles?.length || 0 
    })

    // FINAL SAFEGUARD: Check if this data is stale before proceeding
    const feedSyncForValidation = await localDB.feedSyncs.where('id').equals(feedSyncId).first()
    if (feedSyncForValidation?.lastSyncAt) {
      const now = new Date()
      const staleThresholdMs = 15 * 60 * 1000 // 15 minutes
      const isStale = (now.getTime() - feedSyncForValidation.lastSyncAt.getTime()) > staleThresholdMs
      
      if (isStale) {
        console.warn(`DataManager: Aborting loadPendingArticles - data is stale (${Math.round((now.getTime() - feedSyncForValidation.lastSyncAt.getTime()) / 60000)} min old)`)
        
        // Clear the stale data
        await localDB.saveFeedSync({
          ...feedSyncForValidation,
          pendingNewArticles: 0,
          pendingUpdatedArticles: 0,
          pendingArticlesData: undefined
        })
        
        this.pendingArticlesStore.delete(feedSyncId)
        return
      }
    }

    try {
      // Get the feedSync to check if we need topic filtering
      const feedSync = await localDB.feedSyncs.where('id').equals(feedSyncId).first()
      
      let filteredNewArticles = pendingData.newArticles
      let filteredUpdatedArticles = pendingData.updatedArticles
      
      // If this is a topic-specific feed, filter articles by topic
      // This handles both scenarios:
      // 1. Home feed: User follows Tech+Business+Science, viewing Tech tab → filter to Tech only  
      // 2. World feed: All topics available, viewing Tech tab → filter to Tech only
      if (feedSync?.topicSlug) {
        console.log(`DataManager: Filtering pending articles for topic "${feedSync.topicSlug}"`)
        
        const filterByTopic = (articles: any[]) => {
          return articles.filter((item: any) => {
            // Get the article to check its topics
            const articleId = item.articleId
            return localDB.articles.where('id').equals(articleId).first().then(article => {
              if (!article?.topics) return false
              
              try {
                const articleTopics = JSON.parse(article.topics)
                return articleTopics.some((topic: any) => topic.slug === feedSync.topicSlug)
              } catch (error) {
                console.error('DataManager: Failed to parse article topics:', error)
                return false
              }
            })
          })
        }
        
        // Filter both new and updated articles by topic
        filteredNewArticles = await Promise.all(filteredNewArticles.map(async (item: any) => {
          const articleId = item.articleId
          const article = await localDB.articles.where('id').equals(articleId).first()
          if (!article?.topics) return null
          
          try {
            const articleTopics = JSON.parse(article.topics)
            const matchesTopic = articleTopics.some((topic: any) => topic.slug === feedSync.topicSlug)
            return matchesTopic ? item : null
          } catch (error) {
            console.error('DataManager: Failed to parse article topics:', error)
            return null
          }
        })).then(results => results.filter(item => item !== null))
        
        filteredUpdatedArticles = await Promise.all(filteredUpdatedArticles.map(async (item: any) => {
          const articleId = item.articleId  
          const article = await localDB.articles.where('id').equals(articleId).first()
          if (!article?.topics) return null
          
          try {
            const articleTopics = JSON.parse(article.topics)
            const matchesTopic = articleTopics.some((topic: any) => topic.slug === feedSync.topicSlug)
            return matchesTopic ? item : null
          } catch (error) {
            console.error('DataManager: Failed to parse article topics:', error)
            return null
          }
        })).then(results => results.filter(item => item !== null))
        
        console.log(`DataManager: Filtered ${pendingData.newArticles.length} → ${filteredNewArticles.length} new articles, ${pendingData.updatedArticles.length} → ${filteredUpdatedArticles.length} updated articles for topic "${feedSync.topicSlug}"`)
      }
      
      // Insert the (possibly filtered) pending articles
      await localDB.insertPendingArticles(feedSyncId, filteredNewArticles, filteredUpdatedArticles)
      
      // Clear pending data from feed sync
      const currentFeedSync = await localDB.feedSyncs.where('id').equals(feedSyncId).first()
      if (currentFeedSync) {
        await localDB.saveFeedSync({
          ...currentFeedSync,
          pendingNewArticles: 0,
          pendingUpdatedArticles: 0,
          pendingArticlesData: undefined // Clear the persisted data
        })
      }
      
      // Remove from in-memory storage
      this.pendingArticlesStore.delete(feedSyncId)
      
      console.log(`✅ DataManager: Successfully loaded ${filteredNewArticles.length} new and ${filteredUpdatedArticles.length} updated articles (filtered by topic: ${feedSync?.topicSlug || 'none'})`)
      console.log(`DataManager: Clearing pending counts and data from feedSyncId ${feedSyncId}`)
      
    } catch (error) {
      console.error('DataManager: Failed to load pending articles:', error)
      throw error
    }
  }

  /**
   * Get pending articles count for a specific feed
   */
  async getPendingArticlesCount(userId: string, feedType: 'personalized' | 'world', topicSlug?: string): Promise<{ newArticlesCount: number; updatedArticlesCount: number }> {
    const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
    
    // First, try to get topic-specific feed sync
    let feedSync = await localDB.getFeedSync(userId, feedType, normalizedTopicSlug)
    
    // If no topic-specific pending articles, fall back to general feed
    // Background sync creates general feeds that contain:
    // - Personalized: Articles from user's followed topics (filtered by preferences)
    // - World: Articles from all topics (filtered by user's regions only)
    // When user views a specific topic tab, we filter these general feed articles by topic
    if ((!feedSync?.pendingNewArticles && !feedSync?.pendingUpdatedArticles) && normalizedTopicSlug) {
      console.log(`DataManager: No pending articles for topic "${normalizedTopicSlug}", checking general feed`)
      const generalFeedSync = await localDB.getFeedSync(userId, feedType, undefined)
      if (generalFeedSync?.pendingNewArticles || generalFeedSync?.pendingUpdatedArticles) {
        feedSync = generalFeedSync
        console.log(`DataManager: Found ${generalFeedSync.pendingNewArticles || 0} new articles in general feed for topic-specific request`)
      }
    }
    
    // CRITICAL: Validate that pending data is not stale
    if (feedSync?.pendingNewArticles || feedSync?.pendingUpdatedArticles) {
      const now = new Date()
      const staleThresholdMs = 15 * 60 * 1000 // 15 minutes
      const isStale = feedSync.lastSyncAt && (now.getTime() - feedSync.lastSyncAt.getTime()) > staleThresholdMs
      
      if (isStale) {
        console.warn(`DataManager: Pending articles are stale (${Math.round((now.getTime() - feedSync.lastSyncAt.getTime()) / 60000)} min old), clearing them`)
        
        // Clear stale pending data
        await localDB.saveFeedSync({
          ...feedSync,
          pendingNewArticles: 0,
          pendingUpdatedArticles: 0,
          pendingArticlesData: undefined
        })
        
        // Clear from memory too
        if (feedSync.id) {
          this.pendingArticlesStore.delete(feedSync.id)
        }
        
        return { newArticlesCount: 0, updatedArticlesCount: 0 }
      }
    }
    
    const result = {
      newArticlesCount: feedSync?.pendingNewArticles || 0,
      updatedArticlesCount: feedSync?.pendingUpdatedArticles || 0
    }
    
    console.log(`DataManager: getPendingArticlesCount for ${feedType}:${normalizedTopicSlug || 'general'} = ${result.newArticlesCount} new, ${result.updatedArticlesCount} updated`)
    console.log(`DataManager: FeedSync used:`, feedSync ? { id: feedSync.id, topicSlug: feedSync.topicSlug, pendingData: !!feedSync.pendingArticlesData, lastSync: feedSync.lastSyncAt } : 'none')
    
    return result
  }

  /**
   * Fetch a single specific page and append it to existing feed
   */
  private async fetchSinglePage(
    userId: string,
    feedType: 'personalized' | 'world',
    page: number,
    topicSlug?: string,
    pageSize: number = 10
  ): Promise<void> {
    const syncKey = `single-page:${feedType}:${topicSlug}:${userId}:${page}`
    
    // Prevent concurrent fetches of the same page
    if (this.activeSyncs.has(syncKey)) {
      console.log(`DataManager: Skipping concurrent fetch for page ${page}`)
      return
    }

    this.activeSyncs.add(syncKey)

    try {
      const feedSync = await localDB.getFeedSync(userId, feedType, topicSlug)
      if (!feedSync?.id) {
        throw new Error('No feed sync found - cannot fetch page')
      }

      console.log(`DataManager: Fetching page ${page} for ${feedType} feed`)
      
      const params = { page, page_size: pageSize } as any
      if (topicSlug) params.topic = topicSlug

      const response = feedType === 'personalized'
        ? await getPersonalizedFeed(params)
        : await getWorldFeed(params)

      if (response.articles.length === 0) {
        console.log(`DataManager: No articles returned for page ${page} - marking as no more`)
        await localDB.saveFeedSync({
          ...feedSync,
          hasMore: false,
          lastSyncAt: new Date()
        })
        return
      }

      // Save new articles and append to feed
      const currentCount = await localDB.feedItems.where('feedSyncId').equals(feedSync.id).count()
      
      console.log(`DataManager: fetchSinglePage - currentCount: ${currentCount}, adding ${response.articles.length} articles at positions ${currentCount} to ${currentCount + response.articles.length - 1}`)
      
      for (let i = 0; i < response.articles.length; i++) {
        const article = response.articles[i]
        
        const articleId = await localDB.saveArticle({
          backendId: article.id,
          title: article.title,
          visualTitle: article.visualTitle,
          description: article.description,
          url: article.url,
          imageUrl: article.imageUrl,
          publishedAt: new Date(article.publishedAt),
          readTime: article.readTime,
          isTopHeadline: article.isTopHeadline,
          sourceName: article.source.name,
          sourceLogoUrl: article.source.logoUrl,
          topics: (article as any).topics ? JSON.stringify((article as any).topics) : undefined,
          isRead: false,
          isSaved: false,
          lastSyncAt: new Date()
        })

        const position = currentCount + i
        console.log(`DataManager: Adding article ${i+1}/${response.articles.length} at position ${position}`)

        // Append to existing feed items
        await localDB.feedItems.add({
          feedSyncId: feedSync.id,
          articleId,
          position,
          addedAt: new Date()
        })
      }

      // Update feed sync metadata
      await localDB.saveFeedSync({
        ...feedSync,
        lastSyncAt: new Date(),
        hasMore: response.pagination.hasNext,
        totalItems: Math.max(feedSync.totalItems || 0, response.pagination.totalItems || 0),
        lastPage: page
      })

      console.log(`DataManager: 💾 CACHED page ${page} with ${response.articles.length} articles`)

    } catch (error) {
      console.error(`DataManager: Failed to fetch page ${page}:`, error)
      throw error
    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  /**
   * Load additional pages for existing feed - EXPLICIT pagination method  
   * @deprecated Use fetchSinglePage instead
   */
  private async loadMoreFeed(
    userId: string,
    feedType: 'personalized' | 'world',
    topicSlug?: string,
    targetPage: number = 2,
    pageSize: number = 10
  ): Promise<void> {
    const syncKey = `feed-more:${feedType}:${topicSlug}:${userId}:${targetPage}`
    
    // Prevent concurrent page loads
    if (this.activeSyncs.has(syncKey)) {
      console.log(`DataManager: Skipping concurrent page load for ${syncKey}`)
      return
    }

    this.activeSyncs.add(syncKey)

    try {
      const feedSync = await localDB.getFeedSync(userId, feedType, topicSlug)
      if (!feedSync?.id) {
        throw new Error('No feed sync found - cannot load more pages')
      }

      // Check if we already have enough pages
      const currentArticleCount = await localDB.getFeedArticles(feedSync.id, 1, targetPage * pageSize)
      if (currentArticleCount.articles.length >= targetPage * pageSize) {
        console.log(`DataManager: Already have page ${targetPage} data`)
        return
      }

      console.log(`DataManager: Fetching additional pages for ${feedType} feed (target page: ${targetPage})`)

      // Calculate current state and how many pages to fetch
      const currentPageCount = Math.ceil(currentArticleCount.totalCount / pageSize)
      const batchSize = 5 // Fetch 5 pages at a time for smooth UX
      
      console.log(`DataManager: loadMoreFeed debug:`, {
        targetPage,
        currentArticleCount: currentArticleCount.totalCount,
        currentPageCount,
        feedSyncHasMore: feedSync.hasMore,
        batchSize
      })
      
      // Simple check: if we don't have the target page, fetch what we need
      if (targetPage <= currentPageCount) {
        console.log(`DataManager: Target page ${targetPage} already available (have ${currentPageCount} pages) - aborting`)
        return
      }
      
      // Calculate what pages to fetch
      const startPage = currentPageCount + 1
      const endPage = Math.max(targetPage, startPage + 3) // Fetch at least 4 pages or up to targetPage
      
      console.log(`DataManager: Need page ${targetPage}, have ${currentPageCount} pages - fetching pages ${startPage} to ${endPage}`)

      for (let fetchPage = startPage; fetchPage <= endPage; fetchPage++) {
        
        console.log(`DataManager: Fetching page ${fetchPage} for ${feedType} feed`)
        
        const params = { page: fetchPage, page_size: pageSize } as any
        if (topicSlug) params.topic = topicSlug

        const response = feedType === 'personalized'
          ? await getPersonalizedFeed(params)
          : await getWorldFeed(params)

        if (response.articles.length === 0) {
          console.log(`DataManager: No more articles available (page ${fetchPage})`)
          // Update hasMore flag
          await localDB.saveFeedSync({
            ...feedSync,
            hasMore: false,
            lastSyncAt: new Date()
          })
          break
        }

        // Save new articles to local storage
        const feedItemsToAdd = []
        const basePosition = currentArticleCount.totalCount

        for (let j = 0; j < response.articles.length; j++) {
          const article = response.articles[j]
          
          const articleId = await localDB.saveArticle({
            backendId: article.id,
            title: article.title,
            visualTitle: article.visualTitle,
            description: article.description,
            url: article.url,
            imageUrl: article.imageUrl,
            publishedAt: new Date(article.publishedAt),
            readTime: article.readTime,
            isTopHeadline: article.isTopHeadline,
            sourceName: article.source.name,
            sourceLogoUrl: article.source.logoUrl,
            topics: (article as any).topics ? JSON.stringify((article as any).topics) : undefined,
            isRead: false,
            isSaved: false,
            lastSyncAt: new Date()
          })

          feedItemsToAdd.push({
            feedSyncId: feedSync.id,
            articleId,
            position: basePosition + j,
            addedAt: new Date()
          })
        }

        // Add new feed items (append, don't replace)
        for (const feedItem of feedItemsToAdd) {
          await localDB.feedItems.add(feedItem)
        }

        console.log(`DataManager: 💾 CACHED ${response.articles.length} articles from page ${fetchPage} - now available for instant access!`)

        // Update our reference for next iteration
        currentArticleCount.totalCount += response.articles.length

        // If this page didn't return a full page, we've reached the end
        if (response.articles.length < pageSize || !response.pagination.hasNext) {
          console.log(`DataManager: Reached end of feed at page ${fetchPage}`)
          await localDB.saveFeedSync({
            ...feedSync,
            lastSyncAt: new Date(),
            hasMore: false,
            totalItems: Math.max(feedSync.totalItems || 0, response.pagination.totalItems || 0),
            lastPage: fetchPage
          })
          break
        }
      }

      // Update feed sync metadata after batch completion
      await localDB.saveFeedSync({
        ...feedSync,
        lastSyncAt: new Date(),
        totalItems: Math.max(feedSync.totalItems || 0, currentArticleCount.totalCount),
        lastPage: endPage
      })

      console.log(`DataManager: Batch complete - fetched pages ${startPage} to ${endPage}`)

    } catch (error) {
      console.error('DataManager: Failed to load more feed pages:', error)
      throw error
    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  /**
   * Convert local article to preview format
   */
  private mapLocalArticleToPreview(article: LocalArticle): LocalArticlePreview {
    return {
      id: article.backendId,
      title: article.title,
      visualTitle: article.visualTitle,
      description: article.description,
      source: {
        name: article.sourceName,
        logoUrl: article.sourceLogoUrl
      },
      publishedAt: article.publishedAt.toISOString(),
      imageUrl: article.imageUrl,
      url: article.url,
      isTopHeadline: article.isTopHeadline,
      readTime: article.readTime,
      isRead: article.isRead,
      isSaved: article.isSaved,
      readAt: article.readAt,
      savedAt: article.savedAt,
      topics: article.topics ? JSON.parse(article.topics) : undefined
    }
  }

  // ===============================================
  // ARTICLE DETAIL - LOCAL FIRST
  // ===============================================

  /**
   * Get article detail - LOCAL FIRST, same pattern as feeds
   */
  async getArticleDetail(articleId: string, options: SyncOptions = {}): Promise<ArticleDetail | null> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for article detail')
      return null
    }

    const { maxAge = this.config.articleDetailMaxAge, backgroundSync = false } = options

    // STEP 1: Check local storage first (by backend ID)
    const localArticle = await localDB.getArticleByBackendId(articleId)
    const isStale = !localArticle ||
      (options.forceRefresh === true) ||
      localDB.isStale(localArticle.lastSyncAt, maxAge) ||
      !localArticle.content // No content cached yet

    console.log(`DataManager: getArticleDetail - articleId: ${articleId}, hasLocal: ${!!localArticle}, hasContent: ${!!localArticle?.content}, isStale: ${isStale}`)

    // STEP 2: If we have fresh article content, return immediately
    if (localArticle?.content && !isStale) {
      console.log(`DataManager: ⚡ INSTANT - Returning cached article content`)
      return this.mapLocalArticleToDetail(localArticle)
    }

    // STEP 3: If stale but have content and background sync enabled, return stale + refresh
    if (localArticle?.content && isStale && backgroundSync && this.config.enableBackgroundSync) {
      console.log(`DataManager: Returning stale article content and triggering background sync`)
      this.queueBackgroundSync(`article-detail:${articleId}`, () =>
        this.syncArticleDetail(articleId)
      )
      return this.mapLocalArticleToDetail(localArticle)
    }

    // STEP 4: No content or explicit refresh - sync immediately (blocking)
    try {
      console.log(`DataManager: No fresh article content available, syncing immediately`)
      await this.syncArticleDetail(articleId)
      const updatedArticle = await localDB.getArticleByBackendId(articleId)
      if (updatedArticle) {
        return this.mapLocalArticleToDetail(updatedArticle)
      }
    } catch (error) {
      console.error('DataManager: Failed to sync article detail:', error)
      // Fallback to local data if available
      if (localArticle) {
        return this.mapLocalArticleToDetail(localArticle)
      }
    }

    return null
  }

  /**
   * Sync article detail from backend - fetches full content
   */
  private async syncArticleDetail(articleId: string): Promise<void> {
    const syncKey = `article-detail:${articleId}`

    // Prevent concurrent syncs of the same article
    if (this.activeSyncs.has(syncKey)) {
      console.log(`DataManager: Skipping concurrent sync for article ${articleId}`)
      return
    }

    this.activeSyncs.add(syncKey)

    try {
      console.log(`DataManager: Syncing article detail for ${articleId}`)

      // Fetch full article detail from backend
      const articleDetail = await getArticleDetail(articleId)

      // Get existing article to preserve read/saved status
      const existingArticle = await localDB.getArticleByBackendId(articleDetail.id)

      // Save/update article with full content
      await localDB.saveArticle({
        backendId: articleDetail.id,
        title: articleDetail.title,
        visualTitle: articleDetail.visualTitle,
        description: articleDetail.description,
        content: articleDetail.content, // Full content
        url: articleDetail.url,
        imageUrl: articleDetail.imageUrl,
        publishedAt: new Date(articleDetail.publishedAt),
        readTime: articleDetail.readTime,
        isTopHeadline: articleDetail.isTopHeadline,
        sourceName: articleDetail.source.name,
        sourceLogoUrl: articleDetail.source.logoUrl,
        summary: articleDetail.summary ? JSON.stringify(articleDetail.summary) : undefined,
        richContent: articleDetail.richContent ? JSON.stringify(articleDetail.richContent) : undefined,
        contentStatus: articleDetail.contentStatus,
        topics: articleDetail.topics ? JSON.stringify(articleDetail.topics) : undefined,
        // Preserve existing read/saved status or default to false
        isRead: existingArticle?.isRead ?? false,
        isSaved: existingArticle?.isSaved ?? false,
        lastSyncAt: new Date()
      })

      console.log(`DataManager: Successfully synced article detail for ${articleId}`)

    } catch (error) {
      console.error(`DataManager: Failed to sync article detail for ${articleId}:`, error)
      throw error
    } finally {
      this.activeSyncs.delete(syncKey)
    }
  }

  /**
   * Map local article to ArticleDetail format
   */
  private mapLocalArticleToDetail(localArticle: LocalArticle): ArticleDetail {
    return {
      id: localArticle.backendId,
      title: localArticle.title,
      visualTitle: localArticle.visualTitle,
      description: localArticle.description,
      content: localArticle.content || '',
      url: localArticle.url,
      imageUrl: localArticle.imageUrl,
      publishedAt: localArticle.publishedAt.toISOString(),
      readTime: localArticle.readTime,
      isTopHeadline: localArticle.isTopHeadline,
      source: {
        name: localArticle.sourceName,
        logoUrl: localArticle.sourceLogoUrl
      },
      summary: localArticle.summary ? JSON.parse(localArticle.summary) : undefined,
      richContent: localArticle.richContent ? JSON.parse(localArticle.richContent) : undefined,
      contentStatus: localArticle.contentStatus,
      topics: localArticle.topics ? JSON.parse(localArticle.topics) : undefined
    }
  }

  // ===============================================
  // DIGEST OPERATIONS - LOCAL FIRST
  // ===============================================

  /**
   * Get latest digest - LOCAL FIRST with background sync
   */
  async getLatestDigest(options: SyncOptions = {}): Promise<{ digest: Digest | null; message?: string }> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for digest')
      return { digest: null, message: 'Not authenticated' }
    }

    const userId = session.user.django_user_id.toString()
    const { maxAge = this.config.digestMaxAge, backgroundSync = false } = options

    // STEP 1: Check local storage first
    const localDigest = await localDB.getLatestDigest(userId)
    const digestSync = await localDB.getDigestSync(userId)
    
    const isStale = !localDigest || 
      (Date.now() - digestSync.lastSyncAt.getTime()) > maxAge

    console.log(`DataManager: getLatestDigest - hasLocal: ${!!localDigest}, isStale: ${isStale}`)

    // STEP 2: Return local data immediately if not stale or if background sync is preferred
    if (localDigest && (!isStale || backgroundSync)) {
      const apiDigest = localDB.convertLocalDigestToApi(localDigest)
      
      // Queue background sync if stale
      if (isStale && backgroundSync) {
        this.queueBackgroundSync(`digest-latest:${userId}`, async () => {
          await this.syncLatestDigest(userId)
        })
      }
      
      return { digest: apiDigest }
    }

    // STEP 3: No fresh local data available, sync immediately
    console.log('DataManager: No fresh local digest data available, syncing immediately')
    return await this.syncLatestDigest(userId)
  }

  /**
   * Get digest by date - LOCAL FIRST with fallback sync
   */
  async getDigestByDate(date: string, options: SyncOptions = {}): Promise<{ digest: Digest | null; date: string; message?: string }> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for digest by date')
      return { digest: null, date, message: 'Not authenticated' }
    }

    const userId = session.user.django_user_id.toString()
    const { maxAge = this.config.digestMaxAge } = options

    // STEP 1: Check local storage first
    const localDigest = await localDB.getDigestByDate(userId, date)
    const isStale = !localDigest || 
      (Date.now() - localDigest.lastSyncAt.getTime()) > maxAge

    console.log(`DataManager: getDigestByDate(${date}) - hasLocal: ${!!localDigest}, isStale: ${isStale}`)

    // STEP 2: Return local data if fresh enough
    if (localDigest && !isStale) {
      const apiDigest = localDB.convertLocalDigestToApi(localDigest)
      return { digest: apiDigest, date }
    }

    // STEP 3: Sync from backend
    console.log(`DataManager: Syncing digest for date ${date}`)
    try {
      const response = await digestService.getDigestByDate(date)
      
      if (response.digest) {
        // Store in local database
        await localDB.storeDigest(userId, response.digest)
        console.log(`DataManager: Successfully synced digest for ${date}`)
      }
      
      return response
    } catch (error) {
      console.error(`DataManager: Failed to sync digest for ${date}:`, error)
      
      // Return stale local data if available
      if (localDigest) {
        console.log('DataManager: Returning stale local digest due to sync failure')
        const apiDigest = localDB.convertLocalDigestToApi(localDigest)
        return { digest: apiDigest, date }
      }
      
      throw error
    }
  }

  /**
   * List digests - LOCAL FIRST with pagination
   */
  async listDigests(page: number = 1, pageSize: number = 10, options: SyncOptions = {}): Promise<any> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for digest list')
      return { digests: [], pagination: { page, page_size: pageSize, total_pages: 0, total_count: 0, has_next: false, has_previous: false } }
    }

    const userId = session.user.django_user_id.toString()
    const { maxAge = this.config.digestMaxAge, backgroundSync = false } = options

    // STEP 1: Check local storage first
    const localResult = await localDB.listDigests(userId, page, pageSize)
    const digestSync = await localDB.getDigestSync(userId)
    
    const isStale = (Date.now() - digestSync.lastSyncAt.getTime()) > maxAge

    console.log(`DataManager: listDigests - hasLocal: ${localResult.digests.length > 0}, isStale: ${isStale}`)

    // STEP 2: Return local data if not stale or if background sync preferred
    if (localResult.digests.length > 0 && (!isStale || backgroundSync)) {
      const apiDigests = localResult.digests.map(d => localDB.convertLocalDigestToApi(d))
      
      const response = {
        digests: apiDigests.map(digest => ({
          id: digest.id,
          title: digest.title,
          headline: digest.headline,
          date: digest.date,
          introduction: digest.introduction,
          generation_status: digest.generation_status,
          created_at: digest.created_at,
          topics_included: digest.metrics?.topics_included || 0,
          events_included: digest.metrics?.events_included || 0,
          articles_processed: digest.metrics?.articles_processed || 0,
          reading_time_minutes: digest.metrics?.reading_time_minutes || 0,
          generation_cost_usd: digest.metrics?.generation_cost_usd || 0
        })),
        pagination: {
          page,
          page_size: pageSize,
          total_pages: Math.ceil(localResult.totalCount / pageSize),
          total_count: localResult.totalCount,
          has_next: localResult.hasMore,
          has_previous: page > 1
        }
      }
      
      // Queue background sync if stale
      if (isStale && backgroundSync) {
        this.queueBackgroundSync(`digest-list:${userId}`, async () => {
          await this.syncDigestList(userId)
        })
      }
      
      return response
    }

    // STEP 3: Sync from backend
    console.log('DataManager: Syncing digest list from backend')
    return await this.syncDigestList(userId, page, pageSize)
  }

  /**
   * Mark digest as read - instant local update
   */
  async markDigestAsRead(digestId: string): Promise<void> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for mark digest as read')
      return
    }

    const userId = session.user.django_user_id.toString()
    await localDB.markDigestAsRead(userId, digestId)
    console.log(`DataManager: Marked digest ${digestId} as read`)
  }

  /**
   * Sync latest digest from backend
   */
  private async syncLatestDigest(userId: string): Promise<{ digest: Digest | null; message?: string }> {
    try {
      console.log('DataManager: Syncing latest digest from backend')
      
      const response = await digestService.getLatestDigest()
      
      if (response.digest) {
        // Store in local database
        await localDB.storeDigest(userId, response.digest)
        console.log('DataManager: Successfully synced latest digest')
      }
      
      // Update sync metadata
      await localDB.updateDigestSync(userId, {
        lastSyncAt: new Date(),
        isStale: false,
        syncInProgress: false,
        latestDigestId: response.digest?.id,
        latestDigestDate: response.digest?.date
      })
      
      return response
    } catch (error) {
      console.error('DataManager: Failed to sync latest digest:', error)
      
      // Update sync metadata to indicate failure
      await localDB.updateDigestSync(userId, {
        syncInProgress: false
      })
      
      throw error
    }
  }

  /**
   * Sync digest list from backend
   */
  private async syncDigestList(userId: string, page: number = 1, pageSize: number = 10): Promise<any> {
    try {
      console.log(`DataManager: Syncing digest list from backend (page ${page})`)
      
      const response = await digestService.listDigests(page, pageSize)
      
      // Store digests in local database
      for (const digestSummary of response.digests) {
        // Convert digest summary to full digest format for storage
        const fullDigest = {
          ...digestSummary,
          topics: [],
          metrics: {
            topics_included: digestSummary.topics_included,
            events_included: digestSummary.events_included,
            articles_processed: digestSummary.articles_processed,
            reading_time_minutes: digestSummary.reading_time_minutes,
            generation_cost_usd: digestSummary.generation_cost_usd,
            generation_tokens_total: 0
          }
        }
        
        await localDB.storeDigest(userId, fullDigest)
      }
      
      // Update sync metadata
      await localDB.updateDigestSync(userId, {
        lastSyncAt: new Date(),
        isStale: false,
        syncInProgress: false
      })
      
      console.log(`DataManager: Successfully synced ${response.digests.length} digests`)
      
      return response
    } catch (error) {
      console.error('DataManager: Failed to sync digest list:', error)
      
      // Update sync metadata to indicate failure
      await localDB.updateDigestSync(userId, {
        syncInProgress: false
      })
      
      throw error
    }
  }

  /**
   * Background sync digests - used by background sync process
   */
  async backgroundSyncDigests(userId: string): Promise<void> {
    try {
      console.log('DataManager: Background syncing digests')
      
      const digestSync = await localDB.getDigestSync(userId)
      
      // Skip if sync already in progress
      if (digestSync.syncInProgress) {
        console.log('DataManager: Digest sync already in progress, skipping')
        return
      }
      
      // Mark sync as in progress
      await localDB.updateDigestSync(userId, {
        syncInProgress: true
      })
      
      // Sync latest digest
      await this.syncLatestDigest(userId)
      
      console.log('DataManager: Background digest sync completed')
    } catch (error) {
      console.error('DataManager: Background digest sync failed:', error)
      
      // Reset sync status on failure
      await localDB.updateDigestSync(userId, {
        syncInProgress: false
      })
    }
  }

  // ===============================================
  // DIGEST CACHE INVALIDATION
  // ===============================================

  /**
   * Invalidate digest cache when new digest is generated
   * Called by UI components when they detect a new digest
   */
  async invalidateDigestCache(): Promise<void> {
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for cache invalidation')
      return
    }

    const userId = session.user.django_user_id.toString()
    
    try {
      console.log('DataManager: Invalidating digest cache - new digest detected')
      
      // Force sync metadata to be stale
      await localDB.updateDigestSync(userId, {
        lastSyncAt: new Date(0), // Force immediate refresh
        isStale: true,
        syncInProgress: false
      })
      
      // Clear any queued background syncs to avoid conflicts
      const digestSyncKeys = Array.from(this.syncQueue).filter(key => 
        key.includes('digest-latest') || key.includes('digest-list')
      )
      digestSyncKeys.forEach(key => this.syncQueue.delete(key))
      
      console.log('DataManager: Digest cache invalidated successfully')
    } catch (error) {
      console.error('DataManager: Failed to invalidate digest cache:', error)
    }
  }

  /**
   * Force refresh latest digest - bypass cache entirely
   * Used when we know a new digest has been generated
   */
  async forceRefreshLatestDigest(): Promise<{ digest: Digest | null; message?: string }> {
    console.log('DataManager: Force refreshing latest digest (bypassing cache)')
    return await this.getLatestDigest({ 
      forceRefresh: true, 
      maxAge: 0, 
      backgroundSync: false 
    })
  }

  // ===============================================
  // USER ACTIONS - INSTANT LOCAL UPDATES
  // ===============================================

  /**
   * Mark article as read - instant local update, no API call
   */
  async markArticleAsRead(articleId: string): Promise<void> {
    await localDB.markArticleAsRead(articleId)
    console.log(`DataManager: Marked article ${articleId} as read`)
  }

  /**
   * Toggle article saved status - instant local update, no API call
   */
  async toggleArticleSaved(articleId: string): Promise<boolean> {
    const newSavedState = await localDB.toggleArticleSaved(articleId)
    console.log(`DataManager: Toggled article ${articleId} saved to ${newSavedState}`)
    return newSavedState
  }

  // ===============================================
  // BACKGROUND SYNC MANAGEMENT
  // ===============================================

  /**
   * Queue background sync with debouncing - prevents loops
   */
  private queueBackgroundSync(key: string, syncFn: () => Promise<void>): void {
    // Skip if already queued
    if (this.syncQueue.has(key)) {
      console.log(`DataManager: Background sync already queued for ${key}`)
      return
    }

    // Skip if too many active syncs
    if (this.activeSyncs.size >= this.config.maxConcurrentSyncs) {
      console.log(`DataManager: Too many active syncs, skipping ${key}`)
      return
    }

    this.syncQueue.add(key)
    console.log(`DataManager: Queued background sync for ${key}`)

    // Debounced execution
    setTimeout(() => {
      this.syncQueue.delete(key)
      
      syncFn().catch(error => {
        console.error(`DataManager: Background sync failed for ${key}:`, error)
      })
    }, this.SYNC_DEBOUNCE_MS)
  }

  /**
   * Force refresh all stale data - comprehensive sync for offline recovery
   */
  async forceRefreshAll(): Promise<void> {
    console.log('DataManager: Force refreshing all data comprehensively')
    
    const session = await getSession()
    if (!session?.user?.django_user_id) {
      console.warn('DataManager: No authenticated user for force refresh')
      return
    }

    const userId = String(session.user.django_user_id)

    // Clear sync queue to avoid conflicts
    this.syncQueue.clear()

    try {
      // 1. Sync user preferences
      console.log('DataManager: Force refreshing user preferences...')
      await this.getUserPreferences({ maxAge: 0, backgroundSync: false })

      // 2. Sync latest digest
      console.log('DataManager: Force refreshing latest digest...')
      try {
        await this.getLatestDigest({ maxAge: 0, backgroundSync: false })
      } catch (error) {
        console.warn('DataManager: Digest refresh failed during force refresh:', error)
      }

      // 3. Sync both main feeds
      console.log('DataManager: Force refreshing main feeds...')
      const feedRefreshPromises = [
        this.getFeed('personalized', undefined, 1, 10, { forceRefresh: true }),
        this.getFeed('world', undefined, 1, 10, { forceRefresh: true })
      ]
      await Promise.all(feedRefreshPromises.map(p => p.catch(err => 
        console.warn('DataManager: Feed refresh failed during force refresh:', err)
      )))

      console.log('DataManager: Force refresh completed successfully')
    } catch (error) {
      console.error('DataManager: Force refresh failed:', error)
      throw error
    }
  }

  /**
   * Get sync status for debugging
   */
  async getSyncStatus(): Promise<any> {
    const session = await getSession()
    if (!session?.user?.django_user_id) return null

    const userId = String(session.user.django_user_id)
    const stats = await localDB.getStats()
    
    return {
      databaseStats: stats,
      activeSyncs: Array.from(this.activeSyncs),
      queuedSyncs: Array.from(this.syncQueue),
      config: this.config
    }
  }



  /**
   * Cleanup resources
   */
  destroy(): void {
    this.syncQueue.clear()
    this.activeSyncs.clear()
    console.log('DataManager: Destroyed')
  }
}

// ===============================================
// SINGLETON INSTANCE
// ===============================================

export const dataManager = new DataManager()

// Expose for debugging
if (typeof window !== 'undefined') {
  (window as any).dataManager = dataManager
}

// Cleanup on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    dataManager.destroy()
  })
} 
