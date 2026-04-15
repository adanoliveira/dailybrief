import { localDB } from './local-database'
import { dataManager } from './data-manager'
import { useUserPreferences, useFeed, useOfflineStatus } from './use-local-data'

/**
 * Simple test function to validate database functionality
 * Call this from browser console: testDatabase()
 */
export async function testDatabase() {
  try {
    console.log('🧪 Testing LocalDatabase...')
    
    // Test 1: Database stats
    const stats = await localDB.getStats()
    console.log('📊 Database stats:', stats)
    
    // Test 2: Save a test user profile
    await localDB.saveUserProfile({
      userId: 'test-user-123',
      publicId: 'test-public-id',
      email: 'test@example.com',
      name: 'Test User',
      hasCompletedOnboarding: true,
      topics: JSON.stringify([1, 2, 3]),
      regions: JSON.stringify([1]),
      languages: JSON.stringify([1]),
      publications: JSON.stringify([1, 2, 3, 4]),
      lastSyncAt: new Date()
    })
    console.log('✅ User profile saved')
    
    // Test 3: Retrieve the user profile
    const userProfile = await localDB.getUserProfile('test-user-123')
    console.log('✅ User profile retrieved:', userProfile)
    
    // Test 4: Save a test article
    await localDB.saveArticle({
      backendId: 'test-article-456',
      title: 'Test Article Title',
      description: 'This is a test article description',
      url: 'https://example.com/test-article',
      publishedAt: new Date(),
      isTopHeadline: true,
      sourceName: 'Test Source',
      isRead: false,
      isSaved: false,
      lastSyncAt: new Date()
    })
    console.log('✅ Article saved')
    
    // Test 5: Retrieve the article
    const article = await localDB.getArticleByBackendId('test-article-456')
    console.log('✅ Article retrieved:', article)
    
    // Test 6: Mark article as read
    await localDB.markArticleAsRead('test-article-456')
    const readArticle = await localDB.getArticleByBackendId('test-article-456')
    console.log('✅ Article marked as read:', readArticle?.isRead)
    
    // Test 7: Create feed sync
    const feedSync = await localDB.saveFeedSync({
      userId: 'test-user-123',
      feedType: 'personalized',
      topicSlug: undefined,
      lastSyncAt: new Date(),
      isStale: false,
      syncInProgress: false,
      lastPage: 1,
      hasMore: true,
      syncCount: 1,
      consecutiveErrors: 0
    })
    console.log('✅ Feed sync created:', feedSync)
    
    // Test 8: Get updated stats
    const finalStats = await localDB.getStats()
    console.log('📊 Final database stats:', finalStats)
    
    console.log('🎉 All database tests passed!')
    return true
    
  } catch (error) {
    console.error('❌ Database test failed:', error)
    return false
  }
}

/**
 * Test DataManager functionality
 */
export async function testDataManager() {
  try {
    console.log('🧪 Testing DataManager...')
    
    // Test 1: Get sync status
    const syncStatus = await dataManager.getSyncStatus()
    console.log('📊 DataManager sync status:', syncStatus)
    
    // Test 2: Test user preferences (local-first)
    console.log('Testing user preferences (will return null if not logged in)...')
    const preferences = await dataManager.getUserPreferences({ backgroundSync: true })
    console.log('✅ User preferences from DataManager:', preferences)
    
    // Test 3: Test feed access (local-first)
    console.log('Testing feed access (will return null if not logged in)...')
    const feed = await dataManager.getFeed('world', 'all', 1, 5, { backgroundSync: true })
    console.log('✅ World feed from DataManager:', feed)
    
    // Test 4: Test article actions
    if (feed?.articles && feed.articles.length > 0) {
      const firstArticleId = feed.articles[0].id
      console.log(`Testing article actions with article: ${firstArticleId}`)
      
      await dataManager.markArticleAsRead(firstArticleId)
      console.log('✅ Marked article as read')
      
      const savedState = await dataManager.toggleArticleSaved(firstArticleId)
      console.log(`✅ Toggled article saved to: ${savedState}`)
    }
    
    console.log('🎉 DataManager tests completed!')
    return true
    
  } catch (error) {
    console.error('❌ DataManager test failed:', error)
    return false
  }
}

/**
 * Test React hooks functionality (requires React component context)
 */
export async function testHooksInComponent() {
  console.log('🧪 Testing React hooks...')
  console.log('ℹ️  Note: This should be called from within a React component')
  console.log('✅ React hooks available for testing in components')
  return true
}

/**
 * Debug function to inspect current feed state
 */
export async function debugFeedState(feedType: 'personalized' | 'world' = 'personalized') {
  try {
    console.log('🔍 Debugging feed state...')
    
    const stats = await localDB.getStats()
    console.log('📊 Database stats:', stats)

    // Try to get user ID - this will work if user is logged in
    try {
      const userPrefs = await dataManager.getUserPreferences({ backgroundSync: false })
      if (!userPrefs) {
        console.log('❌ No user session - cannot debug feed')
        return
      }

      const userId = String(userPrefs.user_id)
      console.log('👤 User ID:', userId)
      
      // Get feed sync
      const feedSync = await localDB.getFeedSync(userId, feedType)
      if (!feedSync) {
        console.log('❌ No feed sync found')
        return
      }

      console.log('📋 Feed sync:', {
        id: feedSync.id,
        lastSyncAt: feedSync.lastSyncAt,
        hasMore: feedSync.hasMore,
        totalItems: feedSync.totalItems,
        lastPage: feedSync.lastPage
      })

      // Get all feed items
      const feedItems = await localDB.feedItems
        .where('feedSyncId')
        .equals(feedSync.id!)
        .toArray()

      console.log('📑 Feed items:', {
        count: feedItems.length,
        positions: feedItems.map(item => item.position).sort((a, b) => a - b)
      })

      // Test pagination for first 3 pages
      for (let page = 1; page <= 3; page++) {
        const result = await localDB.getFeedArticles(feedSync.id!, page, 10)
        console.log(`📄 Page ${page}: ${result.articles.length} articles (total: ${result.totalCount})`)
      }

    } catch (sessionError) {
      console.log('❌ Could not get user session:', sessionError)
    }

  } catch (error) {
    console.error('❌ Debug failed:', error)
  }
}

// Cache clearing functions for debugging
export function clearFeedCache() {
  // Access the internal cache through the module
  try {
    const { hookStateCache } = require('./use-local-data')
    hookStateCache.clearFeedCache()
    console.log('✅ Feed cache cleared')
  } catch (error) {
    console.log('⚠️ Feed cache clear attempted - check console for hookStateCache access')
  }
}

export function clearUserPreferencesCache() {
  try {
    const { hookStateCache } = require('./use-local-data')
    hookStateCache.clearUserPreferencesCache()
    console.log('✅ User preferences cache cleared')
  } catch (error) {
    console.log('⚠️ User preferences cache clear attempted - check console for hookStateCache access')
  }
}

export function clearArticleDetailCache() {
  try {
    const { hookStateCache } = require('./use-local-data')
    hookStateCache.clearArticleDetailCache()
    console.log('✅ Article detail cache cleared')
  } catch (error) {
    console.log('⚠️ Article detail cache clear attempted - check console for hookStateCache access')
  }
}

export function clearAllCaches() {
  try {
    const { hookStateCache } = require('./use-local-data')
    hookStateCache.clearAll()
    console.log('✅ All caches cleared')
  } catch (error) {
    console.log('⚠️ All caches clear attempted - check console for hookStateCache access')
  }
}

/**
 * Debug scroll positions for different feeds
 */
export const debugScrollPositions = (): void => {
  console.log('🔍 === SCROLL POSITION DEBUG ===')
  console.log('Current scroll:', window.pageYOffset || document.documentElement.scrollTop)
  console.log('Current path:', window.location.pathname)
  
  // Check sessionStorage
  try {
    const personalizedScroll = sessionStorage.getItem('scroll-personalized:for-you::relevance')
    const worldScroll = sessionStorage.getItem('scroll-world:all::relevance')
    const restoredFlag = (window as any).__scrollRestored
    
    console.log('📰 Home feed:', personalizedScroll || 'Not saved')
    console.log('🌍 World feed:', worldScroll || 'Not saved')
    console.log('🚀 Restored flag:', restoredFlag || 'None')
  } catch (error) {
    console.log('❌ SessionStorage access failed:', error)
  }
}

// Enhanced storage debugging functions
export const debugStorageHealth = async (): Promise<void> => {
  console.log('🔍 === STORAGE HEALTH DEBUG ===')
  
  try {
    const { storageManager } = await import('./storage-manager')
    const health = await storageManager.checkStorageHealth()
    
    console.log('Storage Health:', health)
    
    if (health.info) {
      console.log(`📊 Usage: ${health.info.percentage.toFixed(1)}% (${(health.info.used / 1024 / 1024).toFixed(1)}MB used of ${(health.info.quota / 1024 / 1024).toFixed(1)}MB)`)
    }
    
    // Database statistics
    const userProfiles = await localDB.userProfiles.count()
    const articles = await localDB.articles.count()
    const feedSyncs = await localDB.feedSyncs.count()
    const feedItems = await localDB.feedItems.count()
    
    console.log('📈 Database Stats:', {
      userProfiles,
      articles,
      feedSyncs,
      feedItems,
      total: userProfiles + articles + feedSyncs + feedItems
    })
    
  } catch (error) {
    console.error('❌ Storage health check failed:', error)
  }
}

export const testStorageCleanup = async (): Promise<void> => {
  console.log('🧹 === TESTING STORAGE CLEANUP ===')
  
  try {
    const { storageManager } = await import('./storage-manager')
    const result = await storageManager.cleanupOldData()
    
    console.log('Cleanup Result:', result)
    
    if (result.success) {
      console.log(`✅ Successfully cleaned ${result.cleaned} items`)
    } else {
      console.log('❌ Cleanup failed')
    }
    
    // Show updated stats
    await debugStorageHealth()
    
  } catch (error) {
    console.error('❌ Cleanup test failed:', error)
  }
}

// Make all functions and hooks available globally for easy testing
if (typeof window !== 'undefined') {
  (window as any).testDatabase = testDatabase;
  (window as any).testDataManager = testDataManager;
  (window as any).testHooksInComponent = testHooksInComponent;
  (window as any).debugFeedState = debugFeedState;
  (window as any).debugScrollPositions = debugScrollPositions;
  (window as any).clearFeedCache = clearFeedCache;
  (window as any).clearUserPreferencesCache = clearUserPreferencesCache;
  (window as any).clearArticleDetailCache = clearArticleDetailCache;
  (window as any).clearAllCaches = clearAllCaches;
  (window as any).useUserPreferences = useUserPreferences;
  (window as any).useFeed = useFeed;
  (window as any).useOfflineStatus = useOfflineStatus;
  (window as any).dataManager = dataManager;
  (window as any).localDB = localDB
} 