/**
 * Custom hook for managing cached data in DailyBrief
 * Provides easy access to cached articles, preferences, and topics
 */

import { useState, useEffect } from 'react'
import { cachedApi } from '@/lib/cached-api'
import { useUser } from '@/lib/user-context'
import { ArticleQueryParams, PaginatedResponse, ArticlePreview, Topic } from '@/lib/api'

interface UseCachedFeedOptions {
  feedType: 'personalized' | 'world'
  params?: ArticleQueryParams
  publicMode?: boolean
  enabled?: boolean
}

interface UseCachedFeedResult {
  data: PaginatedResponse<ArticlePreview> | null
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  loadMore: () => Promise<void>
  hasMore: boolean
  isLoadingMore: boolean
}

/**
 * Hook for cached feed data
 */
export function useCachedFeed({
  feedType,
  params = {},
  publicMode = false,
  enabled = true
}: UseCachedFeedOptions): UseCachedFeedResult {
  const [data, setData] = useState<PaginatedResponse<ArticlePreview> | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  const loadFeed = async (page = 1, isRefresh = false) => {
    if (!enabled) return

    try {
      if (page === 1) {
        setIsLoading(true)
      } else {
        setIsLoadingMore(true)
      }
      
      setError(null)

      const response = await cachedApi.getFeed(feedType, { ...params, page }, {
        forceRefresh: isRefresh,
        loadMore: page > 1,
        publicMode
      })

      if (page === 1) {
        setData(response)
      } else {
        // Append to existing data
        setData(prev => prev ? {
          ...response,
          articles: [...prev.articles, ...response.articles]
        } : response)
      }

      setCurrentPage(page)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load feed')
    } finally {
      setIsLoading(false)
      setIsLoadingMore(false)
    }
  }

  const refresh = async () => {
    setCurrentPage(1)
    await loadFeed(1, true)
  }

  const loadMore = async () => {
    if (data?.pagination.hasNext && !isLoadingMore) {
      await loadFeed(currentPage + 1)
    }
  }

  // Load initial data
  useEffect(() => {
    if (enabled) {
      setCurrentPage(1)
      loadFeed(1)
    }
  }, [feedType, params?.topic, params?.search, params?.sort, enabled])

  return {
    data,
    isLoading,
    error,
    refresh,
    loadMore,
    hasMore: data?.pagination.hasNext || false,
    isLoadingMore
  }
}

interface UseCachedTopicsResult {
  topics: Topic[]
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
}

/**
 * Hook for cached topics
 */
export function useCachedTopics(): UseCachedTopicsResult {
  const [topics, setTopics] = useState<Topic[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadTopics = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const data = await cachedApi.getTopics()
      setTopics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load topics')
    } finally {
      setIsLoading(false)
    }
  }

  const refresh = async () => {
    await loadTopics()
  }

  useEffect(() => {
    loadTopics()
  }, [])

  return {
    topics,
    isLoading,
    error,
    refresh
  }
}

/**
 * Hook for invalidating cache when user preferences change
 */
export function useCacheInvalidation() {
  const { userPreferences } = useUser()

  useEffect(() => {
    // Invalidate feed cache when user preferences change
    if (userPreferences) {
      console.log('User preferences changed, invalidating feed cache')
      cachedApi.invalidateFeedCache()
    }
  }, [userPreferences?.topics, userPreferences?.regions, userPreferences?.languages, userPreferences?.publications])

  const invalidateAll = () => {
    cachedApi.invalidateFeedCache()
  }

  const invalidateSpecificFeed = (feedType: 'personalized' | 'world', topicSlug?: string, searchQuery?: string) => {
    cachedApi.invalidateSpecificFeed(feedType, topicSlug, searchQuery)
  }

  return {
    invalidateAll,
    invalidateSpecificFeed
  }
}

/**
 * Hook for cache statistics and debugging
 */
export function useCacheStats() {
  const [stats, setStats] = useState(cachedApi.getCacheStats())

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(cachedApi.getCacheStats())
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [])

  return stats
} 