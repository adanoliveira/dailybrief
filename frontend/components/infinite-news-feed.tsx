"use client"

import { useEffect, useState, useRef, useCallback, useMemo } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Check, Clock, Coffee, Newspaper, AlertTriangle, Tag } from "lucide-react"
import { ArticlePreview as BaseArticlePreview, getPersonalizedFeed, ArticleQueryParams } from "@/lib/api"
import { format } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import { getTopicIcon } from "@/lib/topic-icons"

// Extend the base ArticlePreview to include optional topics
interface ArticlePreviewWithTopics extends BaseArticlePreview {
  topics?: Array<{
    id: number;
    name: string;
    slug: string;
  }>;
}

interface InfiniteNewsFeedProps {
  topicSlug?: string;
  searchQuery?: string;
  sortOrder?: 'relevance' | 'newest' | 'oldest';
}

export function InfiniteNewsFeed({ topicSlug, searchQuery, sortOrder = 'relevance' }: InfiniteNewsFeedProps) {
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
        sort: sortOrder,
      }
      
      if (topicSlug && topicSlug !== 'for-you') {
        params.topic = topicSlug
      }
      
      if (searchQuery) {
        params.search = searchQuery
      }
      
      const data = await getPersonalizedFeed(params)
      
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
  }, [topicSlug, searchQuery, sortOrder])

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
        <h3 className="text-lg font-medium mb-2">No articles found</h3>
        <p className="text-muted-foreground">
          {searchQuery 
            ? "No articles match your search criteria. Try a different search term."
            : topicSlug !== 'for-you' 
              ? "No articles found in this topic. Try a different topic or check back later."
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
        <h3 className="text-lg font-medium mb-2">Failed to load articles</h3>
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

  // Format date
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      
      // If within the last 24 hours, show relative time
      const diffHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60))
      
      if (diffHours < 24) {
        return diffHours === 0 
          ? 'Just now'
          : diffHours === 1 
            ? '1 hour ago'
            : `${diffHours} hours ago`
      }
      
      // Otherwise, show the date in format "Mar 15, 2023"
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
              You've read all the top stories for now. Check back later for more updates.
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

interface NewsCardProps {
  article: ArticlePreviewWithTopics;
  formatDate: (date: string) => string;
}

function NewsCard({ article, formatDate }: NewsCardProps) {
  const [imageError, setImageError] = useState(false);
  const hasImage = article.imageUrl && !imageError;
  
  // Determine topic from article or use a default
  const displayTopic = useMemo(() => {
    // If article has topics array, use the first one
    if (article.topics && article.topics.length > 0) {
      return article.topics[0];
    }
    
    // Otherwise try to extract topic from topic slug in the query params
    const urlParams = new URLSearchParams(window.location.search);
    const topicParam = urlParams.get('topic');
    
    if (topicParam && topicParam !== 'for-you') {
      // Format the slug as a readable name
      const topicName = topicParam
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      
      return {
        id: 0,
        name: topicName,
        slug: topicParam
      };
    }
    
    // Default to "World" if no topic is found
    return {
      id: 0,
      name: "World",
      slug: "world"
    };
  }, [article.topics]);
  
  // Get the topic icon
  const TopicIcon = getTopicIcon(displayTopic.slug);

  return (
    <Card className="overflow-hidden transition-all hover:shadow-md">
      <div className="flex flex-col md:flex-row">
        {/* Image section - conditional rendering based on image availability */}
        {hasImage && (
          <div className="md:w-1/3 h-48 md:h-auto relative overflow-hidden">
            <div 
              className="w-full h-full bg-cover bg-center md:rounded-l" 
              style={{ 
                backgroundImage: `url(${article.imageUrl})`, 
                backgroundPosition: 'center',
                backgroundSize: 'cover'
              }}
              role="img"
              aria-label={article.title}
              onError={() => setImageError(true)}
            />
            {/* Absolute positioned topic tag at the top right of the image */}
            <div className="absolute top-2 right-2">
              <div className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-black/70 text-white backdrop-blur-sm">
                <TopicIcon className="h-3 w-3 mr-1" />
                {displayTopic.name}
              </div>
            </div>
          </div>
        )}
        
        {/* Content section */}
        <div className={`flex flex-col ${hasImage ? 'md:w-2/3' : 'w-full'}`}>
          <CardHeader>
            {/* Topic tag if not showing image (or showing in a prominent way if there's no image) */}
            {!hasImage && (
              <div className="mb-2">
                <div className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-primary/10 text-primary">
                  <TopicIcon className="h-3 w-3 mr-1" />
                  {displayTopic.name}
                </div>
              </div>
            )}
            
            <CardTitle className="line-clamp-2 text-lg">
              <Link href={`/article/${article.id}`} className="hover:underline">
                {article.title}
              </Link>
            </CardTitle>
            <CardDescription className="flex items-center gap-2 text-xs flex-wrap">
              {article.source.logoUrl ? (
                <div className="flex items-center gap-1.5">
                  <div className="h-4 w-4 rounded-full overflow-hidden bg-muted flex items-center justify-center">
                    <img 
                      src={article.source.logoUrl} 
                      alt={article.source.name}
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        // Hide the image on error and show just the name
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                  </div>
                  <span>{article.source.name}</span>
                </div>
              ) : (
                <span>{article.source.name}</span>
              )}
              <span>•</span>
              <span>{formatDate(article.publishedAt)}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground line-clamp-3">{article.description}</p>
          </CardContent>
          <CardFooter className="pt-0">
            <Link href={`/article/${article.id}`}>
              <Button variant="ghost" size="sm">
                Read more
              </Button>
            </Link>
          </CardFooter>
        </div>
      </div>
    </Card>
  );
}
