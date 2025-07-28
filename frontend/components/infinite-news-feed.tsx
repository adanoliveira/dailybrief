"use client"

import { useEffect, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Check, Coffee, Newspaper, AlertTriangle, RefreshCw } from "lucide-react"
import { useFeed, useOfflineStatus } from "@/lib/use-local-data"
import { format, formatDistanceToNow, isWithinInterval, subDays } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import { NewsCard, ArticlePreviewWithTopics } from "@/components/news-card"

interface InfiniteNewsFeedProps {
  feedType?: 'personalized' | 'world';
  topicSlug?: string;
  searchQuery?: string;
  sortOrder?: 'relevance' | 'newest' | 'oldest';
  publicMode?: boolean; // For backwards compatibility, but not used with local storage
}

export function InfiniteNewsFeed({ 
  feedType = 'personalized', 
  topicSlug, 
  searchQuery, 
  sortOrder = 'relevance',
  publicMode = false 
}: InfiniteNewsFeedProps) {
  const { isOnline, wasOffline } = useOfflineStatus()
  const observer = useRef<IntersectionObserver | null>(null)
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const hasRestoredScroll = useRef(false)

  // Use the new local-first hook for feed data
  const {
    articles,
    isLoading,
    isLoadingMore,
    error,
    hasMore,
    totalItems,
    lastSyncAt,
    loadMore,
    refresh,
    backgroundRefresh,
    saveScrollPosition,
    getScrollPosition
  } = useFeed(feedType, topicSlug, searchQuery, sortOrder, {
    backgroundSync: true // Enable background sync for smooth UX
  })

  // Set up intersection observer for infinite scroll
  const lastArticleRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (isLoadingMore) return

      if (observer.current) observer.current.disconnect()

      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          console.log('InfiniteNewsFeed: Loading more articles via intersection observer')
          loadMore()
        }
      })

      if (node) observer.current.observe(node)
    },
    [isLoadingMore, hasMore, loadMore],
  )

  // Trigger background refresh when app comes back online
  useEffect(() => {
    if (isOnline && wasOffline) {
      console.log('InfiniteNewsFeed: App back online, triggering background refresh')
      backgroundRefresh()
    }
  }, [isOnline, wasOffline, backgroundRefresh])

  // Reset scroll restoration flag when feed changes
  useEffect(() => {
    hasRestoredScroll.current = false
  }, [feedType, topicSlug])

  // Scroll position restoration - restore when articles are loaded and we haven't restored yet
  useEffect(() => {
    if (articles.length > 0 && !hasRestoredScroll.current && !isLoading) {
      const savedScrollPosition = getScrollPosition()
      if (savedScrollPosition) {
        console.log(`InfiniteNewsFeed: Restoring scroll position to ${savedScrollPosition}`)
        setTimeout(() => {
          window.scrollTo({ top: savedScrollPosition, behavior: 'auto' })
          hasRestoredScroll.current = true
        }, 100) // Small delay to ensure DOM is ready
      } else {
        hasRestoredScroll.current = true // Mark as restored even if no saved position
      }
    }
  }, [articles.length, isLoading, getScrollPosition])

  // Save scroll position with throttling
  const handleScroll = useCallback(() => {
    if (scrollTimeoutRef.current) {
      clearTimeout(scrollTimeoutRef.current)
    }
    
    scrollTimeoutRef.current = setTimeout(() => {
      const scrollPosition = window.pageYOffset || document.documentElement.scrollTop
      saveScrollPosition(scrollPosition)
    }, 150) // Throttle scroll events
  }, [saveScrollPosition])

  // Set up scroll listener
  useEffect(() => {
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => {
      window.removeEventListener('scroll', handleScroll)
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current)
      }
    }
  }, [handleScroll])

  // Save scroll position when component unmounts (user navigates away)
  useEffect(() => {
    return () => {
      const scrollPosition = window.pageYOffset || document.documentElement.scrollTop
      if (scrollPosition > 0) {
        saveScrollPosition(scrollPosition)
        console.log(`InfiniteNewsFeed: Saved scroll position ${scrollPosition} on unmount`)
      }
    }
  }, [saveScrollPosition])

  // Handle article click - save scroll position immediately
  const handleArticleClick = useCallback(() => {
    const scrollPosition = window.pageYOffset || document.documentElement.scrollTop
    saveScrollPosition(scrollPosition)
    console.log(`InfiniteNewsFeed: Saved scroll position ${scrollPosition} on article click`)
  }, [saveScrollPosition])

  // Handle manual refresh
  const handleRefresh = useCallback(async () => {
    console.log('InfiniteNewsFeed: Manual refresh requested')
    try {
      await refresh()
    } catch (err) {
      console.error('InfiniteNewsFeed: Manual refresh failed:', err)
    }
  }, [refresh])

  // Render empty state
  const renderEmptyState = () => (
    <Card className="bg-primary/5 border-primary/20 text-center">
      <CardContent className="pt-6 pb-4">
        <div className="flex justify-center mb-4">
          <div className="bg-primary/10 p-3 rounded-full">
            <Newspaper className="h-6 w-6 text-primary" />
          </div>
        </div>
        <h3 className="text-lg font-medium mb-2">
          {feedType === 'world' ? 'No headlines found' : 'No articles found'}
        </h3>
        <p className="text-muted-foreground mb-4">
          {!isOnline ? (
            "You're offline. Connect to the internet to load fresh content."
          ) : searchQuery ? (
            `No ${feedType === 'world' ? 'headlines' : 'articles'} match your search criteria. Try a different search term.`
          ) : topicSlug !== 'for-you' && topicSlug !== 'all' ? (
            `No ${feedType === 'world' ? 'headlines' : 'articles'} found in this topic. Try a different topic or check back later.`
          ) : feedType === 'world' ? (
            "We couldn't find any headlines. Check back later for the latest news."
          ) : (
            "We couldn't find any articles for your preferences. Update your interests or check back later."
          )}
        </p>
        {isOnline && (
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        )}
      </CardContent>
    </Card>
  )

  // Render error state
  const renderErrorState = () => (
    <Card className="bg-destructive/5 border-destructive/20 text-center">
      <CardContent className="pt-6 pb-4">
        <div className="flex justify-center mb-4">
          <div className="bg-destructive/10 p-3 rounded-full">
            <AlertTriangle className="h-6 w-6 text-destructive" />
          </div>
        </div>
        <h3 className="text-lg font-medium mb-2">
          Failed to load {feedType === 'world' ? 'headlines' : 'articles'}
        </h3>
        <p className="text-muted-foreground mb-4">
          {!isOnline ? (
            "You're offline and no cached content is available."
          ) : (
            error || "Something went wrong. Please try again."
          )}
        </p>
        <div className="flex gap-2 justify-center">
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Try again
          </Button>
        </div>
      </CardContent>
    </Card>
  )

  // Loading skeletons for initial load
  const renderSkeletons = () => (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <Card key={i}>
          <CardHeader>
            <Skeleton className="h-6 w-3/4 mb-2" />
            <Skeleton className="h-4 w-1/3" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-full mb-2" />
            <Skeleton className="h-4 w-2/3" />
          </CardContent>
          <CardFooter>
            <Skeleton className="h-9 w-24" />
          </CardFooter>
        </Card>
      ))}
    </div>
  )

  // Format date with enhanced relative time
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const oneWeekAgo = subDays(now, 7)
      
      // If within the last week, show relative time
      if (isWithinInterval(date, { start: oneWeekAgo, end: now })) {
        return formatDistanceToNow(date, { addSuffix: true })
      }
      
      // For older articles, show the date in format "Mar 15, 2023"
      return format(date, 'MMM d, yyyy')
    } catch (e) {
      return dateString
    }
  }

  // Show sync status in development
  const renderSyncStatus = () => {
    if (process.env.NODE_ENV !== 'development' || !lastSyncAt) return null

    return (
      <div className="text-xs text-muted-foreground text-center py-2 border-b">
        Last synced: {formatDistanceToNow(lastSyncAt, { addSuffix: true })} 
        {!isOnline && <span className="ml-2 text-amber-600">(Offline mode)</span>}
        {totalItems !== undefined && <span className="ml-2">({totalItems} total)</span>}
      </div>
    )
  }

  // Render content based on state
  if (isLoading) {
    return (
      <>
        {renderSyncStatus()}
        {renderSkeletons()}
      </>
    )
  }
  
  if (error && articles.length === 0) {
    return (
      <>
        {renderSyncStatus()}
        {renderErrorState()}
      </>
    )
  }
  
  if (!isLoading && articles.length === 0) {
    return (
      <>
        {renderSyncStatus()}
        {renderEmptyState()}
      </>
    )
  }

  return (
    <div className="space-y-4">
      {renderSyncStatus()}
      
      {articles.map((article, index) => {
        // Add local storage fields to match NewsCard expectations
        const articleWithTopics = {
          ...article,
          topics: article.topics || []
        } as ArticlePreviewWithTopics

        if (articles.length === index + 1) {
          return (
            <div ref={lastArticleRef} key={article.id}>
              <NewsCard 
                article={articleWithTopics} 
                formatDate={formatDate}
                onArticleClick={handleArticleClick}
              />
            </div>
          )
        } else {
          return (
            <NewsCard 
              key={article.id} 
              article={articleWithTopics} 
              formatDate={formatDate}
              onArticleClick={handleArticleClick}
            />
          )
        }
      })}

      {isLoadingMore && (
        <div className="flex justify-center py-4">
          <div className="animate-pulse flex space-x-2">
            <div className="rounded-full bg-muted h-2 w-2"></div>
            <div className="rounded-full bg-muted h-2 w-2"></div>
            <div className="rounded-full bg-muted h-2 w-2"></div>
          </div>
        </div>
      )}

      {error && articles.length > 0 && (
        <div className="flex justify-center py-4">
          <Button onClick={handleRefresh} variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Failed to load more. Retry?
          </Button>
        </div>
      )}

      {!hasMore && !isLoading && articles.length > 0 && (
        <Card className="bg-primary/5 border-primary/20 text-center">
          <CardContent className="pt-6 pb-4">
            <div className="flex justify-center mb-4">
              <div className="bg-primary/10 p-3 rounded-full">
                <Check className="h-6 w-6 text-primary" />
              </div>
            </div>
            <h3 className="text-lg font-medium mb-2">You're all caught up!</h3>
            <p className="text-muted-foreground mb-4">
              {feedType === 'world' 
                ? "You've seen all the top headlines for now. Check back later for more updates."
                : "You've read all the top stories for now. Check back later for more updates."}
            </p>
            <div className="flex justify-center mt-4 gap-2">
              <Coffee className="h-5 w-5 text-muted-foreground" />
              <Newspaper className="h-5 w-5 text-muted-foreground" />
            </div>
            {isOnline && (
              <Button onClick={handleRefresh} variant="outline" size="sm" className="mt-4">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh for new content
              </Button>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}


