import Dexie, { Table } from 'dexie'

// ===============================================
// CORE INTERFACES
// ===============================================

export interface LocalUserProfile {
  id?: number
  userId: string // Django user ID (unique)
  publicId: string // Django public_id
  email: string
  name: string
  hasCompletedOnboarding: boolean
  
  // Preferences stored as JSON strings for simplicity
  topics: string // JSON array of topic IDs
  topicsDetails?: string // JSON array of topic objects  
  regions: string // JSON array of region IDs
  languages: string // JSON array of language IDs
  publications: string // JSON array of publication IDs
  
  // Sync metadata
  lastSyncAt: Date
  createdAt: Date
  updatedAt: Date
}

export interface LocalArticle {
  id?: number
  backendId: string // Backend article ID (unique)
  
  // Core article data
  title: string
  visualTitle?: string
  description: string
  content?: string // Full content (loaded on demand)
  url: string
  imageUrl?: string
  publishedAt: Date
  readTime?: number
  isTopHeadline: boolean
  
  // Source information
  sourceName: string
  sourceLogoUrl?: string
  
  // Content metadata (stored as JSON strings)
  summary?: string // JSON summary object
  richContent?: string // JSON rich content
  contentStatus?: string
  contentQuality?: string // JSON quality metrics
  topics?: string // JSON array of topic objects
  
  // Local user state (these are the key additions)
  isRead: boolean
  isSaved: boolean
  readAt?: Date
  savedAt?: Date
  
  // Sync metadata
  lastSyncAt: Date
  createdAt: Date
  updatedAt: Date
}

export interface LocalDigest {
  id?: number
  backendId: string // Backend digest ID (unique)
  userId: string // Django user ID
  
  // Core digest data
  title: string
  headline?: string
  date: string // YYYY-MM-DD format
  introduction: string
  conclusion?: string
  
  // Full digest content (stored as JSON string)
  topics: string // JSON array of DigestTopic objects
  
  // Status and metadata
  generationStatus: 'GENERATING' | 'COMPLETED' | 'FAILED'
  
  // Metrics (stored as JSON string)
  metrics: string // JSON DigestMetrics object
  
  // Article date range (stored as JSON string)
  articleDateRange?: string // JSON object with min/max dates
  
  // Local state
  isRead: boolean
  readAt?: Date
  
  // Backend timestamps
  backendCreatedAt: Date
  backendUpdatedAt: Date
  
  // Sync metadata
  lastSyncAt: Date
  createdAt: Date
  updatedAt: Date
}

export interface DigestSync {
  id?: number
  userId: string
  
  // Sync status
  lastSyncAt: Date
  nextSyncAt?: Date
  isStale: boolean
  syncInProgress: boolean
  
  // Latest digest info
  latestDigestId?: string
  latestDigestDate?: string
  
  // Sync metadata
  createdAt: Date
  updatedAt: Date
}

export interface FeedSync {
  id?: number
  userId: string
  feedType: string // 'personalized' | 'world'
  topicSlug?: string // null for 'for-you' or 'all'
  
  // Sync status
  lastSyncAt: Date
  nextSyncAt?: Date
  isStale: boolean
  syncInProgress: boolean
  
  // Pagination state
  lastPage: number
  hasMore: boolean
  totalItems?: number
  
  // Sync metadata for monitoring
  syncCount: number
  lastSyncDuration?: number // milliseconds
  lastError?: string
  consecutiveErrors: number
  
  // Pending articles (detected but not yet inserted)
  pendingNewArticles?: number
  pendingUpdatedArticles?: number
  pendingArticlesData?: string // JSON stringified pending articles data
  
  createdAt: Date
  updatedAt: Date
}

export interface FeedItem {
  id?: number
  feedSyncId: number
  articleId: number
  position: number // Order in feed
  relevanceScore?: number // For personalized feeds
  addedAt: Date
}

// ===============================================
// DATABASE CLASS
// ===============================================

export class LocalDatabase extends Dexie {
  // Table definitions
  userProfiles!: Table<LocalUserProfile>
  articles!: Table<LocalArticle>
  feedSyncs!: Table<FeedSync>
  feedItems!: Table<FeedItem>
  digests!: Table<LocalDigest>
  digestSyncs!: Table<DigestSync>

  constructor() {
    super('DailyBriefLocalDB')
    
    // Version 1 schema
    this.version(1).stores({
      // User profiles - indexed by userId for fast lookups
      userProfiles: '++id, userId, publicId, lastSyncAt',
      
      // Articles - indexed for efficient queries
      articles: '++id, backendId, publishedAt, isTopHeadline, isRead, isSaved, lastSyncAt',
      
      // Feed sync metadata - separate indexes for efficient queries
      feedSyncs: '++id, userId, feedType, lastSyncAt, nextSyncAt, isStale',
      
      // Feed items - for feed-article relationships with compound index for efficient smart updates
      feedItems: '++id, feedSyncId, articleId, position, addedAt, [feedSyncId+position]'
    })

    // Version 2 schema - Add digest tables
    this.version(2).stores({
      // Keep all existing tables
      userProfiles: '++id, userId, publicId, lastSyncAt',
      articles: '++id, backendId, publishedAt, isTopHeadline, isRead, isSaved, lastSyncAt',
      feedSyncs: '++id, userId, feedType, lastSyncAt, nextSyncAt, isStale',
      feedItems: '++id, feedSyncId, articleId, position, addedAt, [feedSyncId+position]',
      
      // Add new digest tables
      digests: '++id, backendId, userId, date, isRead, generationStatus, backendCreatedAt, lastSyncAt',
      digestSyncs: '++id, userId, lastSyncAt, nextSyncAt, isStale'
    })

    // Add hooks for automatic timestamps - existing tables
    this.userProfiles.hook('creating', function (primKey: any, obj: any, trans: any) {
      obj.createdAt = new Date()
      obj.updatedAt = new Date()
    })

    this.userProfiles.hook('updating', function (modifications: any) {
      modifications.updatedAt = new Date()
    })

    this.articles.hook('creating', function (primKey: any, obj: any, trans: any) {
      obj.createdAt = new Date()
      obj.updatedAt = new Date()
    })

    this.articles.hook('updating', function (modifications: any) {
      modifications.updatedAt = new Date()
    })

    this.feedSyncs.hook('creating', function (primKey: any, obj: any, trans: any) {
      obj.createdAt = new Date()
      obj.updatedAt = new Date()
    })

    this.feedSyncs.hook('updating', function (modifications: any) {
      modifications.updatedAt = new Date()
    })

    // Add hooks for new digest tables
    this.digests.hook('creating', function (primKey: any, obj: any, trans: any) {
      obj.createdAt = new Date()
      obj.updatedAt = new Date()
    })

    this.digests.hook('updating', function (modifications: any) {
      modifications.updatedAt = new Date()
    })

    this.digestSyncs.hook('creating', function (primKey: any, obj: any, trans: any) {
      obj.createdAt = new Date()
      obj.updatedAt = new Date()
    })

    this.digestSyncs.hook('updating', function (modifications: any) {
      modifications.updatedAt = new Date()
    })

  }

  // Wrapper method with error handling for database operations
  async safeExecute<T>(operation: () => Promise<T>, operationName: string): Promise<T | null> {
    try {
      return await operation()
    } catch (error: any) {
      console.error(`Database operation '${operationName}' failed:`, error)
      
      // Handle specific error types
      if (error.name === 'QuotaExceededError') {
        console.warn('Storage quota exceeded, triggering cleanup')
        await this.triggerEmergencyCleanup()
      }
      
      return null
    }
  }

  private async triggerEmergencyCleanup(): Promise<void> {
    try {
      const { storageManager } = await import('./storage-manager')
      await storageManager.cleanupOldData()
    } catch (cleanupError) {
      console.error('Emergency cleanup failed:', cleanupError)
    }
  }

  // ===============================================
  // USER PROFILE METHODS
  // ===============================================

  /**
   * Get user profile by userId - NO automatic fetching to prevent loops
   */
  async getUserProfile(userId: string): Promise<LocalUserProfile | undefined> {
    return await this.userProfiles.where('userId').equals(userId).first()
  }

  /**
   * Save user profile - called only by sync manager
   */
  async saveUserProfile(profile: Omit<LocalUserProfile, 'id' | 'createdAt' | 'updatedAt'>): Promise<number> {
    const existing = await this.getUserProfile(profile.userId)
    
    if (existing?.id) {
      await this.userProfiles.update(existing.id, {
        ...profile,
        updatedAt: new Date()
      })
      return existing.id
    } else {
      return await this.userProfiles.add({
        ...profile,
        createdAt: new Date(),
        updatedAt: new Date()
      })
    }
  }

  // ===============================================
  // ARTICLE METHODS
  // ===============================================

  /**
   * Get article by backend ID - NO automatic fetching to prevent loops
   */
  async getArticleByBackendId(backendId: string): Promise<LocalArticle | undefined> {
    return await this.articles.where('backendId').equals(backendId).first()
  }

  /**
   * Save article - called only by sync manager
   */
  async saveArticle(article: Omit<LocalArticle, 'id' | 'createdAt' | 'updatedAt'>): Promise<number> {
    const existing = await this.getArticleByBackendId(article.backendId)
    
    if (existing?.id) {
      await this.articles.update(existing.id, {
        ...article,
        updatedAt: new Date()
      })
      return existing.id
    } else {
      return await this.articles.add({
        ...article,
        createdAt: new Date(),
        updatedAt: new Date()
      })
    }
  }

  /**
   * Mark article as read - instant local update
   */
  async markArticleAsRead(backendId: string): Promise<void> {
    const article = await this.getArticleByBackendId(backendId)
    if (article?.id) {
      await this.articles.update(article.id, {
        isRead: true,
        readAt: new Date()
      })
    }
  }

  /**
   * Toggle article saved status - instant local update
   */
  async toggleArticleSaved(backendId: string): Promise<boolean> {
    const article = await this.getArticleByBackendId(backendId)
    if (!article?.id) {
      throw new Error('Article not found in local storage')
    }

    const newSavedState = !article.isSaved
    await this.articles.update(article.id, {
      isSaved: newSavedState,
      savedAt: newSavedState ? new Date() : undefined
    })

    return newSavedState
  }

  // ===============================================
  // FEED SYNC METHODS
  // ===============================================

  /**
   * Get feed sync record - NO automatic creation to prevent loops
   */
  async getFeedSync(userId: string, feedType: string, topicSlug?: string): Promise<FeedSync | undefined> {
    const normalizedTopicSlug = topicSlug === 'for-you' || topicSlug === 'all' ? undefined : topicSlug
    
    // Use where clause to find matching record
    return await this.feedSyncs
      .where('userId').equals(userId)
      .and(item => item.feedType === feedType && item.topicSlug === normalizedTopicSlug)
      .first()
  }

  /**
   * Create or update feed sync record - called only by sync manager
   */
  async saveFeedSync(feedSync: Omit<FeedSync, 'id' | 'createdAt' | 'updatedAt'>): Promise<FeedSync> {
    const existing = await this.getFeedSync(feedSync.userId, feedSync.feedType, feedSync.topicSlug)
    
    if (existing?.id) {
      await this.feedSyncs.update(existing.id, {
        ...feedSync,
        updatedAt: new Date()
      })
      return { ...feedSync, id: existing.id, createdAt: existing.createdAt, updatedAt: new Date() }
    } else {
      const id = await this.feedSyncs.add({
        ...feedSync,
        createdAt: new Date(),
        updatedAt: new Date()
      })
      return { ...feedSync, id, createdAt: new Date(), updatedAt: new Date() }
    }
  }

  /**
   * Get feed articles with pagination
   */
  async getFeedArticles(
    feedSyncId: number, 
    page: number = 1, 
    pageSize: number = 10
  ): Promise<{ articles: LocalArticle[], totalCount: number }> {
    const offset = (page - 1) * pageSize

    // Get feed items for this page, sorted by position
    const feedItems = await this.feedItems
      .where('feedSyncId')
      .equals(feedSyncId)
      .toArray()
    
    console.log(`DB: getFeedArticles - feedSyncId: ${feedSyncId}, page: ${page}, totalFeedItems: ${feedItems.length}, offset: ${offset}`)
    console.log(`DB: Feed item positions:`, feedItems.map(item => item.position).sort((a, b) => a - b))
    
    // Sort by position and apply pagination
    const sortedFeedItems = feedItems
      .sort((a, b) => a.position - b.position)
      .slice(offset, offset + pageSize)

    console.log(`DB: After pagination - sliced items: ${sortedFeedItems.length}, positions:`, sortedFeedItems.map(item => item.position))

    // Get corresponding articles
    const articleIds = sortedFeedItems.map((item: FeedItem) => item.articleId)
    const articles = await this.articles.where('id').anyOf(articleIds).toArray()

    // Sort articles by feed position
    const sortedArticles = sortedFeedItems.map((item: FeedItem) => 
      articles.find(article => article.id === item.articleId)!
    ).filter(Boolean)

    const totalCount = await this.feedItems.where('feedSyncId').equals(feedSyncId).count()

    console.log(`DB: Final result - articles: ${sortedArticles.length}, totalCount: ${totalCount}`)

    return {
      articles: sortedArticles,
      totalCount
    }
  }

  /**
   * Clear and replace feed items - called only by sync manager
   */
  async replaceFeedItems(feedSyncId: number, items: Omit<FeedItem, 'id'>[]): Promise<void> {
    await this.transaction('rw', [this.feedItems], async () => {
      // Clear existing items
      await this.feedItems.where('feedSyncId').equals(feedSyncId).delete()
      
      // Add new items
      await this.feedItems.bulkAdd(items)
    })
  }

  // ===============================================
  // UTILITY METHODS
  // ===============================================

  /**
   * Mark all feed syncs as stale so they refetch on next load.
   * Called when user preferences change (regions, languages, publications).
   */
  async markAllFeedSyncsStale(): Promise<void> {
    await this.feedSyncs.toCollection().modify({ isStale: true })
    console.log('LocalDatabase: Marked all feed syncs as stale')
  }

  /**
   * Check if data is stale based on age
   */
  isStale(lastSyncAt: Date, maxAgeMs: number): boolean {
    return (Date.now() - lastSyncAt.getTime()) > maxAgeMs
  }

  /**
   * Get database stats for debugging
   */
  async getStats(): Promise<any> {
    const [userCount, articleCount, feedSyncCount, feedItemCount] = await Promise.all([
      this.userProfiles.count(),
      this.articles.count(),
      this.feedSyncs.count(),
      this.feedItems.count()
    ])

    return {
      userProfiles: userCount,
      articles: articleCount,
      feedSyncs: feedSyncCount,
      feedItems: feedItemCount,
      version: this.verno
    }
  }

  /**
   * Detect new articles without inserting them - for user-controlled feed updates
   * Returns info about pending new articles that user can choose to load
   */
  async detectNewArticles(feedSyncId: number, newItems: Omit<FeedItem, 'id'>[]): Promise<{ 
    newArticlesCount: number; 
    updatedArticlesCount: number;
    newArticles: Omit<FeedItem, 'id'>[];
    updatedArticles: Omit<FeedItem, 'id'>[];
  }> {
    // Get existing feed items to compare
    const existingItems = await this.feedItems
      .where('feedSyncId')
      .equals(feedSyncId)
      .toArray()
    
    // Sort by position for consistent ordering
    existingItems.sort((a, b) => a.position - b.position)
    
    // Get article IDs from new items to check for existing articles
    const newArticleIds = newItems.map((item: any) => item.articleId)
    const existingArticleIds = existingItems.map((item: any) => item.articleId)
    
    // Identify truly new articles (not seen before in this feed)
    const newArticles = newItems.filter((item: any) => !existingArticleIds.includes(item.articleId))
    const updatedArticles = newItems.filter((item: any) => existingArticleIds.includes(item.articleId))
    
    console.log(`LocalDatabase: Detected ${newArticles.length} new articles, ${updatedArticles.length} updated articles (not inserted yet)`)
    
    return { 
      newArticlesCount: newArticles.length,
      updatedArticlesCount: updatedArticles.length,
      newArticles,
      updatedArticles
    }
  }

  /**
   * Insert pending new articles at the top of the feed (user-triggered)
   */
  async insertPendingArticles(feedSyncId: number, pendingArticles: Omit<FeedItem, 'id'>[], updatedArticles: Omit<FeedItem, 'id'>[]): Promise<void> {
    await this.transaction('rw', [this.feedItems, this.articles], async () => {
      if (pendingArticles.length > 0) {
        // Get existing items to shift down
        const existingItems = await this.feedItems
          .where('feedSyncId')
          .equals(feedSyncId)
          .toArray()
        
        existingItems.sort((a, b) => a.position - b.position)
        
        // Shift existing articles down to make room for new ones
        const shiftAmount = pendingArticles.length
        console.log(`LocalDatabase: Inserting ${pendingArticles.length} pending articles, shifting ${existingItems.length} existing articles down`)
        
        // Update positions of existing articles (in reverse order to avoid conflicts)
        for (let i = existingItems.length - 1; i >= 0; i--) {
          const item = existingItems[i]
          await this.feedItems
            .where('id')
            .equals(item.id!)
            .modify({ position: item.position + shiftAmount })
        }
        
        // Add new articles at the top (positions 0, 1, 2, ...)
        await this.feedItems.bulkAdd(
          pendingArticles.map((item, index) => ({
            ...item,
            position: index
          }))
        )
      }
      
      // Update existing articles metadata in place
      for (const updatedItem of updatedArticles) {
        // Find the existing item by articleId and update it
        const existingItem = await this.feedItems
          .where({ feedSyncId, articleId: updatedItem.articleId })
          .first()
        
        if (existingItem) {
          await this.feedItems
            .where('id')
            .equals(existingItem.id!)
            .modify({ 
              addedAt: updatedItem.addedAt 
            })
        }
      }
    })
    
    console.log(`LocalDatabase: Successfully inserted ${pendingArticles.length} new articles and updated ${updatedArticles.length} existing articles`)
  }

  /**
   * Clean up old data
   */
  async cleanup(maxAgeMs: number = 7 * 24 * 60 * 60 * 1000): Promise<void> {
    const cutoffDate = new Date(Date.now() - maxAgeMs)
    
    // Remove old articles that aren't saved
    await this.articles
      .where('lastSyncAt')
      .below(cutoffDate)
      .and(article => !article.isSaved)
      .delete()

    console.log('LocalDatabase: Cleaned up old data')
  }

  // ===============================================
  // DIGEST OPERATIONS
  // ===============================================

  /**
   * Store or update a digest in local storage
   */
  async storeDigest(userId: string, digest: any): Promise<LocalDigest | null> {
    return await this.safeExecute(async () => {
      const localDigest: Omit<LocalDigest, 'id' | 'createdAt' | 'updatedAt'> = {
        backendId: digest.id,
        userId,
        title: digest.title,
        headline: digest.headline,
        date: digest.date,
        introduction: digest.introduction,
        conclusion: digest.conclusion,
        topics: JSON.stringify(digest.topics || []),
        generationStatus: digest.generation_status,
        metrics: JSON.stringify(digest.metrics || {}),
        articleDateRange: digest.article_date_range ? JSON.stringify(digest.article_date_range) : undefined,
        isRead: false,
        backendCreatedAt: new Date(digest.created_at),
        backendUpdatedAt: new Date(digest.updated_at),
        lastSyncAt: new Date()
      }

      // Check if digest already exists
      const existing = await this.digests
        .where('backendId')
        .equals(digest.id)
        .and(item => item.userId === userId)
        .first()

      if (existing) {
        // Update existing digest
        await this.digests.update(existing.id!, {
          ...localDigest,
          isRead: existing.isRead, // Preserve read status
          readAt: existing.readAt
        })
        
        const updated = await this.digests.get(existing.id!)
        console.log(`LocalDatabase: Updated digest ${digest.id}`)
        return updated || null
      } else {
        // Insert new digest
        const id = await this.digests.add(localDigest as LocalDigest)
        const stored = await this.digests.get(id)
        console.log(`LocalDatabase: Stored new digest ${digest.id}`)
        return stored || null
      }
    }, `storeDigest(${digest.id})`)
  }

  /**
   * Get digest by backend ID
   */
  async getDigest(userId: string, backendId: string): Promise<LocalDigest | null> {
    return await this.safeExecute(async () => {
      const digest = await this.digests
        .where('backendId')
        .equals(backendId)
        .and(item => item.userId === userId)
        .first()
      
      return digest || null
    }, `getDigest(${backendId})`)
  }

  /**
   * Get latest digest for user
   */
  async getLatestDigest(userId: string): Promise<LocalDigest | null> {
    return await this.safeExecute(async () => {
      const digest = await this.digests
        .where('userId')
        .equals(userId)
        .and(item => item.generationStatus === 'COMPLETED')
        .reverse()
        .sortBy('backendCreatedAt')
      
      return digest.length > 0 ? digest[0] : null
    }, `getLatestDigest(${userId})`)
  }

  /**
   * Get digest by date
   */
  async getDigestByDate(userId: string, date: string): Promise<LocalDigest | null> {
    return await this.safeExecute(async () => {
      const digest = await this.digests
        .where('userId')
        .equals(userId)
        .and(item => item.date === date)
        .first()
      
      return digest || null
    }, `getDigestByDate(${userId}, ${date})`)
  }

  /**
   * List digests for user with pagination
   */
  async listDigests(userId: string, page: number = 1, pageSize: number = 10): Promise<{
    digests: LocalDigest[];
    totalCount: number;
    hasMore: boolean;
  }> {
    return await this.safeExecute(async () => {
      const offset = (page - 1) * pageSize
      
      // Get total count
      const totalCount = await this.digests
        .where('userId')
        .equals(userId)
        .count()
      
      // Get paginated results
      const digests = await this.digests
        .where('userId')
        .equals(userId)
        .reverse()
        .sortBy('backendCreatedAt')
        .then(results => results.slice(offset, offset + pageSize))
      
      const hasMore = offset + pageSize < totalCount
      
      console.log(`LocalDatabase: Listed ${digests.length} digests for user ${userId} (page ${page})`)
      
      return {
        digests,
        totalCount,
        hasMore
      }
    }, `listDigests(${userId}, page=${page})`) || { digests: [], totalCount: 0, hasMore: false }
  }

  /**
   * Mark digest as read
   */
  async markDigestAsRead(userId: string, backendId: string): Promise<boolean> {
    return await this.safeExecute(async () => {
      const digest = await this.getDigest(userId, backendId)
      if (!digest || digest.isRead) {
        return false
      }

      await this.digests.update(digest.id!, {
        isRead: true,
        readAt: new Date()
      })

      console.log(`LocalDatabase: Marked digest ${backendId} as read`)
      return true
    }, `markDigestAsRead(${backendId})`) || false
  }

  /**
   * Get or create digest sync record for user
   */
  async getDigestSync(userId: string): Promise<DigestSync> {
    return await this.safeExecute(async () => {
      let digestSync = await this.digestSyncs
        .where('userId')
        .equals(userId)
        .first()

      if (!digestSync) {
        // Create new digest sync record
        const newDigestSync: Omit<DigestSync, 'id' | 'createdAt' | 'updatedAt'> = {
          userId,
          lastSyncAt: new Date(0), // Start from epoch
          isStale: true,
          syncInProgress: false
        }

        const id = await this.digestSyncs.add(newDigestSync as DigestSync)
        digestSync = await this.digestSyncs.get(id)
        console.log(`LocalDatabase: Created digest sync for user ${userId}`)
      }

      return digestSync!
    }, `getDigestSync(${userId})`) || {
      userId,
      lastSyncAt: new Date(0),
      isStale: true,
      syncInProgress: false,
      createdAt: new Date(),
      updatedAt: new Date()
    } as DigestSync
  }

  /**
   * Update digest sync metadata
   */
  async updateDigestSync(userId: string, updates: Partial<DigestSync>): Promise<boolean> {
    return await this.safeExecute(async () => {
      const digestSync = await this.getDigestSync(userId)
      
      if (digestSync.id) {
        await this.digestSyncs.update(digestSync.id, updates)
        console.log(`LocalDatabase: Updated digest sync for user ${userId}`)
        return true
      }
      
      return false
    }, `updateDigestSync(${userId})`) || false
  }

  /**
   * Convert LocalDigest back to API format for UI consumption
   */
  convertLocalDigestToApi(localDigest: LocalDigest): any {
    return {
      id: localDigest.backendId,
      title: localDigest.title,
      headline: localDigest.headline,
      date: localDigest.date,
      introduction: localDigest.introduction,
      conclusion: localDigest.conclusion,
      topics: JSON.parse(localDigest.topics || '[]'),
      generation_status: localDigest.generationStatus,
      metrics: JSON.parse(localDigest.metrics || '{}'),
      article_date_range: localDigest.articleDateRange ? JSON.parse(localDigest.articleDateRange) : null,
      created_at: localDigest.backendCreatedAt.toISOString(),
      updated_at: localDigest.backendUpdatedAt.toISOString(),
      
      // Local metadata
      _isRead: localDigest.isRead,
      _readAt: localDigest.readAt?.toISOString(),
      _lastSyncAt: localDigest.lastSyncAt.toISOString()
    }
  }
}

// ===============================================
// SINGLETON INSTANCE
// ===============================================

export const localDB = new LocalDatabase() 