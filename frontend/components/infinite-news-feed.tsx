"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Check, Coffee, Newspaper, AlertTriangle } from "lucide-react"
import { getPersonalizedFeed, getWorldFeed, ArticleQueryParams } from "@/lib/api"
import { format, formatDistanceToNow, isWithinInterval, subDays } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import { NewsCard, ArticlePreviewWithTopics } from "@/components/news-card"

interface InfiniteNewsFeedProps {
  feedType?: 'personalized' | 'world';
  topicSlug?: string;
  searchQuery?: string;
  sortOrder?: 'relevance' | 'newest' | 'oldest';
}

export function InfiniteNewsFeed({ feedType = 'personalized', topicSlug, searchQuery, sortOrder = 'relevance' }: InfiniteNewsFeedProps) {
  const [articles, setArticles] = useState<ArticlePreviewWithTopics[]>([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true) // Start with loading
  const [initialLoading, setInitialLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(true)
  const [reachedEnd, setReachedEnd] = useState(false)
  const observer = useRef<IntersectionObserver | null>(null)

  // Function to load articles
  const loadArticles = useCallback(async (pageNum: number, reset: boolean = false) => {
    setLoading(true)
    setError(null)
    
    try {
      const params: ArticleQueryParams = {
        page: pageNum,
        page_size: 10,
      }

      // Add sort parameter only for personalized feed
      if (feedType === 'personalized') {
        params.sort = sortOrder
      }
      
      if (topicSlug && topicSlug !== 'for-you' && topicSlug !== 'all') {
        params.topic = topicSlug
      }
      
      if (searchQuery) {
        params.search = searchQuery
      }
      
      // Choose the appropriate API based on feed type
      const data = feedType === 'world' 
        ? await getWorldFeed(params)
        : await getPersonalizedFeed(params)
      
      if (reset) {
        setArticles(data.articles)
      } else {
        setArticles(prev => [...prev, ...data.articles])
      }
      
      if (!data.pagination.hasNext) {
        setHasMore(false)
        if (data.articles.length === 0 && pageNum === 1) {
          // No articles found
          setReachedEnd(false)
        } else {
        setReachedEnd(true)
        }
      } else {
        setHasMore(true)
        setReachedEnd(false)
      }
      
      return data.articles.length
    } catch (err) {
      console.error("Error fetching articles:", err)
      setError(err instanceof Error ? err.message : "Failed to load articles")
      return 0
    } finally {
      setLoading(false)
      setInitialLoading(false)
    }
  }, [feedType, topicSlug, searchQuery, sortOrder])

  // Handle search/filter changes
  useEffect(() => {
    setPage(1)
    setHasMore(true)
    setReachedEnd(false)
    setInitialLoading(true)
    loadArticles(1, true)
  }, [topicSlug, searchQuery, sortOrder, loadArticles])

  // Set up the intersection observer for infinite scroll
  const lastArticleRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (loading) return

      if (observer.current) observer.current.disconnect()

      observer.current = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && hasMore) {
          setPage(prevPage => prevPage + 1)
        }
      })

      if (node) observer.current.observe(node)
    },
    [loading, hasMore],
  )

  // Load more articles when page changes
  useEffect(() => {
    if (page > 1) {
      loadArticles(page)
    }
  }, [page, loadArticles])

  // Handle retry
  const handleRetry = () => {
    setError(null)
    loadArticles(page, page === 1)
  }

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
        <p className="text-muted-foreground">
          {searchQuery 
            ? `No ${feedType === 'world' ? 'headlines' : 'articles'} match your search criteria. Try a different search term.`
            : topicSlug !== 'for-you' && topicSlug !== 'all'
              ? `No ${feedType === 'world' ? 'headlines' : 'articles'} found in this topic. Try a different topic or check back later.`
              : feedType === 'world' 
                ? "We couldn't find any headlines. Check back later for the latest news."
                : "We couldn't find any articles for your preferences. Update your interests or check back later."}
        </p>
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
          {error || "Something went wrong. Please try again."}
        </p>
        <Button onClick={handleRetry} variant="outline">
          Try again
        </Button>
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

  // Render content based on state
  if (initialLoading) {
    return renderSkeletons()
  }
  
  if (error && articles.length === 0) {
    return renderErrorState()
  }
  
  if (!loading && articles.length === 0) {
    return renderEmptyState()
  }

  return (
    <div className="space-y-4">
      {articles.map((article, index) => {
        if (articles.length === index + 1) {
          return (
            <div ref={lastArticleRef} key={article.id}>
              <NewsCard article={article} formatDate={formatDate} />
            </div>
          )
        } else {
          return <NewsCard key={article.id} article={article} formatDate={formatDate} />
        }
      })}

      {loading && !initialLoading && (
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
          <Button onClick={handleRetry} variant="outline" size="sm">
            Failed to load more. Retry?
          </Button>
        </div>
      )}

      {reachedEnd && (
        <Card className="bg-primary/5 border-primary/20 text-center">
          <CardContent className="pt-6 pb-4">
            <div className="flex justify-center mb-4">
              <div className="bg-primary/10 p-3 rounded-full">
                <Check className="h-6 w-6 text-primary" />
              </div>
            </div>
            <h3 className="text-lg font-medium mb-2">You're all caught up!</h3>
            <p className="text-muted-foreground">
              {feedType === 'world' 
                ? "You've seen all the top headlines for now. Check back later for more updates."
                : "You've read all the top stories for now. Check back later for more updates."}
            </p>
            <div className="flex justify-center mt-4 gap-2">
              <Coffee className="h-5 w-5 text-muted-foreground" />
              <Newspaper className="h-5 w-5 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}


