"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Clock, ExternalLink, Image, Video, Volume2, Sparkles } from "lucide-react"
import Link from "next/link"
import { getArticleDetail, ArticleDetail } from "@/lib/api"
import { format } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import { RichArticleRenderer } from "@/components/rich-article-renderer"

export default function Article({ params }: { params: { id: string } }) {
  const [article, setArticle] = useState<ArticleDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchArticle = async () => {
      try {
        setLoading(true)
        const data = await getArticleDetail(params.id)
        setArticle(data)
        setError(null)
      } catch (err) {
        console.error('Error fetching article:', err)
        setError(err instanceof Error ? err.message : 'Failed to load article')
      } finally {
        setLoading(false)
      }
    }

    fetchArticle()
  }, [params.id])

  // Format date
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return format(date, 'MMMM d, yyyy')
    } catch (e) {
      return dateString
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className="container py-6 max-w-3xl">
        <div className="space-y-6">
          <div>
            <Skeleton className="h-4 w-1/3 mb-2" />
            <Skeleton className="h-10 w-full" />
          </div>
          <Card>
            <CardContent className="p-4">
              <Skeleton className="h-4 w-40 mb-2" />
              <Skeleton className="h-24 w-full" />
            </CardContent>
          </Card>
          <div className="space-y-4">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="container py-6 max-w-3xl">
        <Card className="bg-destructive/5 border-destructive/20 text-center">
          <CardContent className="pt-6 pb-4">
            <div className="flex justify-center mb-4">
              <div className="bg-destructive/10 p-3 rounded-full">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
            </div>
            <h3 className="text-lg font-medium mb-2">Failed to load article</h3>
            <p className="text-muted-foreground mb-4">
              {error}
            </p>
            <div className="flex justify-center gap-4">
              <Button onClick={() => window.location.reload()} variant="outline">
                Try again
              </Button>
              <Link href="/home">
                <Button>Back to feed</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // No article found
  if (!article) {
    return (
      <div className="container py-6 max-w-3xl">
        <div className="text-center space-y-4">
          <h1 className="text-2xl font-bold">Article not found</h1>
          <p className="text-muted-foreground">The article you're looking for doesn't exist or has been removed.</p>
          <Link href="/home">
            <Button>Back to feed</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="container py-6 max-w-3xl">
      <div className="space-y-6">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
            {article.topics && article.topics.length > 0 && (
              <>
                <span>{article.topics[0].name}</span>
                <span>•</span>
              </>
            )}
            <span>{formatDate(article.publishedAt)}</span>
            <span>•</span>
            <span>{article.source.name}</span>
            {article.author && (
              <>
                <span>•</span>
                <span>By {article.author}</span>
              </>
            )}
            {article.readTime && (
              <>
            <span>•</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {article.readTime} min read
                </span>
              </>
            )}
          </div>
          <h1 className="text-3xl font-bold tracking-tight md:text-4xl">
            {article.visualTitle || article.title}
          </h1>
        </div>

        {article.summary && article.summary.abstract && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="p-4">
            <h2 className="font-semibold mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              AI-Generated Abstract
            </h2>
            <p className="text-sm">
                {article.summary.abstract}
            </p>
          </CardContent>
        </Card>
        )}

        {/* Article Content */}
        <div className="article-content">
          {article.richContent && article.richContent.blocks && article.richContent.blocks.length > 0 ? (
            <RichArticleRenderer
              blocks={article.richContent.blocks}
              mediaAssets={article.richContent.mediaAssets}
              formattingData={article.richContent.formattingData}
              fallbackContent={article.content}
              className="prose prose-gray max-w-none dark:prose-invert"
            />
          ) : (
            <div className="prose prose-gray max-w-none dark:prose-invert">
          {article.content ? (
            <div dangerouslySetInnerHTML={{ __html: article.content }} />
          ) : (
                <p className="text-muted-foreground">{article.description}</p>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-center pt-4">
          <Link href={article.url} target="_blank" rel="noopener noreferrer">
            <Button className="gap-2">
              Read the full article
              <ExternalLink className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
