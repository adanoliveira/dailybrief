/**
 * API Cache - Utility for deduplicating API calls
 * 
 * This module provides a way to cache API requests and prevent duplicate calls
 * to the same endpoint with the same parameters in a short time window.
 */

interface CacheEntry {
  timestamp: number
  data: any
  promise: Promise<any> | null
}

interface CacheOptions {
  cacheTimeMs?: number  // How long to cache requests
  logEnabled?: boolean  // Whether to log cache hits/misses
}

class ApiCache {
  private cache: Map<string, CacheEntry>
  private cacheTimeMs: number
  private logEnabled: boolean

  constructor(options: CacheOptions = {}) {
    this.cache = new Map()
    this.cacheTimeMs = options.cacheTimeMs || 2000 // Default: 2 seconds
    this.logEnabled = options.logEnabled || false
  }

  /**
   * Generates a cache key from the URL and params
   */
  private generateKey(url: string, params: any = {}): string {
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}=${JSON.stringify(params[key])}`)
      .join('&')
    
    return `${url}?${sortedParams}`
  }

  /**
   * Logs a message if logging is enabled
   */
  private log(message: string): void {
    if (this.logEnabled) {
      console.log(`ApiCache: ${message}`)
    }
  }

  /**
   * Executes the API request with caching
   * Returns cached data if available and fresh, otherwise makes a new request
   */
  async fetch<T>(
    url: string,
    requestFn: () => Promise<T>,
    options: {
      params?: any,
      forceRefresh?: boolean,
      cacheTimeMs?: number
    } = {}
  ): Promise<T> {
    const { params = {}, forceRefresh = false, cacheTimeMs } = options
    const cacheKey = this.generateKey(url, params)
    const now = Date.now()
    const cacheDuration = cacheTimeMs || this.cacheTimeMs
    
    // Check if we have a cached entry
    const cachedEntry = this.cache.get(cacheKey)
    
    // Return cached data if it's still fresh and not forced to refresh
    if (
      !forceRefresh && 
      cachedEntry && 
      now - cachedEntry.timestamp < cacheDuration
    ) {
      this.log(`Cache hit for ${cacheKey}`)
      return cachedEntry.data
    }
    
    // If there's a request in progress, wait for it instead of starting a new one
    if (cachedEntry && cachedEntry.promise) {
      this.log(`Request in progress for ${cacheKey}, joining existing request`)
      return cachedEntry.promise
    }
    
    // Create new request
    this.log(`Cache miss for ${cacheKey}, fetching fresh data`)
    
    // Create promise and store it in cache
    const promise = requestFn().then(
      (data) => {
        // Update cache with successful response
        this.cache.set(cacheKey, {
          timestamp: Date.now(),
          data,
          promise: null
        })
        return data
      },
      (error) => {
        // Remove failed request from cache
        this.cache.delete(cacheKey)
        throw error
      }
    )
    
    // Store the pending promise
    this.cache.set(cacheKey, {
      timestamp: 0, // Invalid until completed
      data: null,
      promise
    })
    
    return promise
  }

  /**
   * Clears the entire cache or a specific entry
   */
  clear(url?: string, params?: any): void {
    if (url) {
      const key = this.generateKey(url, params)
      this.cache.delete(key)
      this.log(`Cleared cache for ${key}`)
    } else {
      this.cache.clear()
      this.log('Cleared entire cache')
    }
  }

  /**
   * Manually set a cache value
   */
  set(url: string, data: any, params: any = {}): void {
    const key = this.generateKey(url, params)
    this.cache.set(key, {
      timestamp: Date.now(),
      data,
      promise: null
    })
    this.log(`Manually set cache for ${key}`)
  }
}

// Export a singleton instance
export const apiCache = new ApiCache({
  cacheTimeMs: 5000, // 5 seconds
  logEnabled: process.env.NODE_ENV === 'development'
})

export default apiCache 