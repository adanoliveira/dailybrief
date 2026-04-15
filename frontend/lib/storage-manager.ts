// ===============================================
// PRODUCTION-READY STORAGE MANAGER
// ===============================================

export interface StorageInfo {
  used: number
  available: number
  quota: number
  percentage: number
}

export interface StorageHealth {
  isAvailable: boolean
  canWrite: boolean
  info: StorageInfo | null
  lastError: string | null
}

class StorageManager {
  private static instance: StorageManager
  private isStorageAvailable = true
  private lastQuotaCheck = 0
  private readonly QUOTA_CHECK_INTERVAL = 5 * 60 * 1000 // 5 minutes

  static getInstance(): StorageManager {
    if (!StorageManager.instance) {
      StorageManager.instance = new StorageManager()
    }
    return StorageManager.instance
  }

  // Check if storage is available and functional
  async checkStorageHealth(): Promise<StorageHealth> {
    // Only run in browser environment
    if (typeof window === 'undefined') {
      return {
        isAvailable: false,
        canWrite: false,
        info: null,
        lastError: 'Server-side environment'
      }
    }

    try {
      // Test IndexedDB availability
      if (!window.indexedDB) {
        return {
          isAvailable: false,
          canWrite: false,
          info: null,
          lastError: 'IndexedDB not supported'
        }
      }

      // Test write capability
      const testKey = '__storage_test__'
      localStorage.setItem(testKey, 'test')
      localStorage.removeItem(testKey)

      // Get storage quota info
      const info = await this.getStorageInfo()
      
      return {
        isAvailable: true,
        canWrite: true,
        info,
        lastError: null
      }
    } catch (error) {
      return {
        isAvailable: false,
        canWrite: false,
        info: null,
        lastError: error instanceof Error ? error.message : 'Unknown storage error'
      }
    }
  }

  // Get storage usage information
  async getStorageInfo(): Promise<StorageInfo> {
    // Only run in browser environment
    if (typeof window === 'undefined' || typeof navigator === 'undefined') {
      return { used: 0, available: 0, quota: 0, percentage: 0 }
    }

    if ('storage' in navigator && 'estimate' in navigator.storage) {
      try {
        const estimate = await navigator.storage.estimate()
        const quota = estimate.quota || 0
        const usage = estimate.usage || 0
        const available = quota - usage
        const percentage = quota > 0 ? (usage / quota) * 100 : 0

        return {
          used: usage,
          available,
          quota,
          percentage
        }
      } catch (error) {
        console.warn('Failed to get storage estimate:', error)
      }
    }

    // Fallback for older browsers
    return {
      used: 0,
      available: 0,
      quota: 0,
      percentage: 0
    }
  }

  // Check if we're approaching storage limits
  async isStorageHealthy(): Promise<boolean> {
    const now = Date.now()
    
    // Only check quota periodically to avoid performance impact
    if (now - this.lastQuotaCheck < this.QUOTA_CHECK_INTERVAL) {
      return this.isStorageAvailable
    }

    this.lastQuotaCheck = now
    
    try {
      const info = await this.getStorageInfo()
      
      // Consider storage unhealthy if >85% full
      if (info.percentage > 85) {
        console.warn(`Storage is ${info.percentage.toFixed(1)}% full`)
        this.isStorageAvailable = false
        return false
      }

      this.isStorageAvailable = true
      return true
    } catch (error) {
      console.error('Storage health check failed:', error)
      this.isStorageAvailable = false
      return false
    }
  }

  // Cleanup old data when storage is getting full
  async cleanupOldData(): Promise<{ success: boolean; cleaned: number }> {
    // Only run in browser environment
    if (typeof window === 'undefined') {
      console.log('StorageManager: Skipping cleanup - not in browser environment')
      return { success: false, cleaned: 0 }
    }
    
    try {
      const { localDB } = await import('./local-database')
      let cleanedItems = 0

      // Remove articles older than 30 days
      const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      
      const oldArticles = await localDB.articles
        .where('createdAt')
        .below(thirtyDaysAgo)
        .toArray()

      if (oldArticles.length > 0) {
        await localDB.articles
          .where('createdAt')
          .below(thirtyDaysAgo)
          .delete()
        
        cleanedItems += oldArticles.length
        console.log(`Cleaned up ${oldArticles.length} old articles`)
      }

      // Remove old feed sync data (keep only last 7 days)
      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      
      const oldFeedSyncs = await localDB.feedSyncs
        .where('lastSyncAt')
        .below(sevenDaysAgo)
        .toArray()

      if (oldFeedSyncs.length > 0) {
        // Also clean up associated feed items
        for (const feedSync of oldFeedSyncs) {
          await localDB.feedItems.where('feedSyncId').equals(feedSync.id!).delete()
        }
        
        await localDB.feedSyncs
          .where('lastSyncAt')
          .below(sevenDaysAgo)
          .delete()
        
        cleanedItems += oldFeedSyncs.length
        console.log(`Cleaned up ${oldFeedSyncs.length} old feed syncs`)
      }

      return { success: true, cleaned: cleanedItems }
    } catch (error) {
      console.error('Data cleanup failed:', error)
      return { success: false, cleaned: 0 }
    }
  }

  // Clear all user data (for logout)
  async clearUserData(userId: string): Promise<boolean> {
    // Only run in browser environment
    if (typeof window === 'undefined') {
      console.log('StorageManager: Skipping clear user data - not in browser environment')
      return false
    }
    
    try {
      const { localDB } = await import('./local-database')
      
      // Clear user profile
      await localDB.userProfiles.where('userId').equals(userId).delete()
      
      // Clear user's feed data
      const userFeedSyncs = await localDB.feedSyncs.where('userId').equals(userId).toArray()
      for (const feedSync of userFeedSyncs) {
        await localDB.feedItems.where('feedSyncId').equals(feedSync.id!).delete()
      }
      await localDB.feedSyncs.where('userId').equals(userId).delete()
      
      // Clear articles (they might be shared, so just mark as not cached)
      // Or clear all if this is the only user
      const allUsers = await localDB.userProfiles.toArray()
      if (allUsers.length === 0) {
        await localDB.articles.clear()
      }

      console.log(`Cleared all data for user ${userId}`)
      return true
    } catch (error) {
      console.error('Failed to clear user data:', error)
      return false
    }
  }

  // Emergency clear all data
  async clearAllData(): Promise<boolean> {
    try {
      const { localDB } = await import('./local-database')
      
      await localDB.userProfiles.clear()
      await localDB.articles.clear()
      await localDB.feedSyncs.clear()
      await localDB.feedItems.clear()
      
      // Also clear localStorage cache keys
      const keysToRemove: string[] = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && (key.startsWith('scroll-') || key.startsWith('cache-'))) {
          keysToRemove.push(key)
        }
      }
      
      keysToRemove.forEach(key => localStorage.removeItem(key))
      
      console.log('Emergency: All local data cleared')
      return true
    } catch (error) {
      console.error('Failed to clear all data:', error)
      return false
    }
  }
}

export const storageManager = StorageManager.getInstance() 